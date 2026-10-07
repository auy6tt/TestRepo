#!/usr/bin/env python3
"""Quick self-test for the pdf-binder kit. Run after changing any script:

    python tests/test_kit.py

It checks the SDS text reader on awkward examples, then builds and verifies a
small binder in a temporary folder. Works with or without pytest.
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "scripts"))

import extract_sds as E  # noqa: E402

TODAY = dt.date(2026, 10, 7)


def parse(text):
    return E.parse_text(E.normalize_text(text), "MDY", TODAY)


def test_clean_sheet():
    p = parse("""SECTION 1: IDENTIFICATION
Product name: Example Cleaner X
Manufacturer: Example Chemicals, Inc.
Revision date: 2025-03-14
SECTION 2: HAZARD(S) IDENTIFICATION
Signal word: Danger
H222 Extremely flammable aerosol. H229 Pressurized container: may burst if heated.
Hazard pictograms: GHS02 Flame, GHS07 Exclamation mark
SECTION 3: COMPOSITION/INFORMATION ON INGREDIENTS
Ingredient A 000-00-0 H225, H304""")
    assert p["product"].value == "Example Cleaner X"
    assert p["supplier"].value == "Example Chemicals, Inc."
    assert p["date"].value == dt.date(2025, 3, 14)
    assert p["signal"].value == "Danger"
    assert p["hcodes"].value == ["H222", "H229"], "Section 3 ingredient codes must not be included"
    assert p["pictos"].value == ["GHS02", "GHS07"]


def test_messy_sheet():
    p = parse("""S E C T I O N  1 :  I D E N T I F I C A T I O N
Trade name: EXAMPLE PRIMER - GRAY
Supplier: Example Coatings Ltd. 22 Harbour Road, Sampleton
Revised: 14.02.2023
S E C T I O N  2 :  H A Z A R D S  I D E N T I F I C A T I O N
Signal word Warning
Hazard statements: H226; H 319; H302 + H332
S E C T I O N  3 :  C O M P O S I T I O N
Resin H312""")
    assert p["product"].value == "EXAMPLE PRIMER - GRAY"
    assert p["supplier"].value == "Example Coatings Ltd."
    assert p["date"].value == dt.date(2023, 2, 14)
    assert p["hcodes"].value == ["H226", "H319", "H302", "H332"]


def test_codes_from_wording():
    p = parse("""1. IDENTIFICATION
Product Name Example Washer Fluid
2. HAZARD(S) IDENTIFICATION
Signal Word: DANGER
Highly flammable liquid and vapor. Toxic if swallowed, in contact with skin or if inhaled.
3. COMPOSITION/INFORMATION ON INGREDIENTS""")
    assert p["hcodes"].value == ["H225", "H301", "H311", "H331"]
    assert p["hcodes"].how == "matched from statement wording"


def test_dates():
    cases = [("Revision Date: June 30, 2019", dt.date(2019, 6, 30)),
             ("Issue date: 2025-08-21 Supersedes: 2022-01-10", dt.date(2025, 8, 21)),
             ("Date of first issue: 2015-01-01\nRevision Date 3 March 2024", dt.date(2024, 3, 3)),
             ("Print date: 10/01/2026", dt.date(2026, 10, 1))]
    for text, want in cases:
        found = E.find_date(E.normalize_text(text), "MDY", TODAY)
        assert found.value == want, (text, found)
    print_only = E.find_date(E.normalize_text("Print date: 10/01/2026"), "MDY", TODAY)
    assert print_only.conf == "low", "a print date alone must be flagged for review"


def test_build_and_verify():
    from reportlab.pdfgen import canvas
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "docs").mkdir()
        for name, pages in (("a.pdf", 2), ("b.pdf", 3)):
            c = canvas.Canvas(str(tmp / "docs" / name))
            for i in range(pages):
                c.drawString(72, 720, f"{name} page {i + 1}")
                c.showPage()
            c.save()
        (tmp / "index.csv").write_text("section,title,file,order,notes\n"
                                       "One,First document,a.pdf,1,note\n"
                                       "Two,Second document,b.pdf,2,\n"
                                       "Two,Still to come,,3,placeholder\n", encoding="utf-8")
        out = tmp / "out" / "Test.pdf"
        run = [sys.executable, str(KIT / "scripts" / "build_binder.py"), "--pdf-folder", str(tmp / "docs"),
               "--index", str(tmp / "index.csv"), "--out", str(out), "--page-numbers"]
        assert subprocess.run(run, capture_output=True).returncode == 0
        check = [sys.executable, str(KIT / "scripts" / "verify_binder.py"), str(out), "--quiet"]
        result = subprocess.run(check, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_make_templates_writes_every_template():
    with tempfile.TemporaryDirectory() as tmp:
        run = [sys.executable, str(KIT / "scripts" / "make_templates.py"), "--out-dir", tmp]
        result = subprocess.run(run, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        for name in ("submittal-log.xlsx", "binder-index-template.xlsx", "binder-index-template.csv",
                     "sds-site-list-template.xlsx", "sds-manual-entries-template.csv"):
            assert (Path(tmp) / name).is_file(), f"make_templates.py did not write {name}"
        for name in ("binder-index-template.csv", "sds-manual-entries-template.csv"):
            assert (Path(tmp) / name).read_bytes() == (KIT / "templates" / name).read_bytes(), \
                f"templates/{name} is not what make_templates.py writes"


def test_help_has_no_side_effects():
    with tempfile.TemporaryDirectory() as tmp:
        for script in sorted((KIT / "scripts").glob("*.py")):
            result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True,
                                    cwd=tmp)
            assert result.returncode == 0, f"{script.name} --help: {result.stderr}"
            assert result.stdout.strip(), f"{script.name} --help printed nothing"
        assert not any(Path(tmp).iterdir()), "--help wrote files"


if __name__ == "__main__":
    failures = 0
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print("All tests passed." if not failures else f"{failures} test(s) failed.")
    sys.exit(1 if failures else 0)
