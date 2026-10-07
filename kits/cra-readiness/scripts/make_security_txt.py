#!/usr/bin/env python3
"""Create or check a security.txt file (RFC 9116).

A security.txt file tells researchers how to report a vulnerability. It lives at
https://<your-domain>/.well-known/security.txt and must be served over HTTPS as
plain text.

Create it from client.json:
  python make_security_txt.py --client client.json --out clients/acme/2026-10/security.txt

Or from options (these override client.json):
  python make_security_txt.py --contact mailto:security@example.com \\
      --policy https://example.com/security/policy --languages en,de \\
      --canonical https://example.com/.well-known/security.txt --out clients/acme/2026-10/security.txt

Check an existing file (exit code 1 when it has errors):
  python make_security_txt.py --check clients/acme/2026-10/security.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402

KNOWN_FIELDS = {"acknowledgments", "canonical", "contact", "encryption", "expires", "hiring", "policy",
                "preferred-languages", "csaf"}
FIELD_ORDER = ["Contact", "Expires", "Encryption", "Acknowledgments", "Preferred-Languages", "Canonical",
               "Policy", "Hiring", "CSAF"]


def parse_expires(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def check(text: str, today: dt.datetime | None = None) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """Return (errors, warnings, fields) for the contents of a security.txt file."""
    errors, warnings, fields = [], [], []
    today = today or dt.datetime.now(dt.timezone.utc)
    lines = text.splitlines()
    if lines and lines[0].startswith("-----BEGIN PGP SIGNED MESSAGE-----"):
        warnings.append("The file is signed. This tool does not verify the signature; check it with gpg --verify.")
        body, inside = [], False
        for line in lines[1:]:
            if line.startswith("-----BEGIN PGP SIGNATURE-----"):
                break
            if not inside:
                inside = line.strip() == ""
                continue
            body.append(line[2:] if line.startswith("- ") else line)
        lines = body
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9-]+):\s*(.*)$", line)
        if not match:
            errors.append(f"Line {number} is not in 'Field: value' form: {line[:60]}")
            continue
        name, value = match.group(1), match.group(2).strip()
        if not value:
            errors.append(f"Line {number}: {name} has no value.")
            continue
        fields.append((name, value))
        if name.lower() not in KNOWN_FIELDS:
            warnings.append(f"Line {number}: '{name}' is not a standard field (check the spelling).")

    def values(field):
        return [v for n, v in fields if n.lower() == field]

    contacts = values("contact")
    if not contacts:
        errors.append("At least one Contact field is required.")
    for value in contacts:
        if value.lower().startswith("http://"):
            errors.append(f"Contact must use https, not http: {value}")
        elif not re.match(r"^(mailto:|https://|tel:)", value, re.I):
            errors.append(f"Contact must start with mailto:, https:// or tel: ({value})")
    expires = values("expires")
    if len(expires) != 1:
        errors.append(f"Exactly one Expires field is required (found {len(expires)}).")
    else:
        when = parse_expires(expires[0])
        if when is None or when.tzinfo is None:
            errors.append(f"Expires must be a full date and time with time zone, e.g. 2027-09-30T23:59:59Z ({expires[0]})")
        elif when <= today:
            errors.append(f"The file expired on {expires[0]}. Make a new one.")
        else:
            days = (when - today).days
            if days > 366:
                warnings.append(f"Expires is {days} days away. RFC 9116 recommends less than a year.")
            elif days < 30:
                warnings.append(f"Expires in {days} days. Renew the file soon.")
    langs = values("preferred-languages")
    if len(langs) > 1:
        errors.append("Preferred-Languages may appear only once.")
    for value in langs:
        for tag in [t.strip() for t in value.split(",")]:
            if not re.match(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$", tag):
                errors.append(f"'{tag}' is not a valid language tag (use codes like en, de, fr).")
    for field in ("canonical", "policy", "acknowledgments", "hiring", "csaf"):
        for value in values(field):
            if not value.lower().startswith("https://"):
                errors.append(f"{field.title()} must be an https:// address ({value})")
    for value in values("encryption"):
        if not re.match(r"^(https://|dns:|openpgp4fpr:)", value, re.I):
            errors.append(f"Encryption must point to a key (https://, dns: or openpgp4fpr:), not contain it ({value[:40]})")
    if not values("policy"):
        warnings.append("No Policy field. Link your vulnerability disclosure policy so reporters can find it.")
    if not values("canonical"):
        warnings.append("No Canonical field. Adding the file's own https address is recommended.")
    return errors, warnings, fields


def build(args, client: dict) -> str:
    contacts = client.get("contacts", {}) or {}
    company = client.get("company", {}) or {}
    domain = company.get("domain", "")
    contact_list = list(args.contact or [])
    if not contact_list:
        if contacts.get("security_email"):
            contact_list.append(f"mailto:{contacts['security_email']}")
        if contacts.get("security_form_url"):
            contact_list.append(contacts["security_form_url"])
        if contacts.get("security_phone"):
            contact_list.append("tel:" + re.sub(r"[^\d+]", "", contacts["security_phone"]))
    days = args.expires_days or (client.get("security_txt", {}) or {}).get("expires_days") or 330
    start = dt.date.fromisoformat(K.today())
    expires = (start + dt.timedelta(days=int(days))).strftime("%Y-%m-%dT23:59:59Z")
    languages = args.languages or contacts.get("languages") or []
    if isinstance(languages, str):
        languages = [x.strip() for x in languages.split(",") if x.strip()]
    canonical = args.canonical or contacts.get("security_txt_url") or (
        f"https://{domain}/.well-known/security.txt" if domain else None)
    values = {
        "Contact": contact_list,
        "Expires": [expires],
        "Encryption": [args.encryption or contacts.get("pgp_key_url")],
        "Acknowledgments": [args.acknowledgments or contacts.get("acknowledgments_url")],
        "Preferred-Languages": [", ".join(languages)] if languages else [],
        "Canonical": [canonical],
        "Policy": [args.policy or contacts.get("policy_url")],
        "Hiring": [args.hiring or contacts.get("hiring_url")],
        "CSAF": [args.csaf or contacts.get("csaf_url")],
    }
    name = company.get("legal_name") or company.get("trading_name") or ""
    lines = [f"# Security contact{' for ' + name if name else ''}.",
             "# Found a vulnerability in one of our products? Please tell us. Our policy explains how.",
             ""]
    for field in FIELD_ORDER:
        for value in values[field]:
            if value:
                lines.append(f"{field}: {value}")
    return "\n".join(lines) + "\n"


def report(errors, warnings, fields, label: str) -> int:
    K.info(f"Checked {label}: {len(fields)} fields, {len(errors)} error(s), {len(warnings)} warning(s)")
    for e in errors:
        K.info(f"  ERROR    {e}")
    for w in warnings:
        K.info(f"  WARNING  {w}")
    return 1 if errors else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", metavar="FILE", help="check an existing security.txt and stop")
    ap.add_argument("--client", help="client.json with company and contacts")
    ap.add_argument("--out", help="where to write the new file")
    ap.add_argument("--contact", action="append", help="mailto:, https:// or tel: address (repeatable)")
    ap.add_argument("--expires-days", type=int, help="days until the file expires (default 330, keep under 365)")
    ap.add_argument("--encryption", help="https:// address of your public PGP key")
    ap.add_argument("--acknowledgments", help="https:// page thanking reporters")
    ap.add_argument("--languages", help="comma-separated language codes, e.g. en,de")
    ap.add_argument("--canonical", help="https:// address where this file will be published")
    ap.add_argument("--policy", help="https:// address of your vulnerability disclosure policy")
    ap.add_argument("--hiring", help="https:// address of security jobs (optional)")
    ap.add_argument("--csaf", help="https:// address of your CSAF provider-metadata.json (optional)")
    args = ap.parse_args()

    if args.check:
        text = Path(args.check).read_text(encoding="utf-8")
        errors, warnings, fields = check(text)
        sys.exit(report(errors, warnings, fields, args.check))

    if not args.out:
        K.fail("Give --out for the new file, or --check to check an existing one.")
    client = K.load_json(args.client) if args.client else {}
    text = build(args, client)
    errors, warnings, fields = check(text)
    out = Path(args.out)
    K.write_text(out, text)
    K.info(text)
    code = report(errors, warnings, fields, str(out))
    canonical = next((v for n, v in fields if n == "Canonical"), "https://<your-domain>/.well-known/security.txt")
    K.info("")
    K.info("To publish:")
    K.info(f"  1. Upload the file so it opens at {canonical}")
    K.info("  2. Serve it over HTTPS as text/plain; charset=utf-8 (most web hosts do this for .txt files).")
    K.info("  3. Optional: also redirect /security.txt to it, and sign it with PGP (gpg --clearsign).")
    K.info("  4. Put a reminder in the calendar one month before the Expires date to renew it.")
    sys.exit(code)


if __name__ == "__main__":
    main()
