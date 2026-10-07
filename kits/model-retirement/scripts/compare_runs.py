#!/usr/bin/env python3
"""Run the same test cases through the OLD and the NEW model setup and compare them side by side.

Usage:
    python compare_runs.py --tests test_set.jsonl --old runner_old.json --new runner_new.json \
        --out comparison.xlsx

Options:
    --out FILE      Excel file to write (default: comparison.xlsx next to the test set)
    --dry-run       check the files and show the plan (calls, rough cost) without calling anything
    --yes           required when a runner calls a real API (any runner except mock and recorded)
    --grades FILE   CSV with columns id, preferred, new_ok, notes to pre-fill the grading columns
    --from-raw FILE re-build the workbook from the answers saved by an earlier run
                    (comparison_raw.jsonl). Calls nothing. Use it to add --grades.
    --limit N       only run the first N cases (a cheap smoke test)
    --delay S       wait S seconds after each call (helps with rate limits)
    --retries N     retry a failed call N times (default 2)

Writes:
    comparison.xlsx         Summary, Comparison (one row per case) and Settings sheets
    comparison_raw.jsonl    every prompt and answer, so paid results are never lost
                            (not written again with --from-raw)

Test set: a JSONL file, one JSON object per line. Only "input" is required:
    {"id": "S01", "feature": "summarize", "input": "the text the feature receives",
     "system": "optional system prompt", "expected": "optional: what a good answer looks like",
     "must_include": ["#10423"], "must_not_include": ["order #"], "expect_json": false,
     "max_chars": 600, "tags": ["delivery"]}

Runner config: a JSON file. See templates/runner_config_template.json and runners.py.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import importlib.util
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runners  # noqa: E402  (lives next to this script)

OFFLINE_RUNNERS = {"mock", "recorded"}
PLACEHOLDER_MODEL = "PUT-THE-MODEL-ID-HERE"   # the model in templates/runner_config_template.json
PRICE_KEYS = ("price_per_1m_input_tokens", "price_per_1m_output_tokens")
MAX_TOKEN_KEYS = ("max_tokens", "max_completion_tokens", "max_output_tokens", "maxTokens", "maxOutputTokens")
SECRET_RE = re.compile(r"\b(?:sk|pk|rk)[-_][A-Za-z0-9_\-]{12,}|\bAKIA[0-9A-Z]{16}\b|\bAIza[0-9A-Za-z_\-]{30,}")


# --------------------------------------------------------------------------- loading
def load_test_set(path: Path) -> list:
    if not path.exists():
        raise SystemExit(f"Test set not found: {path}")
    cases, seen = [], set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            case = json.loads(line)
        except ValueError as exc:
            raise SystemExit(f"{path.name} line {n} is not valid JSON: {exc}")
        if not isinstance(case, dict):
            raise SystemExit(f"{path.name} line {n} must be a JSON object.")
        if "input" not in case:
            if "prompt" not in case:
                raise SystemExit(f'{path.name} line {n} has no "input".')
            case["input"] = case["prompt"]
        case["id"] = str(case.get("id") or f"case-{n}")
        if case["id"] in seen:
            raise SystemExit(f'{path.name} line {n}: the id "{case["id"]}" is used twice.')
        seen.add(case["id"])
        for key in ("must_include", "must_not_include", "tags"):
            if isinstance(case.get(key), str):
                case[key] = [case[key]]
        cases.append(case)
    if not cases:
        raise SystemExit(f"{path.name} has no test cases.")
    return cases


def load_config(path: Path, side: str) -> dict:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Runner config not found: {path}")
    except ValueError as exc:
        raise SystemExit(f"{path.name} is not valid JSON: {exc}")
    if not isinstance(cfg, dict):
        raise SystemExit(f"{path.name} must contain one JSON object {{...}}.")
    for key in ("runner", "model"):
        if not cfg.get(key):
            raise SystemExit(f'{path.name} needs a "{key}" value.')
    for key, value in cfg.items():
        if re.search(r"(?i)(api[_-]?key|secret|access[_-]?token|auth[_-]?token|password)$", key) and value:
            raise SystemExit(f'{path.name} contains "{key}". Never put keys in files: name an environment '
                             f'variable in "api_key_env" instead.')
    for key in PRICE_KEYS:
        if cfg.get(key) is not None:
            try:
                float(cfg[key])
            except (TypeError, ValueError):
                raise SystemExit(f'{path.name}: "{key}" must be a number such as 0.8, not {cfg[key]!r}.')
    cfg.setdefault("name", side)
    cfg["_config_dir"] = str(path.resolve().parent)
    cfg["_config_file"] = path.name
    return cfg


def resolve_runner(cfg: dict):
    name = cfg["runner"]
    if name in runners.BUILT_IN:
        return runners.BUILT_IN[name]
    if ":" in name:
        file_part, func_name = name.rsplit(":", 1)
        path = Path(file_part)
        if not path.is_absolute():
            path = Path(cfg["_config_dir"]) / path
        if not path.exists():
            raise SystemExit(f"Runner file not found: {path}")
        spec = importlib.util.spec_from_file_location(f"custom_runner_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, func_name, None)
        if not callable(func):
            raise SystemExit(f'{path.name} has no function called "{func_name}".')
        return func
    raise SystemExit(f'Unknown runner "{name}" in {cfg["_config_file"]}. '
                     f'Use mock, recorded, client_api or "my_runner.py:function_name".')


def load_grades(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Grades file not found: {path}")
    grades = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for n, raw in enumerate(csv.DictReader(fh), start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not row.get("id"):
                continue
            pref, ok = row.get("preferred", "").lower(), row.get("new_ok", "").lower()
            if pref not in ("", "old", "new", "same"):
                print(f"WARNING: {path.name} line {n}: preferred should be old, new or same (got '{pref}').")
            if ok not in ("", "yes", "no"):
                print(f"WARNING: {path.name} line {n}: new_ok should be yes or no (got '{ok}').")
            grades[row["id"]] = {"preferred": pref, "new_ok": ok,
                                 "notes": row.get("notes", row.get("grader_notes", ""))}
    return grades


# --------------------------------------------------------------------------- running
def build_request(case: dict, cfg: dict):
    """Apply the runner config (and its per-feature settings) to one test case."""
    feature = (cfg.get("features") or {}).get(str(case.get("feature") or ""), {})
    system = feature.get("system", cfg.get("system", case.get("system")))
    template = feature.get("prompt_template", cfg.get("prompt_template", "{input}"))
    prompt = template.replace("{input}", str(case["input"]))
    params = dict(cfg.get("params") or {})
    for key, value in (feature.get("params") or {}).items():
        if value is None:
            params.pop(key, None)        # null in a feature removes a top-level setting
        else:
            params[key] = value
    return prompt, system, params, feature.get("model", cfg["model"])


def clean_error(exc: Exception) -> str:
    return SECRET_RE.sub("***", f"{type(exc).__name__}: {exc}")[:500]


def run_checks(case: dict, output: str):
    """Simple automatic checks from the test case. Returns (passed or None, detail)."""
    problems, has_checks, low = [], False, output.lower()
    for phrase in case.get("must_include") or []:
        has_checks = True
        if str(phrase).lower() not in low:
            problems.append(f'missing "{phrase}"')
    for phrase in case.get("must_not_include") or []:
        has_checks = True
        if str(phrase).lower() in low:
            problems.append(f'contains "{phrase}"')
    if case.get("expect_json"):
        has_checks = True
        try:
            json.loads(output.strip())
        except ValueError:
            fenced = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", output.strip())
            try:
                json.loads(fenced)
                problems.append("JSON is wrapped in ``` fences (the app may fail to read it)")
            except ValueError:
                problems.append("not valid JSON")
    if case.get("max_chars"):
        has_checks = True
        if len(output) > int(case["max_chars"]):
            problems.append(f"longer than {case['max_chars']} characters")
    if not has_checks:
        return None, ""
    return (not problems), ("OK" if not problems else "; ".join(problems))


def run_one(runner, case: dict, cfg: dict, retries: int, delay: float) -> dict:
    prompt, system, params, model = build_request(case, cfg)
    call_cfg = dict(cfg, params=params, model=model)
    result, attempt = None, 0
    while result is None:
        started = time.perf_counter()
        try:
            raw = runner(prompt, system, call_cfg, case)
            elapsed = time.perf_counter() - started
            result = {"output": raw} if isinstance(raw, str) else dict(raw or {})
            result["output"] = "" if result.get("output") is None else str(result["output"])
            if result.get("latency_s") is None and not result.get("error"):
                result["latency_s"] = round(elapsed, 3)
        except (runners.RunnerSetupError, NotImplementedError):
            raise
        except Exception as exc:  # one failed call should not stop the whole run
            attempt += 1
            if attempt > retries:
                result = {"output": "", "error": clean_error(exc), "latency_s": None}
            else:
                time.sleep(min(30, 2 ** attempt))
    result.update(model=model, params=params, system=system, prompt=prompt)
    pin, pout = cfg.get("price_per_1m_input_tokens"), cfg.get("price_per_1m_output_tokens")
    if None not in (pin, pout, result.get("input_tokens"), result.get("output_tokens")):
        result["cost"] = round(result["input_tokens"] * float(pin) / 1e6
                               + result["output_tokens"] * float(pout) / 1e6, 8)
    if not result.get("error"):
        result["check_ok"], result["check_detail"] = run_checks(case, result["output"])
    if delay:
        time.sleep(delay)
    return result


def similarity(a: str, b: str):
    """Share of words the two answers have in common, in the same order (0 to 1)."""
    wa, wb = str(a or "").lower().split(), str(b or "").lower().split()
    if not wa or not wb:
        return None
    return round(difflib.SequenceMatcher(None, wa, wb, autojunk=False).ratio(), 3)


def estimate_max_cost(cases: list, cfg: dict):
    pin, pout = cfg.get("price_per_1m_input_tokens"), cfg.get("price_per_1m_output_tokens")
    if pin is None or pout is None:
        return None
    total = 0.0
    for case in cases:
        prompt, system, params, _ = build_request(case, cfg)
        max_out = next((params[k] for k in MAX_TOKEN_KEYS if k in params), None)
        if max_out is None:
            return None
        total += runners.estimate_tokens((system or "") + prompt) * float(pin) / 1e6
        total += float(max_out) * float(pout) / 1e6
    return total


def describe_plan(cases: list, old: dict, new: dict) -> str:
    lines = [f"Test cases: {len(cases)}  ->  {2 * len(cases)} calls ({len(cases)} old + {len(cases)} new)"]
    for label, cfg in (("OLD", old), ("NEW", new)):
        est = estimate_max_cost(cases, cfg)
        cost = f"rough maximum cost ${est:.4f}" if est is not None else "rough cost unknown (set prices and max tokens)"
        lines.append(f"  {label}: {cfg['name']} | runner={cfg['runner']} | model={cfg['model']} | {cost}")
    return "\n".join(lines)


def check_setup(cases: list, old: dict, new: dict):
    """Find common setup mistakes before anything is called.

    Returns (problems, warnings). A problem stops a run that calls a real API.
    """
    problems, warnings = [], []
    for cfg in (old, new):
        file, live = cfg["_config_file"], cfg["runner"] not in OFFLINE_RUNNERS
        if any(PLACEHOLDER_MODEL in str(build_request(case, cfg)[3]) for case in cases):
            (problems if live else warnings).append(
                f'{file} still has the template model "{PLACEHOLDER_MODEL}". Put in the real model ID.')
        if live:
            prices = [cfg.get(k) for k in PRICE_KEYS]
            if None in prices:
                warnings.append(f"{file} has no prices, so the cost is unknown. Copy them from the provider's "
                                f"pricing page.")
            elif all(float(p) == 0 for p in prices):
                warnings.append(f"{file} has prices of 0, so the cost estimate says $0. Copy the real prices "
                                f"from the provider's pricing page.")

    def settings(cfg):
        return {k: v for k, v in cfg.items() if not k.startswith("_") and k != "name"}
    if settings(old) == settings(new):
        warnings.append(f"{old['_config_file']} and {new['_config_file']} have the same settings, so old and new "
                        f"would be the same. Set the new model (and prompt) in {new['_config_file']}.")
    elif old["name"] == new["name"]:
        warnings.append(f'Both runner configs are called "{old["name"]}". Give each one its own "name", so the '
                        f'workbook shows which side is which.')
    return problems, warnings


def load_raw(path: Path, cases: list) -> list:
    """Re-build the result rows from the raw file of an earlier run (comparison_raw.jsonl)."""
    if not path.exists():
        raise SystemExit(f"Saved answers not found: {path}")
    saved = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise SystemExit(f"{path.name} line {n} is not valid JSON: {exc}")
        if not (isinstance(row, dict) and isinstance(row.get("old"), dict) and isinstance(row.get("new"), dict)):
            raise SystemExit(f'{path.name} line {n} has no "old" and "new" answers. Use the _raw.jsonl file '
                             f'that compare_runs.py wrote.')
        saved[str(row.get("id"))] = row
    rows, missing = [], []
    for case in cases:
        row = saved.pop(case["id"], None)
        if row is None:
            missing.append(case["id"])
            continue
        for side in ("old", "new"):
            row[side]["output"] = "" if row[side].get("output") is None else str(row[side]["output"])
        rows.append({"case": case, "old": row["old"], "new": row["new"],
                     "similarity": row.get("similarity"), "len_change": row.get("len_change")})
    if not rows:
        raise SystemExit(f"None of the case ids in {path.name} are in the test set. Use the test set of that run.")
    if missing:
        print(f"WARNING: no saved answers for {len(missing)} test case(s), left out: {', '.join(missing)}")
    if saved:
        print(f"WARNING: saved answers for case ids not in the test set, left out: {', '.join(sorted(saved))}")
    return rows


def changed_configs(rows: list, old: dict, new: dict) -> list:
    """Runner config files whose model, prompt or settings differ from the saved answers."""
    changed = []
    for side, cfg in (("old", old), ("new", new)):
        for row in rows:
            prompt, system, params, model = build_request(row["case"], cfg)
            saved = row[side]
            if any(key in saved and saved[key] != value for key, value in
                   (("model", model), ("system", system), ("prompt", prompt), ("params", params))):
                changed.append(cfg["_config_file"])
                break
    return changed


# --------------------------------------------------------------------------- numbers
def pct_change(old, new):
    if old in (None, 0) or new is None:
        return None
    return new / old - 1


def side_stats(rows: list, side: str) -> dict:
    ok = [r[side] for r in rows if not r[side].get("error")]
    lat = [x["latency_s"] for x in ok if x.get("latency_s") is not None]
    tin = [x["input_tokens"] for x in ok if x.get("input_tokens") is not None]
    tout = [x["output_tokens"] for x in ok if x.get("output_tokens") is not None]
    costs = [x["cost"] for x in ok if x.get("cost") is not None]
    checked = [x for x in ok if x.get("check_ok") is not None]
    total_cost = sum(costs) if costs and len(costs) == len(ok) else None
    return {
        "calls": len(rows), "ok": len(ok),
        "avg_chars": statistics.mean(len(x["output"]) for x in ok) if ok else None,
        "median_latency": statistics.median(lat) if lat else None,
        "avg_latency": statistics.mean(lat) if lat else None,
        "tokens_in": sum(tin) if tin else None, "tokens_out": sum(tout) if tout else None,
        "cost": total_cost,
        "cost_per_1000": total_cost / len(ok) * 1000 if total_cost is not None and ok else None,
        "checks_passed": sum(1 for x in checked if x["check_ok"]), "checks_total": len(checked),
        "simulated": any(x.get("simulated") for x in ok),
    }


# --------------------------------------------------------------------------- workbook
def write_workbook(rows: list, old: dict, new: dict, out: Path, tests_path: Path, grades: dict,
                   from_raw: Path = None):
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    bold = Font(bold=True)
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1F4E79")
    human_fill = PatternFill("solid", fgColor="BF8F00")
    input_fill = PatternFill("solid", fgColor="FFF2CC")
    good_fill, good_font = PatternFill("solid", fgColor="C6EFCE"), Font(color="006100")
    bad_fill, bad_font = PatternFill("solid", fgColor="FFC7CE"), Font(color="9C0006")
    section_fill = PatternFill("solid", fgColor="DDEBF7")
    wrap_top = Alignment(wrap_text=True, vertical="top")
    money = '"$"#,##0.00000'
    pct = "+0%;-0%;0%"

    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    comp = wb.create_sheet("Comparison")
    settings = wb.create_sheet("Settings")

    # ---- Comparison sheet
    columns = [
        ("Case ID", 10, None), ("Feature / tags", 14, None), ("Input", 45, None),
        ("Expected / notes", 30, None), ("Old output", 55, None), ("New output", 55, None),
        ("Old chars", 9, "0"), ("New chars", 9, "0"), ("Length change", 10, pct),
        ("Similarity (0-1)", 11, "0.00"), ("Old latency (s)", 10, "0.00"), ("New latency (s)", 10, "0.00"),
        ("Old tokens in", 10, "#,##0"), ("Old tokens out", 10, "#,##0"),
        ("New tokens in", 10, "#,##0"), ("New tokens out", 10, "#,##0"),
        ("Old cost ($)", 11, money), ("New cost ($)", 11, money),
        ("Old checks", 20, None), ("New checks", 20, None), ("Errors", 22, None),
        ("Preferred (old / new / same)", 15, None), ("New OK? (yes / no)", 12, None), ("Grader notes", 35, None),
    ]
    human_cols = {"Preferred (old / new / same)", "New OK? (yes / no)", "Grader notes"}
    for c, (title, width, _) in enumerate(columns, start=1):
        cell = comp.cell(row=1, column=c, value=title)
        cell.font, cell.alignment = head_font, Alignment(wrap_text=True, vertical="center")
        cell.fill = human_fill if title in human_cols else head_fill
        comp.column_dimensions[get_column_letter(c)].width = width
    comp.row_dimensions[1].height = 45

    for r, row in enumerate(rows, start=2):
        case, o, n = row["case"], row["old"], row["new"]
        tags = [str(case["feature"])] if case.get("feature") else []
        tags += [str(t) for t in case.get("tags") or []]
        errors = "; ".join(f"{side}: {row[side]['error']}" for side in ("old", "new") if row[side].get("error"))
        g = grades.get(case["id"], {})
        values = [
            case["id"], ", ".join(tags), str(case["input"]), str(case.get("expected", "")),
            o.get("output", ""), n.get("output", ""),
            len(o.get("output", "")) if not o.get("error") else None,
            len(n.get("output", "")) if not n.get("error") else None,
            row["len_change"], row["similarity"], o.get("latency_s"), n.get("latency_s"),
            o.get("input_tokens"), o.get("output_tokens"), n.get("input_tokens"), n.get("output_tokens"),
            o.get("cost"), n.get("cost"), o.get("check_detail", ""), n.get("check_detail", ""), errors,
            g.get("preferred", ""), g.get("new_ok", ""), g.get("notes", ""),
        ]
        for c, value in enumerate(values, start=1):
            title, _, fmt = columns[c - 1]
            cell = comp.cell(row=r, column=c, value=value if value != "" else None)
            cell.alignment = wrap_top
            if fmt:
                cell.number_format = fmt
            if title in human_cols:
                cell.fill = input_fill
        for c, side in ((19, o), (20, n)):
            if side.get("check_ok") is True:
                comp.cell(row=r, column=c).fill, comp.cell(row=r, column=c).font = good_fill, good_font
            elif side.get("check_ok") is False:
                comp.cell(row=r, column=c).fill, comp.cell(row=r, column=c).font = bad_fill, bad_font
        if errors:
            comp.cell(row=r, column=21).fill, comp.cell(row=r, column=21).font = bad_fill, bad_font
        line_counts = []
        for c, (title, width, _) in enumerate(columns, start=1):
            text = comp.cell(row=r, column=c).value
            if isinstance(text, str) and text:
                per_line = max(8, int(width * 1.1))
                line_counts.append(sum(max(1, math.ceil(len(p) / per_line)) for p in text.split("\n")))
        comp.row_dimensions[r].height = min(400, max(30, 15 * max(line_counts or [1])))

    last = len(rows) + 1
    comp.freeze_panes = "B2"
    comp.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{last}"
    pref_col, ok_col = get_column_letter(22), get_column_letter(23)
    dv_pref = DataValidation(type="list", formula1='"old,new,same"', allow_blank=True)
    dv_ok = DataValidation(type="list", formula1='"yes,no"', allow_blank=True)
    comp.add_data_validation(dv_pref)
    comp.add_data_validation(dv_ok)
    dv_pref.add(f"{pref_col}2:{pref_col}{last}")
    dv_ok.add(f"{ok_col}2:{ok_col}{last}")
    comp.conditional_formatting.add(f"{ok_col}2:{ok_col}{last}",
                                    CellIsRule(operator="equal", formula=['"no"'], fill=bad_fill, font=bad_font))
    comp.conditional_formatting.add(f"{ok_col}2:{ok_col}{last}",
                                    CellIsRule(operator="equal", formula=['"yes"'], fill=good_fill, font=good_font))
    comp.conditional_formatting.add(f"{pref_col}2:{pref_col}{last}",
                                    CellIsRule(operator="equal", formula=['"old"'], fill=bad_fill, font=bad_font))

    # ---- Summary sheet
    so, sn = side_stats(rows, "old"), side_stats(rows, "new")
    for col, width in zip("ABCD", (44, 34, 34, 12)):
        summary.column_dimensions[col].width = width
    summary["A1"] = "Old vs new model comparison"
    summary["A1"].font = Font(bold=True, size=14)
    summary["A2"] = (f"Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} by compare_runs.py. "
                     f"Test set: {tests_path.name} ({len(rows)} cases)."
                     + (f" Answers re-used from {from_raw.name}." if from_raw else ""))
    r = 3
    if so["simulated"] or sn["simulated"]:
        summary.cell(row=r, column=1, value="SIMULATED RUN (mock runner): answers, tokens and timings are not "
                                            "from a real model.").font = Font(bold=True, color="9C0006")
        r += 1

    def section(title, headers):
        nonlocal r
        r += 1
        for c, text in enumerate([title] + headers, start=1):
            cell = summary.cell(row=r, column=c, value=text)
            cell.font, cell.fill = bold, section_fill
        r += 1

    def line(label, old_value, new_value, change=None, fmt=None):
        nonlocal r
        summary.cell(row=r, column=1, value=label).alignment = wrap_top
        for c, value in ((2, old_value), (3, new_value)):
            cell = summary.cell(row=r, column=c, value=value)
            cell.alignment = wrap_top
            if fmt and isinstance(value, (int, float)):
                cell.number_format = fmt
        if change is not None:
            summary.cell(row=r, column=4, value=change).number_format = pct
        r += 1

    def params_text(cfg):
        text = json.dumps(cfg["params"], ensure_ascii=False) if cfg.get("params") else ""
        if cfg.get("features"):
            extra = f"per feature ({', '.join(cfg['features'])}): see Settings sheet"
            text = f"{text}, plus {extra}" if text else extra[0].upper() + extra[1:]
        return text or "none"

    def prompt_text(cfg):
        if cfg.get("features"):
            return "Per feature (see Settings sheet)"
        if cfg.get("system") or cfg.get("prompt_template"):
            return "Set in the runner config (see Settings sheet)"
        return "System prompt from the test set"

    section("Run details", ["Old", "New"])
    line("Runner config file", old["_config_file"], new["_config_file"])
    line("Runner name", old["name"], new["name"])
    line("Runner type", old["runner"], new["runner"])
    line("Model", old["model"], new["model"])
    line("Settings", params_text(old), params_text(new))
    line("Prompt", prompt_text(old), prompt_text(new))
    line("Prices per 1M tokens (input / output)",
         *[f"${float(c['price_per_1m_input_tokens']):.2f} / ${float(c['price_per_1m_output_tokens']):.2f}"
           if c.get("price_per_1m_input_tokens") is not None and c.get("price_per_1m_output_tokens") is not None
           else "not set" for c in (old, new)])

    section("Automatic results", ["Old", "New", "Change"])
    line("Successful calls", f"{so['ok']} / {so['calls']}", f"{sn['ok']} / {sn['calls']}")
    line("Average answer length (characters)", so["avg_chars"], sn["avg_chars"],
         pct_change(so["avg_chars"], sn["avg_chars"]), "0")
    line("Median response time (seconds)", so["median_latency"], sn["median_latency"],
         pct_change(so["median_latency"], sn["median_latency"]), "0.00")
    line("Average response time (seconds)", so["avg_latency"], sn["avg_latency"],
         pct_change(so["avg_latency"], sn["avg_latency"]), "0.00")
    line("Total input tokens", so["tokens_in"], sn["tokens_in"], pct_change(so["tokens_in"], sn["tokens_in"]), "#,##0")
    line("Total output tokens", so["tokens_out"], sn["tokens_out"],
         pct_change(so["tokens_out"], sn["tokens_out"]), "#,##0")
    line("Estimated cost of this run ($)", so["cost"], sn["cost"], pct_change(so["cost"], sn["cost"]), money)
    line("Estimated cost per 1,000 calls ($)", so["cost_per_1000"], sn["cost_per_1000"],
         pct_change(so["cost_per_1000"], sn["cost_per_1000"]), '"$"#,##0.00')
    line("Automatic checks passed",
         f"{so['checks_passed']} / {so['checks_total']}" if so["checks_total"] else "no checks",
         f"{sn['checks_passed']} / {sn['checks_total']}" if sn["checks_total"] else "no checks")
    sims = [x["similarity"] for x in rows if x["similarity"] is not None]
    line("Average similarity, old vs new (0-1)", round(statistics.mean(sims), 2) if sims else None, None, None, "0.00")

    features = sorted({str(x["case"].get("feature")) for x in rows if x["case"].get("feature")})
    if len(features) > 1:
        section("By feature", ["Cases", "Checks passed (old / new)", "Avg similarity"])
        for feat in features:
            sub = [x for x in rows if str(x["case"].get("feature")) == feat]
            po, pn = side_stats(sub, "old"), side_stats(sub, "new")
            fs = [x["similarity"] for x in sub if x["similarity"] is not None]
            summary.cell(row=r, column=1, value=feat)
            summary.cell(row=r, column=2, value=len(sub))
            summary.cell(row=r, column=3, value=f"{po['checks_passed']}/{po['checks_total']} old, "
                                                f"{pn['checks_passed']}/{pn['checks_total']} new")
            cell = summary.cell(row=r, column=4, value=round(statistics.mean(fs), 2) if fs else None)
            cell.number_format = "0.00"
            r += 1

    section("Human grading (updates as you grade)", ["Count"])
    pref = f"Comparison!${pref_col}$2:${pref_col}${last}"
    okr = f"Comparison!${ok_col}$2:${ok_col}${last}"
    for label, formula, fmt in (
        ("Cases graded", f"=COUNTA({pref})", "0"),
        ("New answer preferred", f'=COUNTIF({pref},"new")', "0"),
        ("About the same", f'=COUNTIF({pref},"same")', "0"),
        ("Old answer preferred", f'=COUNTIF({pref},"old")', "0"),
        ("New answer acceptable (yes)", f'=COUNTIF({okr},"yes")', "0"),
        ("New answer NOT acceptable (no)", f'=COUNTIF({okr},"no")', "0"),
        ("Acceptable rate", f'=IF(COUNTA({okr})=0,"-",COUNTIF({okr},"yes")/COUNTA({okr}))', "0%"),
    ):
        summary.cell(row=r, column=1, value=label)
        summary.cell(row=r, column=2, value=formula).number_format = fmt
        r += 1

    section("How to read this", [])
    for note in (
        "Similarity is the share of words the two answers have in common, in the same order. 1 = identical, "
        "0 = nothing in common. Different wording can be just as good, so read the answers and grade them.",
        "Automatic checks come from must_include, must_not_include, expect_json and max_chars in the test set.",
        "Costs use the prices in the runner configs. Check them on the provider's pricing page. Real token counts "
        "come from the API; mock and estimated counts are rough.",
        "Grade every case in the yellow columns of the Comparison sheet: Preferred = old, new or same; "
        "New OK? = yes or no. The counts above update by themselves.",
    ):
        summary.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        cell = summary.cell(row=r, column=1, value=note)
        cell.alignment = wrap_top
        summary.row_dimensions[r].height = 32
        r += 1

    # ---- Settings sheet
    settings.column_dimensions["A"].width = 34
    settings.column_dimensions["B"].width = 70
    settings.column_dimensions["C"].width = 70
    for c, text in enumerate(("Setting", "Old", "New"), start=1):
        cell = settings.cell(row=1, column=c, value=text)
        cell.font, cell.fill = head_font, head_fill
    keys = ["name", "runner", "model", "params", "system", "prompt_template",
            "price_per_1m_input_tokens", "price_per_1m_output_tokens", "api_key_env"]
    extra = sorted({k for cfg in (old, new) for k in cfg
                    if k not in keys and k != "features" and not k.startswith("_")})
    rows_out = [("config file", old["_config_file"], new["_config_file"])]
    rows_out += [(k, old.get(k), new.get(k)) for k in keys + extra]
    for feat in sorted(set(old.get("features") or {}) | set(new.get("features") or {})):
        for k in ("model", "system", "prompt_template", "params"):
            fo = (old.get("features") or {}).get(feat, {}).get(k)
            fn = (new.get("features") or {}).get(feat, {}).get(k)
            if fo is not None or fn is not None:
                rows_out.append((f"feature '{feat}': {k}", fo, fn))
    for i, (label, vo, vn) in enumerate(rows_out, start=2):
        settings.cell(row=i, column=1, value=label).font = bold
        for c, value in ((2, vo), (3, vn)):
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            cell = settings.cell(row=i, column=c, value=None if value is None else str(value))
            cell.alignment = wrap_top
        longest = max(len(str(vo or "")), len(str(vn or "")))
        settings.row_dimensions[i].height = min(300, max(15, 15 * math.ceil(longest / 75)))
    settings.freeze_panes = "B2"

    for ws in (summary, comp, settings):
        ws.page_setup.orientation = "landscape"
    summary.sheet_properties.pageSetUpPr.fitToPage = True
    summary.page_setup.fitToWidth, summary.page_setup.fitToHeight = 1, 0
    wb.calculation.fullCalcOnLoad = True
    wb.properties.creator = "compare_runs.py"
    wb.save(out)
    return so, sn


def write_raw(rows: list, path: Path):
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            case = row["case"]
            fh.write(json.dumps({"id": case["id"], "feature": case.get("feature"), "input": case["input"],
                                 "old": row["old"], "new": row["new"], "similarity": row["similarity"],
                                 "len_change": row["len_change"]}, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compare an old and a new model setup on the same test cases.")
    ap.add_argument("--tests", required=True, help="test set (JSONL)")
    ap.add_argument("--old", required=True, help="runner config for the current (old) setup")
    ap.add_argument("--new", required=True, help="runner config for the new setup")
    ap.add_argument("--out", default="comparison.xlsx", help="Excel file to write (default comparison.xlsx)")
    ap.add_argument("--raw-out", help="JSONL with every prompt and answer (default: <out>_raw.jsonl)")
    ap.add_argument("--grades", help="CSV (id, preferred, new_ok, notes) to pre-fill the grading columns")
    ap.add_argument("--limit", type=int, help="only run the first N cases")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds to wait after each call")
    ap.add_argument("--retries", type=int, default=2, help="retries for a failed call (default 2)")
    ap.add_argument("--dry-run", action="store_true", help="check inputs and show the plan, call nothing")
    ap.add_argument("--yes", action="store_true", help="confirm calls to a real API")
    args = ap.parse_args(argv)

    tests_path = Path(args.tests)
    cases = load_test_set(tests_path)
    if args.limit:
        cases = cases[: args.limit]
    old_cfg, new_cfg = load_config(Path(args.old), "old"), load_config(Path(args.new), "new")
    old_runner, new_runner = resolve_runner(old_cfg), resolve_runner(new_cfg)
    print(describe_plan(cases, old_cfg, new_cfg))
    if args.dry_run:
        print("Dry run: nothing was called.")
        return 0
    live = [c["runner"] for c in (old_cfg, new_cfg) if c["runner"] not in OFFLINE_RUNNERS]
    if live and not args.yes:
        print(f"\nThis run calls a real API ({', '.join(live)}). That uses the client's key and costs money.\n"
              f"Check the plan above, then run again with --yes.")
        return 2
    if importlib.util.find_spec("openpyxl") is None:
        print("openpyxl is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    grades = load_grades(Path(args.grades)) if args.grades else {}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(args.raw_out) if args.raw_out else out.with_name(out.stem + "_raw.jsonl")

    rows = []
    try:
        for i, case in enumerate(cases, start=1):
            row = {"case": case}
            for side, cfg, runner in (("old", old_cfg, old_runner), ("new", new_cfg, new_runner)):
                row[side] = run_one(runner, case, cfg, args.retries, args.delay)
            o, n = row["old"], row["new"]
            row["similarity"] = similarity(o["output"], n["output"]) if not (o.get("error") or n.get("error")) else None
            row["len_change"] = pct_change(len(o["output"]), len(n["output"])) if not (
                o.get("error") or n.get("error")) else None

            def show(x):
                if x.get("error"):
                    return "ERROR"
                check = "" if x.get("check_ok") is None else (" checks OK" if x["check_ok"] else " checks FAILED")
                return f"{x['latency_s']:.2f}s{check}"
            sim = "-" if row["similarity"] is None else f"{row['similarity']:.2f}"
            print(f"[{i}/{len(cases)}] {case['id']}: old {show(o)} | new {show(n)} | similarity {sim}")
            rows.append(row)
    except (runners.RunnerSetupError, NotImplementedError) as exc:
        print(f"\nSTOPPED: {exc}", file=sys.stderr)
        if not rows:
            return 1
        print(f"Saving the {len(rows)} cases that finished.", file=sys.stderr)
    except KeyboardInterrupt:
        print(f"\nStopped by you. Saving the {len(rows)} cases that finished.")
        if not rows:
            return 1

    write_raw(rows, raw_path)
    try:
        so, sn = write_workbook(rows, old_cfg, new_cfg, out, tests_path, grades)
    except PermissionError:
        print(f"Could not write {out}. Close it in Excel and run again. Every answer is saved in {raw_path}; "
              f'to rebuild without new calls, use "runner": "recorded" with "recorded_side".', file=sys.stderr)
        return 1
    if grades:
        unknown = sorted(set(grades) - {r["case"]["id"] for r in rows})
        if unknown:
            print(f"WARNING: grades for unknown case ids ignored: {', '.join(unknown)}")
    print(f"\nOld: {so['ok']}/{so['calls']} ok, checks {so['checks_passed']}/{so['checks_total']} | "
          f"New: {sn['ok']}/{sn['calls']} ok, checks {sn['checks_passed']}/{sn['checks_total']}")
    if so["simulated"] or sn["simulated"]:
        print("Note: mock runner used, so answers, tokens and timings are simulated.")
    print(f"Wrote {out}")
    print(f"Wrote {raw_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
