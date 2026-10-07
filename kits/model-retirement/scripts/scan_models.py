#!/usr/bin/env python3
"""Find AI model references in a codebase and check them against a retirement list.

Usage:
    python scan_models.py PATH/TO/CLIENT/REPO \
        --retirements ../data/retirements.csv --out-dir scan_output

Writes two files to --out-dir:
    model_scan.csv   every reference, one row each (open it in a spreadsheet)
    model_scan.md    a readable summary: what needs action, env vars to confirm, next steps

What it looks for:
    - model names next to keys such as model=, "model":, model:, modelId, deployment_name
    - MODEL settings in .env files, shell scripts, Dockerfiles and YAML / INI config
    - environment variable reads such as os.getenv("CHAT_MODEL", "...") and process.env.CHAT_MODEL
    - common SDK call sites in Python, JavaScript and TypeScript (chat completions, responses,
      messages, embeddings, generate content, Bedrock runtime, LangChain, Vercel AI SDK, LiteLLM)
    - any text that matches a model_id in the retirement list (even in comments)
    - nearby settings: temperature, top_p, top_k, max_tokens and their variants

This is a helper, not a guarantee. It can miss model names that are built at run time,
stored in a database or set in a hosting dashboard. Read the code around every hit.
Standard library only: no installs needed.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXAMPLE_MODEL_ID = "example-model-2023"
REQUIRED_COLUMNS = ["provider", "model_id", "retirement_date", "replacement", "source_url", "notes"]

# --------------------------------------------------------------------------- file types
LANG_BY_EXT = {
    ".py": "py", ".pyw": "py",
    ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js", ".ts": "js", ".tsx": "js",
    ".mts": "js", ".cts": "js", ".vue": "js", ".svelte": "js",
    ".java": "js", ".kt": "js", ".kts": "js", ".go": "js", ".cs": "js", ".swift": "js",
    ".dart": "js", ".rs": "js", ".php": "js", ".scala": "js",
    ".rb": "rb",
    ".json": "json", ".jsonc": "json",
    ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini", ".cfg": "ini", ".conf": "ini", ".properties": "ini",
    ".env": "env",
    ".sh": "sh", ".bash": "sh", ".zsh": "sh",
    ".tf": "tf", ".tfvars": "tf",
    ".ipynb": "ipynb",
}
CODE_LANGS = {"py", "js", "rb", "json", "tf"}          # languages with brackets we can match
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "site-packages",
    "dist", "build", ".next", ".nuxt", ".svelte-kit", ".output", "coverage", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", ".nox", ".idea", ".gradle", "target", "vendor",
    "bower_components", ".terraform", ".cache", ".parcel-cache", ".turbo", ".yarn",
    ".pnpm-store", ".expo", "Pods", "DerivedData",
}
SKIP_FILES = ["*.min.js", "*.min.css", "*.map", "*.lock", "package-lock.json",
              "pnpm-lock.yaml", "yarn.lock", "*.bundle.js", "*.chunk.js"]

# --------------------------------------------------------------------------- patterns
KEYWORD = r"(?i:model|deployment|engine)"
KEY = r"(?:[A-Za-z_$][\w$-]*?)?" + KEYWORD + r"[\w$-]*"          # e.g. model, openai_model, modelId
KEY_NODASH = r"(?:[A-Za-z_$][\w$]*?)?" + KEYWORD + r"[\w$]*"
KEY_MODEL_ONLY = r"(?:[A-Za-z_$][\w$]*?)?(?i:model)[\w$]*"
KEY_ENV = r"(?:[A-Za-z_][A-Za-z0-9_]*?)?" + KEYWORD + r"[A-Za-z0-9_]*"
QUOTED_VALUE = r"(?P<prefix>[rRbBuUfF]{0,2})(?P<q>[\"'`])(?P<val>[^\"'`\r\n]{1,200}?)(?P=q)"

# model="x"   "model": "x"   model: 'x'   MODEL = "x"   if model == "x"
R_KV_LITERAL = re.compile(
    r"(?<![\w$-])(?P<kq>[\"']?)(?P<key>" + KEY + r")(?P=kq)"
    r"\s*(?P<op>===|!==|==|!=|=|:)\s*" + QUOTED_VALUE)
# openai_model: str = "x"      const MODEL: string = "x"
R_TYPED = re.compile(
    r"(?<![\w$-])(?P<key>" + KEY_NODASH + r")\s*:\s*[A-Za-z_][\w.\[\]|, ]{0,40}?\s*=\s*" + QUOTED_VALUE)
# model: someProvider("x")     model=provider.chat("x")
R_FACTORY = re.compile(
    r"(?<![\w$-])(?P<kq>[\"']?)(?P<key>" + KEY_MODEL_ONLY + r")(?P=kq)\s*[:=]\s*"
    r"(?P<fn>[A-Za-z_$][\w$.]*)\(\s*(?P<q>[\"'`])(?P<val>[^\"'`\r\n]{1,200}?)(?P=q)")
FACTORY_SKIP_FN = re.compile(
    r"(?i)(getenv|environ|env\.get|\.get$|^get$|^env$|^config$|^str$|^string$|^number$|"
    r"^int$|^float$|^bool$|^require$|fetch$)")
# GenerativeModel("x")   init_chat_model("x")
R_POSITIONAL = re.compile(
    r"\b(?P<fn>GenerativeModel|getGenerativeModel|init_chat_model)\(\s*(?P<q>[\"'])"
    r"(?P<val>[^\"'\r\n]{1,200}?)(?P=q)")
# FALLBACK_MODELS = ["a", "b"]    "models": {"fast": "a"}
R_LIST_START = re.compile(
    r"(?<![\w$-])(?P<kq>[\"']?)(?P<key>" + KEY_MODEL_ONLY + r")(?P=kq)"
    r"\s*(?::\s*[\w.\[\]|, ]{0,40}?\s*=|[:=])\s*(?P<open>[\[{])")
R_STRING = re.compile(r"(?P<q>[\"'`])(?P<val>[^\"'`\r\n]{1,120}?)(?P=q)(?P<after>\s*:)?")
# YAML / INI without quotes:   model: old-model-v1
R_CFG_UNQUOTED = re.compile(
    r"^(?P<indent>[ \t]*)(?:-[ \t]+)?(?P<key>[\w.$-]*?" + KEYWORD + r"[\w.$-]*)[ \t]*[:=][ \t]*"
    r"(?P<val>[^\s\"'#\[{|>&*!%@`,][^#;\n]*?)[ \t]*(?:[#;].*)?$", re.M)
# .env, shell, Dockerfile, docker-compose:   OPENAI_MODEL=old-model-v1
R_ENV_LINE = re.compile(
    r"^[ \t]*(?:-[ \t]*)?[\"']?(?:export[ \t]+|ENV[ \t]+|ARG[ \t]+)?(?P<key>" + KEY_ENV + r")"
    r"[ \t]*=[ \t]*(?P<q>[\"']?)(?P<val>[^\"'\s#]+)(?P=q)", re.M)
R_ENV_ANY = re.compile(
    r"^[ \t]*(?:-[ \t]*)?[\"']?(?:export[ \t]+|ENV[ \t]+|ARG[ \t]+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)"
    r"[ \t]*=[ \t]*[\"']?(?P<val>[^\"'\s#]*)", re.M)
# Environment variable reads in code
_V = r"[A-Za-z_][A-Za-z0-9_]*"
R_ENV_READ = re.compile(
    r"(?:"
    r"(?:\bos\.)?\bgetenv\(\s*(?P<q1>[\"'])(?P<v1>" + _V + r")(?P=q1)"
    r"(?:\s*,\s*(?:default\s*=\s*)?(?P<d1q>[\"'])(?P<d1>[^\"'\r\n]*)(?P=d1q))?"
    r"(?:\s*\)\s*(?:or|\|\|)\s*(?P<d1bq>[\"'])(?P<d1b>[^\"'\r\n]*)(?P=d1bq))?"
    r"|(?:\bos\.)?\benviron\.get\(\s*(?P<q2>[\"'])(?P<v2>" + _V + r")(?P=q2)"
    r"(?:\s*,\s*(?P<d2q>[\"'])(?P<d2>[^\"'\r\n]*)(?P=d2q))?"
    r"(?:\s*\)\s*or\s*(?P<d2bq>[\"'])(?P<d2b>[^\"'\r\n]*)(?P=d2bq))?"
    r"|(?:\bos\.environ|\bENV)\[\s*(?P<q3>[\"'])(?P<v3>" + _V + r")(?P=q3)\s*\]"
    r"|\bENV\.fetch\(\s*(?P<q4>[\"'])(?P<v4>" + _V + r")(?P=q4)"
    r"(?:\s*,\s*(?P<d4q>[\"'])(?P<d4>[^\"'\r\n]*)(?P=d4q))?"
    r"|\b(?:process\.env|import\.meta\.env)(?:\.(?P<v5>[A-Za-z_$][\w$]*)"
    r"|\[\s*(?P<q5>[\"'])(?P<v6>" + _V + r")(?P=q5)\s*\])"
    r"(?:\s*(?:\|\||\?\?)\s*(?P<d5q>[\"'`])(?P<d5>[^\"'`\r\n]*)(?P=d5q))?"
    r"|\bDeno\.env\.get\(\s*(?P<q6>[\"'])(?P<v7>" + _V + r")(?P=q6)\s*\)"
    r"(?:\s*(?:\|\||\?\?)\s*(?P<d6q>[\"'`])(?P<d6>[^\"'`\r\n]*)(?P=d6q))?"
    r"|\b(?:env|config)\(\s*(?P<q7>[\"'])(?P<v8>" + _V + r")(?P=q7)"
    r"(?:\s*,\s*(?:default\s*=\s*)?(?P<d7q>[\"'])(?P<d7>[^\"'\r\n]*)(?P=d7q))?"
    r")")
R_ALIAS = re.compile(
    r"^\s*(?:export\s+)?(?:(?:const|let|var|final|static|private|public|readonly|val)\s+)*"
    r"(?P<alias>[A-Za-z_$][\w$.]*)\s*(?::[^=]{1,40})?=\s*$")
# model=SOME_VARIABLE inside an SDK call
R_MODEL_EXPR = re.compile(
    r"(?<![\w$-])(?P<kq>[\"']?)(?P<key>model|model_name|modelName|model_id|modelId|engine|"
    r"deployment_name|deploymentName|azure_deployment|deployment_id)(?P=kq)\s*[:=]\s*"
    r"(?P<expr>[A-Za-z_$][\w$.]*(?:\[[^\]\r\n]{1,60}\])?(?:\([^()\r\n]{0,80}\))?)")
R_ANY_KEY = re.compile(
    r"(?<![\w$-])(?P<kq>[\"']?)(?P<key>[A-Za-z_$][\w$-]{1,40})(?P=kq)\s*(?::(?!:)|=(?![=>]))\s*")

# SDK call sites. "weak" patterns are common words, so they only count when the call
# also mentions a model or a typical AI setting.
SDK_PATTERNS = [
    (r"\.chat\.completions\.(?:create|parse|stream)\s*\(", "Chat Completions call (OpenAI-style SDK)", False),
    (r"\.responses\.(?:create|parse|stream)\s*\(", "Responses API call (OpenAI-style SDK)", True),
    (r"(?<!chat)\.completions\.create\s*\(", "Legacy Completions call (OpenAI-style SDK)", True),
    (r"\bChatCompletion\.a?create\s*\(", "Legacy ChatCompletion call (OpenAI SDK before v1)", False),
    (r"\bopenai\.Completion\.a?create\s*\(", "Legacy Completion call (OpenAI SDK before v1)", False),
    (r"\.embeddings\.create\s*\(|\bEmbedding\.a?create\s*\(", "Embeddings call", False),
    (r"\.images\.(?:generate|edit|create_variation)\s*\(", "Image generation call", True),
    (r"\.audio\.(?:transcriptions|translations|speech)\.create\s*\(", "Audio call", True),
    (r"\.messages\.(?:create|stream|count_tokens|countTokens)\s*\(", "Messages API call (Anthropic-style SDK)", True),
    (r"\.messages\.batches\.create\s*\(", "Message Batches call (Anthropic-style SDK)", True),
    (r"\.(?:generate_content|generate_content_async|generateContent|generateContentStream)\s*\(",
     "Generate content call (Google-style SDK)", False),
    (r"\b(?:GenerativeModel|getGenerativeModel)\s*\(", "Model object (Google-style SDK)", False),
    (r"\.(?:invoke_model|invoke_model_with_response_stream|converse|converse_stream)\s*\("
     r"|\bnew\s+(?:InvokeModel|InvokeModelWithResponseStream|Converse|ConverseStream)Command\s*\(",
     "AWS Bedrock runtime call", True),
    (r"\b(?:ChatOpenAI|AzureChatOpenAI|ChatAnthropic|ChatVertexAI|ChatGoogleGenerativeAI|ChatBedrock|"
     r"ChatBedrockConverse|OpenAIEmbeddings|AzureOpenAIEmbeddings|init_chat_model)\s*\(",
     "LangChain model wrapper", False),
    (r"\b(?:generateText|streamText|generateObject|streamObject)\s*\(", "Vercel AI SDK call", True),
    (r"\blitellm\.a?(?:completion|embedding|responses)\s*\(", "LiteLLM call", False),
]
SDK_RES = [(re.compile(p), label, weak) for p, label, weak in SDK_PATTERNS]
AI_HINT = re.compile(r"\b(model|modelId|model_id|max_tokens|maxTokens|max_output_tokens|maxOutputTokens|"
                     r"max_completion_tokens|temperature|prompt)\b")
HTTP_HINT = re.compile(r"(api\.openai\.com|api\.anthropic\.com|openai\.azure\.com|generativelanguage\.googleapis\.com|"
                       r"aiplatform\.googleapis\.com|bedrock-runtime|/chat/completions|/v1/messages\b|/v1/responses\b)")

PARAM_PATTERNS = [
    ("max_completion_tokens", r"max[_-]?completion[_-]?tokens"),
    ("max_output_tokens", r"max[_-]?output[_-]?tokens"),
    ("max_new_tokens", r"max[_-]?new[_-]?tokens"),
    ("max_tokens", r"max[_-]?tokens(?:[_-]?to[_-]?sample)?"),
    ("temperature", r"temperature"),
    ("top_p", r"top[_-]?p"),
    ("top_k", r"top[_-]?k"),
    ("frequency_penalty", r"frequency[_-]?penalty"),
    ("presence_penalty", r"presence[_-]?penalty"),
]
PARAM_EXACT = [re.compile(p, re.I) for _, p in PARAM_PATTERNS]
PARAM_SUFFIX = [re.compile(r"(?:^|[_.-])(?:" + p + r")$", re.I) for _, p in PARAM_PATTERNS]

IGNORE_KEY_PARTS = (
    "viewmodel", "ngmodel", "v-model", "modelvalue", "model_dump", "model_validate", "model_config",
    "model_fields", "model_class", "modelclass", "datamodel", "data_model", "model_construct",
    "model_copy", "model_json", "model_post_init", "modelref", "model_ref", "modelstate",
    "model_state", "model_path", "modelpath", "model_dir", "modeldir", "model_file", "modelfile",
)
DEPLOY_KEYS = {"deployment", "deploymentname", "deploymentid", "azuredeployment", "azuredeploymentname"}
GENERIC_NAMES = {"model", "model_name", "modelname", "model_id", "modelid", "engine", "deployment",
                 "deployment_name", "deploymentname", "self.model", "this.model", "name", "id"}
NOT_A_MODEL = {"true", "false", "null", "none", "nil", "undefined", "yes", "no", "on", "off", "~"}
SECRET_KEY_RE = re.compile(
    r"(?i)((?:api[_-]?key|secret|token|password|passwd|authorization|bearer)[\"']?\s*[:=]\s*[\"']?)"
    r"([^\"'\s,;)]{6,})")
SECRET_VALUE_RE = re.compile(r"\b(?:sk|pk|rk)[-_][A-Za-z0-9_\-]{12,}|\bAKIA[0-9A-Z]{16}\b|\bAIza[0-9A-Za-z_\-]{30,}")

STATUS_ORDER = ["RETIRED", "RETIRING SOON", "SCHEDULED", "LISTED (NO DATE)", "CHECK VALUE", "NOT IN LIST"]
LITERAL_HOW = {"hard-coded", "comparison in code", "config file", "env file", "env var + default in code",
               "list/map of model names", "text match"}


# --------------------------------------------------------------------------- data classes
@dataclass
class Finding:
    file: str
    line: int
    model: str
    how_set: str
    offset: int = 0            # character position in the file (used to group references by call)
    key: str = ""
    call_type: str = ""
    params: str = ""
    snippet: str = ""
    confidence: str = "medium"
    alias: str = ""            # variable that receives an env var read (for cross-references)
    ref_name: str = ""         # variable or env var name this reference depends on
    resolved: str = ""         # values found for ref_name elsewhere
    resolved_models: list = field(default_factory=list)
    in_sdk: bool = False
    status: str = ""
    retirement_date: str = ""
    days_left: object = ""
    replacement: str = ""
    provider: str = ""
    source_url: str = ""
    match: str = ""
    list_note: str = ""

    @property
    def literal(self) -> bool:
        return self.how_set in LITERAL_HOW


@dataclass
class SdkCall:
    start: int
    open: int
    close: int
    label: str
    line: int


# --------------------------------------------------------------------------- helpers
def redact(text: str) -> str:
    text = SECRET_KEY_RE.sub(lambda m: m.group(1) + "***", text)
    return SECRET_VALUE_RE.sub("***", text)


def key_kind(key: str):
    k = key.lower()
    if any(part in k for part in IGNORE_KEY_PARTS):
        return None
    if "model" in k:
        return "model"
    squashed = re.sub(r"[^a-z]", "", k)
    if squashed in DEPLOY_KEYS or ("deployment" in squashed and any(
            w in squashed for w in ("openai", "azure", "llm", "chat", "completion", "embedding"))):
        return "deployment"
    if squashed == "engine" or (squashed.endswith("engine") and squashed.startswith(("openai", "azure", "llm"))):
        return "engine"
    return None


def looks_like_model(val: str) -> bool:
    v = val.strip()
    if not (2 <= len(v) <= 120) or not re.search(r"[A-Za-z]", v):
        return False
    if v.lower() in NOT_A_MODEL:
        return False
    if re.search(r"\s", v) and "{" not in v:
        return False
    if v.startswith(("http://", "https://", "/", "./", "../", "~")):
        return False
    if re.search(r"\.(py|js|ts|json|ya?ml|txt|md|csv|pt|bin|gguf|onnx|pkl|h5|safetensors|joblib)$", v, re.I):
        return False
    return True


def id_like(val: str) -> bool:
    return bool(re.search(r"[\d\-.:/@]", val))


def param_name(key: str, allow_suffix: bool):
    patterns = PARAM_SUFFIX if allow_suffix else PARAM_EXACT
    for (canon, _), rx in zip(PARAM_PATTERNS, patterns):
        if (rx.search(key) if allow_suffix else rx.fullmatch(key)):
            return canon
    return None


def skip_string(text: str, i: int, lang: str) -> int:
    """Return the index just after the string literal that starts at text[i]."""
    n, q = len(text), text[i]
    if lang == "py" and text.startswith(q * 3, i):
        j = i + 3
        while j < n:
            if text[j] == "\\":
                j += 2
                continue
            if text.startswith(q * 3, j):
                return j + 3
            j += 1
        return n
    multiline = q == "`"
    j = i + 1
    while j < n:
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == q:
            return j + 1
        if ch == "\n" and not multiline:
            return j
        j += 1
    return n


def read_value(text: str, i: int, limit: int) -> str:
    """Read a parameter value up to the next top-level comma, bracket or line end."""
    n = min(len(text), limit)
    while i < n and text[i] in " \t":
        i += 1
    start, depth = i, 0
    while i < n:
        c = text[i]
        if c in "\"'`":
            i = skip_string(text, i, "js")
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and (c in ",;\n" or c == "#" or text.startswith("//", i)):
            break
        i += 1
    val = " ".join(text[start:i].split())
    return val if len(val) <= 60 else val[:57] + "..."


# --------------------------------------------------------------------------- one file
class FileScan:
    LINE_COMMENTS = {"py": ("#",), "rb": ("#",), "js": ("//",), "tf": ("#", "//"), "json": ()}

    def __init__(self, rel: str, text: str, lang: str):
        self.rel, self.text, self.lang = rel, text, lang
        self.lines = text.split("\n")
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.pairs, self.skips = [], []
        if lang in CODE_LANGS:
            self._match_brackets()
        self.skip_starts = [s[0] for s in self.skips]
        self.pair_close = {o: c for o, c in self.pairs}
        self.calls = self._find_sdk_calls()
        self.findings: list[Finding] = []
        self._seen = set()

    # -- structure
    def _match_brackets(self):
        text, lang, n = self.text, self.lang, len(self.text)
        line_comments = self.LINE_COMMENTS.get(lang, ())
        block = lang in ("js", "tf")
        stack, i = [], 0
        while i < n:
            c = text[i]
            if c in "\"'`" and not (c == "`" and lang != "js"):
                j = skip_string(text, i, lang)
                self.skips.append((i, j, "string"))
                i = j
                continue
            if line_comments and c in "#/" and any(text.startswith(p, i) for p in line_comments):
                j = text.find("\n", i)
                j = n if j < 0 else j
                self.skips.append((i, j, "comment"))
                i = j
                continue
            if block and c == "/" and text.startswith("/*", i):
                j = text.find("*/", i + 2)
                j = n if j < 0 else j + 2
                self.skips.append((i, j, "comment"))
                i = j
                continue
            if c in "([{":
                stack.append((c, i))
            elif c in ")]}":
                want = {")": "(", "]": "[", "}": "{"}[c]
                for k in range(len(stack) - 1, -1, -1):
                    if stack[k][0] == want:
                        self.pairs.append((stack[k][1], i))
                        del stack[k:]
                        break
            i += 1

    def skip_kind(self, offset: int):
        k = bisect.bisect_right(self.skip_starts, offset) - 1
        if k >= 0 and self.skips[k][0] <= offset < self.skips[k][1]:
            return self.skips[k][2]
        return None

    def line_of(self, offset: int) -> int:
        return bisect.bisect_right(self.line_starts, offset)

    def line_text(self, line_no: int) -> str:
        return self.lines[line_no - 1] if 0 < line_no <= len(self.lines) else ""

    def enclosing(self, offset: int):
        best = None
        for o, c in self.pairs:
            if o < offset < c and (best is None or o > best[0]):
                best = (o, c)
        return best

    def call_at(self, offset: int):
        best = None
        for call in self.calls:
            if call.open < offset < call.close and (best is None or call.open > best.open):
                best = call
        return best

    def is_comment_line(self, line_no: int) -> bool:
        s = self.line_text(line_no).lstrip()
        return s.startswith(("#", "//", "/*", "*", "<!--", ";", "--"))

    def _find_sdk_calls(self):
        calls = []
        if self.lang not in ("py", "js", "rb"):
            return calls
        for rx, label, weak in SDK_RES:
            for m in rx.finditer(self.text):
                if self.skip_kind(m.start()):
                    continue
                open_idx = m.end() - 1
                close_idx = self.pair_close.get(open_idx, min(len(self.text), open_idx + 2000))
                if weak and not AI_HINT.search(self.text, open_idx, close_idx):
                    continue
                calls.append(SdkCall(m.start(), open_idx, close_idx, label, self.line_of(m.start())))
        return calls

    # -- parameters near a reference
    def params_for(self, offset: int, line_no: int) -> str:
        if self.lang == "yaml":
            return self._yaml_params(line_no)
        if self.lang in ("ini", "toml"):
            return self._section_params(line_no)
        if self.lang in ("env", "sh"):
            return self._env_params()
        call = self.call_at(offset)
        span = (call.open, call.close) if call else self.enclosing(offset)
        if not span:
            return ""
        found, seen = [], set()
        for m in R_ANY_KEY.finditer(self.text, span[0] + 1, span[1]):
            key = m.group("key")
            if key in seen or not param_name(key, allow_suffix=False):
                continue
            val = read_value(self.text, m.end(), span[1])
            if val:
                seen.add(key)
                found.append(f"{key}={val}")
        return ", ".join(found)

    def _collect_cfg_param(self, line: str, out: list):
        m = re.match(r"^\s*(?:-\s+)?[\"']?([\w.$-]+)[\"']?\s*[:=]\s*(.*?)\s*(?:[#;].*)?$", line)
        if m and m.group(2) and param_name(m.group(1), allow_suffix=True):
            out.append(f"{m.group(1)}={m.group(2).strip(chr(34) + chr(39))}")

    def _yaml_params(self, line_no: int) -> str:
        def indent(s):
            m = re.match(r"^(\s*)(-\s+)?", s)
            return len(m.group(1)) + (len(m.group(2)) if m.group(2) else 0)
        base, out = indent(self.line_text(line_no)), []
        for step in (-1, 1):
            i = line_no - 1 + step
            while 0 <= i < len(self.lines):
                s = self.lines[i]
                if not s.strip() or s.lstrip().startswith("#"):
                    i += step
                    continue
                ind = indent(s)
                if ind < base:
                    break
                if ind == base:
                    self._collect_cfg_param(s, out)
                i += step
        return ", ".join(out)

    def _section_params(self, line_no: int) -> str:
        start, end = 0, len(self.lines)
        for i in range(line_no - 2, -1, -1):
            if self.lines[i].strip().startswith("["):
                start = i + 1
                break
        for i in range(line_no, len(self.lines)):
            if self.lines[i].strip().startswith("["):
                end = i
                break
        out = []
        for s in self.lines[start:end]:
            self._collect_cfg_param(s, out)
        return ", ".join(out)

    def _env_params(self) -> str:
        out = []
        for m in R_ENV_ANY.finditer(self.text):
            if m.group("val") and param_name(m.group("key"), allow_suffix=True):
                out.append(f"{m.group('key')}={m.group('val')}")
        return ", ".join(out)

    # -- adding findings
    def add(self, offset: int, model: str, how_set: str, key: str = "", default_type: str = "",
            alias: str = "", ref_name: str = "", line_no: int = 0) -> bool:
        line_no = line_no or self.line_of(offset)
        dedupe = (line_no, model.strip().lower())
        if dedupe in self._seen:
            return False
        self._seen.add(dedupe)
        call = self.call_at(offset) if self.lang in ("py", "js", "rb") else None
        f = Finding(file=self.rel, line=line_no, model=model.strip(), how_set=how_set, offset=offset,
                    key=key, alias=alias, ref_name=ref_name, in_sdk=call is not None)
        f.call_type = self._call_type(offset, line_no, call, default_type)
        f.params = self.params_for(offset, line_no)
        f.snippet = redact(" ".join(self.line_text(line_no).split()))[:160]
        self.findings.append(f)
        return True

    def _call_type(self, offset, line_no, call, default_type):
        if call:
            return call.label
        if self.lang == "env":
            return "Environment file"
        if self.lang in ("yaml", "toml", "ini"):
            return "Config file"
        if self.lang == "sh":
            return "Shell script / Dockerfile"
        if self.lang == "json":
            return "JSON file"
        if default_type:
            return default_type
        if self.is_comment_line(line_no) or self.skip_kind(offset) == "comment":
            return "Comment"
        enc = self.enclosing(offset)
        if enc:
            return {"(": "Function argument (check what the function does)",
                    "{": "Settings object / dictionary",
                    "[": "List of values"}[self.text[enc[0]]]
        return "Constant or variable"

    def lines_with_findings(self):
        return {f.line for f in self.findings}

    # -- the rules, in priority order
    def scan(self, retirements: "RetirementList"):
        code = self.lang in ("py", "js", "rb")
        text = self.text
        if code:
            self._rule_env_reads()
        if self.lang in CODE_LANGS or self.lang in ("yaml", "toml", "ini", "sh"):
            self._rule_key_literals()
        if code:
            self._rule_factories_and_positionals()
        if self.lang in CODE_LANGS:
            self._rule_lists()
        if self.lang in ("yaml", "ini"):
            for m in R_CFG_UNQUOTED.finditer(text):
                val = m.group("val").strip()
                if key_kind(m.group("key")) and looks_like_model(val):
                    self.add(m.start("key"), val, "config file", key=m.group("key"))
        if self.lang in ("env", "sh", "yaml", "ini"):
            for m in R_ENV_LINE.finditer(text):
                val = m.group("val")
                if key_kind(m.group("key")) and looks_like_model(val):
                    self.add(m.start("key"), val, "env file" if self.lang == "env" else "config file",
                             key=m.group("key"))
        if code:
            self._rule_model_expressions()
            self._rule_calls_without_model()
        self._rule_retirement_ids(retirements)
        self._rule_http_endpoints()
        return self.findings

    def _rule_env_reads(self):
        for m in R_ENV_READ.finditer(self.text):
            if self.skip_kind(m.start()) == "comment":
                continue
            g = m.groupdict()
            var = next((g[k] for k in ("v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8") if g.get(k)), None)
            if not var or not key_kind(var):
                continue
            default = next((g[k] for k in ("d1", "d1b", "d2", "d2b", "d4", "d5", "d6", "d7")
                            if g.get(k) is not None), None)
            line_no = self.line_of(m.start())
            line_start = self.line_starts[line_no - 1]
            am = R_ALIAS.match(self.text[line_start:m.start()])
            alias = am.group("alias").split(".")[-1] if am else ""
            if default and looks_like_model(default):
                self.add(m.start(), default, "env var + default in code", key=var, alias=alias,
                         default_type="Environment variable read")
            else:
                self.add(m.start(), f"${var}", "env var (set outside code)", key=var, alias=alias,
                         ref_name=var, default_type="Environment variable read")

    def _rule_key_literals(self):
        for rx in (R_KV_LITERAL, R_TYPED):
            for m in rx.finditer(self.text):
                key, val = m.group("key"), m.group("val")
                kind = key_kind(key)
                if not kind or not looks_like_model(val):
                    continue
                if self.skip_kind(m.start("key")) == "comment":
                    continue
                op = m.groupdict().get("op") or "="
                default_type = ""
                if op in ("==", "===", "!=", "!=="):
                    how, default_type = "comparison in code", "Comparison (the code branches on the model name)"
                elif self.lang in ("yaml", "toml", "ini", "json", "sh"):
                    how = "config file"
                else:
                    how = "hard-coded"
                if "{" in val:
                    how = "built at run time"
                self.add(m.start("key"), val, how, key=key, default_type=default_type)

    def _rule_factories_and_positionals(self):
        for m in R_FACTORY.finditer(self.text):
            fn, val = m.group("fn"), m.group("val")
            if FACTORY_SKIP_FN.search(fn) or re.fullmatch(r"[A-Z][A-Z0-9_]+", val):
                continue
            if key_kind(m.group("key")) and looks_like_model(val) and not self.skip_kind(m.start()):
                self.add(m.start("key"), val, "hard-coded", key=m.group("key"))
        for m in R_POSITIONAL.finditer(self.text):
            if looks_like_model(m.group("val")) and not self.skip_kind(m.start()):
                self.add(m.start(), m.group("val"), "hard-coded", key=m.group("fn"))

    def _rule_lists(self):
        for m in R_LIST_START.finditer(self.text):
            if not key_kind(m.group("key")) or self.skip_kind(m.start()):
                continue
            open_idx = m.start("open")
            close_idx = self.pair_close.get(open_idx)
            if close_idx is None or close_idx - open_idx > 3000:
                continue
            for s in R_STRING.finditer(self.text, open_idx, close_idx):
                val = s.group("val")
                if s.group("after") or not looks_like_model(val) or not re.search(r"[\d-]", val):
                    continue
                self.add(s.start(), val, "list/map of model names", key=m.group("key"))

    def _rule_model_expressions(self):
        busy = self.lines_with_findings()
        for call in self.calls:
            for m in R_MODEL_EXPR.finditer(self.text, call.open + 1, call.close):
                expr = m.group("expr")
                line_no = self.line_of(m.start())
                if line_no in busy or re.match(r"(os\.|process\.env|import\.meta|Deno\.|getenv|environ|ENV)", expr):
                    continue
                enc = self.enclosing(m.start())
                if enc and enc != (call.open, call.close) and self.text[enc[0]] != "{":
                    continue  # belongs to a nested call, not to this SDK call
                name = re.sub(r"\(.*$", "", expr)
                name = re.sub(r"\[[\"']?([^\]\"']+)[\"']?\]$", r".\1", name).split(".")[-1]
                self.add(m.start(), expr, "variable", key=m.group("key"), ref_name=name)

    def _rule_calls_without_model(self):
        for call in self.calls:
            if any(call.start <= f.offset <= call.close for f in self.findings):
                continue
            self.add(call.open + 1, "(not visible here)", "not visible", line_no=call.line)

    def _rule_retirement_ids(self, retirements: "RetirementList"):
        if not retirements.rx:
            return
        for m in retirements.rx.finditer(self.text):
            line_no = self.line_of(m.start())
            if any(f.line == line_no and m.group(1).lower() in f.model.lower() for f in self.findings):
                continue
            s, e = m.start(), m.end()
            while s > 0 and re.match(r"[\w.:/@+-]", self.text[s - 1]):
                s -= 1
            while e < len(self.text) and re.match(r"[\w.:/@+-]", self.text[e]):
                e += 1
            token = self.text[s:e].strip(".:/-")
            self.add(m.start(), token, "text match", key="", line_no=line_no,
                     default_type="Comment" if (self.is_comment_line(line_no) or
                                                self.skip_kind(m.start()) == "comment") else "")

    def _rule_http_endpoints(self):
        if self.lang not in ("py", "js", "rb"):
            return
        for m in HTTP_HINT.finditer(self.text):
            if self.skip_kind(m.start()) == "comment":
                continue
            line_no = self.line_of(m.start())
            if line_no in self.lines_with_findings():
                continue
            enc = self.enclosing(m.start())
            inside = [f for f in self.findings if enc and enc[0] < f.offset < enc[1]]
            for f in inside:
                if not f.in_sdk:
                    f.call_type = "Direct HTTP call to an AI API"
            if inside:
                continue
            self.add(m.start(), "(not visible here)", "not visible", line_no=line_no,
                     default_type="Direct HTTP call to an AI API (check the request body)")


# --------------------------------------------------------------------------- retirement list
class RetirementList:
    def __init__(self, path: Path | None, warnings: list):
        self.path, self.rows, self.by_id = path, [], {}
        self.rx = None
        if path is None:
            warnings.append("No retirement list given (--retirements). Every model shows as NOT IN LIST.")
            return
        if not path.exists():
            raise SystemExit(f"Retirement list not found: {path}")
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            header = [h.strip().lower() for h in (reader.fieldnames or [])]
            missing = [c for c in REQUIRED_COLUMNS if c not in header]
            if missing:
                raise SystemExit(f"{path.name} is missing column(s): {', '.join(missing)}. "
                                 f"Required header: {','.join(REQUIRED_COLUMNS)}")
            for n, raw in enumerate(reader, start=2):
                row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
                if not row.get("model_id") or row["provider"].startswith("#"):
                    continue
                date_txt = row.get("retirement_date", "")
                row["_date"] = None
                if date_txt and date_txt.upper() not in ("TBD", "UNKNOWN", "N/A"):
                    try:
                        row["_date"] = dt.date.fromisoformat(date_txt)
                    except ValueError:
                        warnings.append(f"{path.name} line {n}: retirement_date '{date_txt}' is not "
                                        f"YYYY-MM-DD, so it was ignored.")
                if not row.get("source_url"):
                    warnings.append(f"{path.name} line {n}: no source_url for {row['model_id']}. "
                                    f"Always record where the date came from.")
                self.rows.append(row)
                self.by_id.setdefault(row["model_id"].lower(), []).append(row)
        ids = [i for i in self.by_id if i != EXAMPLE_MODEL_ID]
        if not ids:
            warnings.append(f"{path.name} only has the fake example row. Fill it from each provider's "
                            f"official deprecations page before trusting this scan (see README).")
        elif EXAMPLE_MODEL_ID in self.by_id:
            warnings.append(f"{path.name} still contains the fake example row '{EXAMPLE_MODEL_ID}'. Delete it.")
        if self.by_id:
            alts = "|".join(re.escape(i) for i in sorted(self.by_id, key=len, reverse=True))
            self.rx = re.compile(r"(?<![A-Za-z0-9])(" + alts + r")(?![A-Za-z0-9])", re.I)

    def lookup(self, model: str):
        """Return (row, match_type, note) for the most urgent matching entry, or (None, '', '')."""
        m = model.strip().lower()
        match_type, rows = "", None
        if m in self.by_id:
            match_type, rows = "exact", self.by_id[m]
        elif self.rx:
            best = max((x.group(1).lower() for x in self.rx.finditer(m)), key=len, default=None)
            if best:
                match_type, rows = "partial", self.by_id[best]
        if not rows:
            return None, "", ""
        dated = [r for r in rows if r["_date"]]
        row = min(dated, key=lambda r: r["_date"]) if dated else rows[0]
        note = f"{len(rows)} entries in the list (earliest date shown)" if len(rows) > 1 else ""
        return row, match_type, note


def status_for(row, today: dt.date, warn_days: int):
    if row["_date"] is None:
        return "LISTED (NO DATE)", ""
    days = (row["_date"] - today).days
    if days < 0:
        return "RETIRED", days
    return ("RETIRING SOON" if days <= warn_days else "SCHEDULED"), days


# --------------------------------------------------------------------------- whole repo
def detect_lang(path: Path):
    name = path.name
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return "env"
    if name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".dockerfile"):
        return "sh"
    return LANG_BY_EXT.get(path.suffix.lower())


def iter_files(root: Path, excludes: list, out_dir: Path | None, extra_exts: dict):
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        keep = []
        for name in dirnames:
            p = d / name
            rel = p.relative_to(root).as_posix()
            if name in SKIP_DIRS or (p / "pyvenv.cfg").exists():
                continue
            if out_dir is not None and p.resolve() == out_dir:
                continue
            if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g) for g in excludes):
                continue
            keep.append(name)
        dirnames[:] = sorted(keep)
        for name in sorted(filenames):
            p = d / name
            rel = p.relative_to(root).as_posix()
            lang = detect_lang(p) or extra_exts.get(p.suffix.lower())
            if not lang or any(fnmatch.fnmatch(name, g) for g in SKIP_FILES):
                continue
            if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g) for g in excludes):
                continue
            yield p, rel, lang


def read_text(path: Path, max_bytes: int):
    try:
        if path.stat().st_size > max_bytes:
            return None, "too large"
        data = path.read_bytes()
    except OSError:
        return None, "unreadable"
    if b"\x00" in data[:8192]:
        return None, "binary"
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n"), None


def notebook_cells(text: str):
    try:
        nb = json.loads(text)
    except ValueError:
        return []
    cells = nb.get("cells", []) if isinstance(nb, dict) else []
    out = []
    for i, cell in enumerate(cells, start=1):
        if isinstance(cell, dict) and cell.get("cell_type") == "code":
            src = cell.get("source", "")
            out.append((i, "".join(src) if isinstance(src, list) else str(src)))
    return out


def resolve_references(findings: list):
    defs = {}
    for f in findings:
        if f.literal:
            for name in {f.key.lower(), f.alias.lower()}:
                if name and name not in GENERIC_NAMES and f not in defs.get(name, []):
                    defs.setdefault(name, []).append(f)
    for f in findings:
        if f.literal or not f.ref_name or f.ref_name.lower() in GENERIC_NAMES:
            continue
        cands = [d for d in defs.get(f.ref_name.lower(), []) if d is not f]
        dotted = "." in f.model  # settings.CHAT_MODEL may live in another file
        use = cands if dotted else ([d for d in cands if d.file == f.file] or cands)
        if use:
            f.resolved = "; ".join(f"{d.model} ({d.file}:{d.line})" for d in use[:4])
            if len(use) > 4:
                f.resolved += f"; +{len(use) - 4} more"
            f.resolved_models = [d.model for d in use]


def apply_status(findings: list, retirements: RetirementList, today: dt.date, warn_days: int):
    for f in findings:
        models = [f.model] if f.literal else f.resolved_models
        best = None
        for model in models:
            row, match_type, note = retirements.lookup(model)
            if not row:
                continue
            status, days = status_for(row, today, warn_days)
            rank = STATUS_ORDER.index(status)
            if best is None or rank < best[0]:
                best = (rank, status, days, row, match_type, note)
        if best:
            _, f.status, f.days_left, row, f.match, f.list_note = best
            f.retirement_date = row["retirement_date"]
            f.replacement, f.provider, f.source_url = row["replacement"], row["provider"], row["source_url"]
            f.confidence = "high"
        else:
            f.status = "NOT IN LIST" if f.literal else "CHECK VALUE"
            if f.in_sdk or f.how_set == "not visible":
                f.confidence = "high"
            elif f.how_set == "text match":
                f.confidence = "medium"
            elif key_kind(f.key) == "engine":
                f.confidence = "low"
            elif f.how_set.startswith("env") or f.how_set == "variable" or id_like(f.model):
                f.confidence = "medium"
            else:
                f.confidence = "low"


def scan(root: Path, retirements: RetirementList, excludes, out_dir, max_bytes, extra_exts):
    findings, stats = [], {"files": 0, "skipped": {}}
    for path, rel, lang in iter_files(root, excludes, out_dir, extra_exts):
        text, problem = read_text(path, max_bytes)
        if problem:
            stats["skipped"][problem] = stats["skipped"].get(problem, 0) + 1
            continue
        stats["files"] += 1
        if lang == "ipynb":
            for cell_no, src in notebook_cells(text):
                findings += FileScan(f"{rel} (cell {cell_no})", src, "py").scan(retirements)
        else:
            findings += FileScan(rel, text, lang).scan(retirements)
    return findings, stats


# --------------------------------------------------------------------------- output
CSV_COLUMNS = ["status", "days_left", "retirement_date", "replacement", "file", "line", "model",
               "resolved_model", "how_set", "key", "call_type", "parameters", "confidence", "match",
               "provider", "source_url", "list_note", "snippet"]


def sort_key(f: Finding):
    return (STATUS_ORDER.index(f.status), {"high": 0, "medium": 1, "low": 2}[f.confidence], f.file, f.line)


def write_csv(findings, path: Path):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_COLUMNS)
        for f in findings:
            w.writerow([f.status, f.days_left, f.retirement_date, f.replacement, f.file, f.line, f.model,
                        f.resolved, f.how_set, f.key, f.call_type, f.params, f.confidence, f.match,
                        f.provider, f.source_url, f.list_note, f.snippet])


def md_cell(value) -> str:
    text = " ".join(str(value).split()).replace("|", "\\|").replace("`", "'")
    return text or "-"


def code(value) -> str:
    text = " ".join(str(value).split()).replace("|", "\\|").replace("`", "'")
    return f"`{text}`" if text else "-"


def days_text(f: Finding) -> str:
    if f.days_left == "":
        return "-"
    return f"retired {-f.days_left} days ago" if f.days_left < 0 else f"{f.days_left} days"


def model_text(f: Finding) -> str:
    if f.literal:
        return code(f.model)
    if f.how_set == "not visible":
        return "not visible here"
    shown = code(f.model)
    return f"{shown} = {md_cell(f.resolved)}" if f.resolved else f"{shown} (value not found)"


def write_markdown(findings, path: Path, root: Path, retirements: RetirementList, today, warn_days,
                   stats, warnings):
    main = [f for f in findings if f.confidence != "low"]
    low = [f for f in findings if f.confidence == "low"]
    counts = {s: sum(1 for f in main if f.status == s) for s in STATUS_ORDER}
    files_hit = len({f.file.split(" (cell")[0] for f in main})
    L = [f"# Model reference scan: {root.name}", ""]
    L.append(f"- **Scan date:** {today.isoformat()} (warning window: {warn_days} days)")
    if retirements.path:
        L.append(f"- **Retirement list:** `{retirements.path.name}` "
                 f"({len([i for i in retirements.by_id if i != EXAMPLE_MODEL_ID])} model IDs)")
    skipped = ", ".join(f"{v} {k}" for k, v in stats["skipped"].items())
    L.append(f"- **Files scanned:** {stats['files']}" + (f" (skipped: {skipped})" if skipped else ""))
    L.append(f"- **References found:** {len(main)} in {files_hit} files"
             + (f", plus {len(low)} low-confidence matches (section 5)" if low else ""))
    L.append("- **By status:** " + ", ".join(f"{s}: {counts[s]}" for s in STATUS_ORDER if counts[s]))
    L.append("")
    for w in warnings:
        L.append(f"> **Warning:** {w}")
        L.append("")
    L.append("> This scan is a helper, not a guarantee. Read the code around every hit, and ask the "
             "client about model names set in hosting dashboards, databases or other repos.")
    L.append("")

    urgent = [f for f in main if f.status in ("RETIRED", "RETIRING SOON")]
    L += ["## 1. Needs action now", ""]
    if urgent:
        L.append(f"Already retired, or retiring within {warn_days} days.")
        L.append("")
        L.append("| Status | Where | Model | Retires | Time left | Replacement | Parameters |")
        L.append("|---|---|---|---|---|---|---|")
        for f in urgent:
            L.append(f"| **{f.status}** | {code(f'{f.file}:{f.line}')} | {model_text(f)} | "
                     f"{md_cell(f.retirement_date)} | {days_text(f)} | {code(f.replacement)} | "
                     f"{md_cell(f.params)} |")
    else:
        L.append(f"Nothing in the retirement list is retired or retiring within {warn_days} days.")
    L.append("")

    later = [f for f in main if f.status not in ("RETIRED", "RETIRING SOON")]
    L += ["## 2. Everything else to check", ""]
    if later:
        L.append("SCHEDULED = retires later. CHECK VALUE = the model name comes from a variable or setting "
                 "the scan could not resolve. NOT IN LIST = no retirement entry; check the provider's "
                 "page, because a missing entry does not prove the model is safe.")
        L.append("")
        L.append("| Status | Where | Model | Retires | How it is set | Call type |")
        L.append("|---|---|---|---|---|---|")
        for f in later:
            L.append(f"| {f.status} | {code(f'{f.file}:{f.line}')} | {model_text(f)} | "
                     f"{md_cell(f.retirement_date or '-')} | {md_cell(f.how_set)} | {md_cell(f.call_type)} |")
    else:
        L.append("Nothing else found.")
    L.append("")

    L += ["## 3. All references", ""]
    L.append("| # | Status | File | Line | Model | How it is set | Call type | Parameters | Confidence |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for n, f in enumerate(main, start=1):
        L.append(f"| {n} | {f.status} | {code(f.file)} | {f.line} | {model_text(f)} | {md_cell(f.how_set)} | "
                 f"{md_cell(f.call_type)} | {md_cell(f.params)} | {f.confidence} |")
    L.append("")

    env_rows = {}
    for f in main:
        if f.how_set.startswith("env var") and f.key:
            env_rows.setdefault(f.key, []).append(f)
    env_files = {f.key: f for f in findings if f.how_set == "env file"}
    L += ["## 4. Environment variables to confirm with the client", ""]
    if env_rows:
        L.append("These model names are read from environment variables. Ask the client for the real "
                 "values in staging and production (hosting dashboard, secrets manager, CI settings).")
        L.append("")
        L.append("| Variable | Read in | Default in code | Value in an env file in the repo |")
        L.append("|---|---|---|---|")
        for var, rows in sorted(env_rows.items()):
            where = ", ".join(code(f"{f.file}:{f.line}") for f in rows)
            defaults = ", ".join(sorted({code(f.model) for f in rows if f.literal})) or "none"
            envf = env_files.get(var)
            env_val = f"{code(envf.model)} in {code(envf.file)}" if envf else "-"
            L.append(f"| {code(var)} | {where} | {defaults} | {env_val} |")
    else:
        L.append("No model names are read from environment variables in the scanned code.")
    L.append("")

    L += ["## 5. Low-confidence matches (probably not AI models)", ""]
    if low:
        L.append("| Where | Key | Value | Line |")
        L.append("|---|---|---|---|")
        for f in low:
            L.append(f"| {code(f'{f.file}:{f.line}')} | {code(f.key)} | {code(f.model)} | {code(f.snippet)} |")
    else:
        L.append("None.")
    L.append("")

    L += ["## Next steps", "",
          "1. Open every row in sections 1 and 2 and confirm it is a real model call.",
          "2. Confirm each retirement date and replacement on the provider's official page "
          "(the `source_url` column in the CSV). Note the date you checked.",
          "3. Ask the client for the values of the environment variables in section 4.",
          "4. Search for anything the scan cannot see: model names stored in a database, set in a no-code "
          "tool or hosting dashboard, or used in other repos and scheduled jobs.",
          "5. Note the parameters next to each call. New models may reject some of them or need "
          "different values.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Find AI model references in a codebase and check them against a retirement list.")
    ap.add_argument("repo", help="folder to scan (the client's code)")
    ap.add_argument("--retirements", help="retirement list CSV (default: ../data/retirements.csv next to this script)")
    ap.add_argument("--out-dir", default="scan_output", help="where to write model_scan.csv and model_scan.md")
    ap.add_argument("--today", help="pretend today is this date (YYYY-MM-DD); useful for repeatable reports")
    ap.add_argument("--warn-days", type=int, default=90, help="flag models retiring within this many days (default 90)")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                    help="skip files or folders matching this pattern (repeatable), e.g. --exclude 'tests/*'")
    ap.add_argument("--ext", action="append", default=[], metavar=".EXT",
                    help="also scan files with this extension as plain code (repeatable)")
    ap.add_argument("--max-file-kb", type=int, default=2000, help="skip files larger than this (default 2000 KB)")
    ap.add_argument("--fail-on-flagged", action="store_true",
                    help="exit with code 2 if anything is retired or retiring soon (for CI checks)")
    args = ap.parse_args(argv)

    root = Path(args.repo).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a folder: {root}", file=sys.stderr)
        return 1
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        print(f"--today must look like 2026-10-07, not {args.today!r}", file=sys.stderr)
        return 1
    default_list = Path(__file__).resolve().parent.parent / "data" / "retirements.csv"
    ret_path = Path(args.retirements).expanduser().resolve() if args.retirements else (
        default_list if default_list.exists() else None)
    warnings: list = []
    retirements = RetirementList(ret_path, warnings)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    extra = {(e if e.startswith(".") else "." + e).lower(): "js" for e in args.ext}

    findings, stats = scan(root, retirements, args.exclude, out_dir, args.max_file_kb * 1024, extra)
    resolve_references(findings)
    apply_status(findings, retirements, today, args.warn_days)
    findings.sort(key=sort_key)

    write_csv(findings, out_dir / "model_scan.csv")
    write_markdown(findings, out_dir / "model_scan.md", root, retirements, today, args.warn_days, stats, warnings)

    main_rows = [f for f in findings if f.confidence != "low"]
    print(f"Scanned {stats['files']} files in {root}")
    print(f"Found {len(main_rows)} model references"
          + (f" (+{len(findings) - len(main_rows)} low-confidence)" if len(findings) > len(main_rows) else ""))
    for s in STATUS_ORDER:
        n = sum(1 for f in main_rows if f.status == s)
        if n:
            print(f"  {s:<17} {n}")
    for w in warnings:
        print(f"WARNING: {w}")
    print(f"Wrote {out_dir / 'model_scan.csv'}")
    print(f"Wrote {out_dir / 'model_scan.md'}")
    flagged = any(f.status in ("RETIRED", "RETIRING SOON") for f in main_rows)
    return 2 if (args.fail_on_flagged and flagged) else 0


if __name__ == "__main__":
    sys.exit(main())
