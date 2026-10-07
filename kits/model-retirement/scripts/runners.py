"""Runners for compare_runs.py.

A runner sends ONE test case to ONE model setup and returns the answer.
Every runner is a function with the same shape:

    def my_runner(prompt, system, config, case):
        return {
            "output": "the model's answer",      # required
            "input_tokens": 123,                 # optional: from the API's usage data
            "output_tokens": 45,                 # optional
            "latency_s": 1.2,                    # optional: measured for you if missing
            "model_reported": "...",             # optional: the model name the API says it used
        }

    prompt  the user message for this case (the runner config's prompt_template already applied)
    system  the system prompt for this case, or None
    config  the runner config (JSON) with "model" and "params" already resolved for this case
    case    the whole test case from the JSONL file (id, input, tags, ...)

Built-in runners (set "runner" in the runner config):
    mock        fake answers for testing the pipeline. No API, no key, no cost.
    recorded    replays answers saved in a JSONL file, for example the client's logs of the
                old model, or an earlier run. Use it when the old model is already retired.
    client_api  STUB: the place for the client's real API call. Edit it for each project.

Your own runner: put a function with the shape above in any .py file and set
"runner": "my_runner.py:run" (the path is relative to the runner config file).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


class RunnerSetupError(RuntimeError):
    """A problem that affects every call (missing key, missing file). Stops the whole run."""


# --------------------------------------------------------------------------- helpers
_CACHE: dict = {}


def _stable_number(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _config_path(config: dict, key: str) -> Path:
    value = config.get(key)
    if not value:
        raise RunnerSetupError(f'Runner config "{config.get("name")}" needs "{key}".')
    path = Path(value)
    if not path.is_absolute():
        path = Path(config.get("_config_dir", ".")) / path
    if not path.exists():
        raise RunnerSetupError(f'File not found for "{key}": {path}')
    return path


def _load_json(path: Path):
    if path not in _CACHE:
        _CACHE[path] = json.loads(path.read_text(encoding="utf-8"))
    return _CACHE[path]


def _load_jsonl_by_id(path: Path) -> dict:
    if path not in _CACHE:
        rows = {}
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise RunnerSetupError(f"{path.name} line {n} is not valid JSON: {exc}") from exc
            rows[str(row.get("id"))] = row
        _CACHE[path] = rows
    return _CACHE[path]


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Rough token estimate. Real tokenizers differ, and newer models often count differently."""
    return max(1, round(len(text or "") / chars_per_token))


# --------------------------------------------------------------------------- mock
def mock_run(prompt, system, config, case):
    """Fake model for testing. Costs nothing and needs no key.

    Optional config keys:
        mock_responses      JSON file {case_id: {mock_key: "answer text"}} with canned answers
                            (used for the portfolio sample so the answers read like real ones)
        mock_key            which answer to use from that file (default: the runner's "name")
        mock_chars_per_token, mock_base_latency_s, mock_seconds_per_output_token
                            simulate token counting and response time
    Without canned answers it returns a short made-up answer built from the input text.
    """
    output = None
    if config.get("mock_responses"):
        canned = _load_json(_config_path(config, "mock_responses"))
        output = canned.get(str(case.get("id")), {}).get(config.get("mock_key") or config.get("name"))
    if output is None:
        words = re.findall(r"\S+", case.get("input") or prompt)
        size = {"short": 25, "medium": 40, "long": 60}.get(config.get("mock_style", "medium"), 40)
        size = max(5, size + _stable_number(f"{config.get('model')}|{case.get('id')}") % 11 - 5)
        output = f"[mock answer from {config.get('model', 'model')}] " + " ".join(words[:size])
    chars_per_token = float(config.get("mock_chars_per_token", 4.0))
    input_tokens = estimate_tokens((system or "") + prompt, chars_per_token)
    output_tokens = estimate_tokens(output, chars_per_token)
    jitter = 0.85 + (_stable_number(f"{config.get('model')}|{case.get('id')}|t") % 31) / 100
    latency = (float(config.get("mock_base_latency_s", 0.6))
               + output_tokens * float(config.get("mock_seconds_per_output_token", 0.015))) * jitter
    return {"output": output, "input_tokens": input_tokens, "output_tokens": output_tokens,
            "latency_s": round(latency, 3), "model_reported": config.get("model"),
            "simulated": True}


# --------------------------------------------------------------------------- recorded
def recorded_run(prompt, system, config, case):
    """Replay saved answers instead of calling a model.

    Config keys:
        recorded_outputs   JSONL file, one line per case: {"id": "T01", "output": "...",
                           "input_tokens": 120, "output_tokens": 80, "latency_s": 1.4}
                           (only id and output are required)
        recorded_side      optional: "old" or "new" to reuse one side of an earlier
                           compare_runs raw file (comparison_raw.jsonl)
    """
    path = _config_path(config, "recorded_outputs")
    row = _load_jsonl_by_id(path).get(str(case.get("id")))
    if row is None:
        raise KeyError(f"no recorded answer for case {case.get('id')} in {path.name}")
    side = config.get("recorded_side")
    if side:
        row = row.get(side) or {}
    return {"output": row.get("output", ""), "input_tokens": row.get("input_tokens"),
            "output_tokens": row.get("output_tokens"), "latency_s": row.get("latency_s"),
            "model_reported": row.get("model_reported") or row.get("model")}


# --------------------------------------------------------------------------- client API (stub)
def client_api_run(prompt, system, config, case):
    """STUB: call the CLIENT's model with the CLIENT's own API key.

    Fill in the block marked below for each project (Claude Code can do it with you),
    then set "runner": "client_api" in the runner config.

    Rules:
      - The key comes from an environment variable named in the runner config
        ("api_key_env", default CLIENT_API_KEY). Never write a key in a file, a config or a chat.
      - Use the client's STAGING key and project. Never production. Never your own account.
      - Send exactly what the client's feature sends: same prompt, same settings.
        Best of all, call the client's own function (example C) so you test the real code path.
    """
    env_name = config.get("api_key_env", "CLIENT_API_KEY")
    api_key = os.environ.get(env_name)
    if not api_key:
        raise RunnerSetupError(
            f"The environment variable {env_name} is not set. Ask the client for a STAGING API key and "
            f"set it in your terminal (export {env_name}=...), or let the client run this script. "
            f"Never paste the key into a file or a chat.")
    model = config["model"]
    params = dict(config.get("params") or {})

    # >>> PUT THE CLIENT'S API CALL HERE <<<
    # Replace the `raise` at the bottom with one of these examples, adapted to the client's code.
    # Check the provider's current SDK documentation; parameter names change between versions.
    #
    # Example A: OpenAI-style SDK (pip install openai)
    #     from openai import OpenAI
    #     client = OpenAI(api_key=api_key)  # add base_url=... if the client uses a proxy or compatible API
    #     messages = ([{"role": "system", "content": system}] if system else [])
    #     messages.append({"role": "user", "content": prompt})
    #     resp = client.chat.completions.create(model=model, messages=messages, **params)
    #     return {"output": resp.choices[0].message.content or "",
    #             "input_tokens": resp.usage.prompt_tokens,
    #             "output_tokens": resp.usage.completion_tokens,
    #             "model_reported": resp.model}
    #
    # Example B: Anthropic-style SDK (pip install anthropic). This API needs max_tokens in params.
    #     import anthropic
    #     client = anthropic.Anthropic(api_key=api_key)
    #     kwargs = dict(model=model, messages=[{"role": "user", "content": prompt}], **params)
    #     if system:
    #         kwargs["system"] = system
    #     resp = client.messages.create(**kwargs)
    #     text = "".join(block.text for block in resp.content if block.type == "text")
    #     return {"output": text,
    #             "input_tokens": resp.usage.input_tokens,
    #             "output_tokens": resp.usage.output_tokens,
    #             "model_reported": resp.model}
    #
    # Example C: call the client's own function (tests the real feature, including their prompt code)
    #     import sys
    #     sys.path.insert(0, "/path/to/client/repo")
    #     from app.summarize_ticket import summarize_ticket
    #     return {"output": summarize_ticket(case["input"])}
    #     (Their function must use the model you are testing, for example through an env var.)
    raise NotImplementedError(
        "client_api_run is a stub. Open scripts/runners.py and fill in the block marked "
        "'PUT THE CLIENT'S API CALL HERE', or point the runner config at your own runner file.")


BUILT_IN = {"mock": mock_run, "recorded": recorded_run, "client_api": client_api_run}
