"""
CMV LLM annotation pipeline: prompts, OpenAI and Anthropic batch files, validation,
resubmission.

Every word of annotation guidance shown to the model is read from the SAME protocol
JSON that the human annotation notebook displayed (cmv_annotation_v4_2026_09_24).
The only edits are the mechanical, documented substitutions in `ADAPTATIONS` below;
run `python cmv_llm_batch.py diff` to print every one of them.

Design (per supervisor's requirements):
  * one API call = one metric x one A/B pair + its OP
  * prompts reuse the human definitions, worked examples, and Strong/Weak A/B labels
  * one sentence of reasoning, written before the label
  * batch APIs (OpenAI, Anthropic); faulty rows are re-queued into a new batch until clean

Subcommands
  build     --input CSV --provider openai|anthropic --model M [--reasoning-effort low]
            [--thinking between_tools] [--main-only|--calibration-only] [--orientations both|ab]
  preview   --input CSV  (writes rendered prompts for one pair, all three metrics)
  diff      (prints human-protocol vs LLM-prompt text differences)
  estimate  --requests JSONL [--pricing pricing.csv] [--out-tokens N]
  validate  --requests JSONL --results JSONL [--results JSONL ...] --out-dir DIR
"""
from __future__ import annotations

import argparse, csv, hashlib, html, itertools, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL_VERSION = "cmv_annotation_v4_2026_09_24"
PROTOCOL_PATH = HERE / f"annotation_protocol_{PROTOCOL_VERSION}.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
assert PROTOCOL["version"] == PROTOCOL_VERSION

# Shown on every human annotation screen under each scale question (notebook: SCALE_UI_TEXT).
SCALE_UI_TEXT = (
    "Weak = one response is somewhat better or you only slightly prefer it. "
    "Strong = one response is clearly better. No ties: if they seem nearly equal, "
    "choose the side you lean toward and use Weak."
)
# Shown on the human screen when both evidence boxes were checked.
EVIDENCE_COMPARE_REMINDER = (
    "Both responses provide evidence. Compare the evidence itself, not the overall writing or argument."
)
CHOICES = ["Strong A", "Weak A", "Weak B", "Strong B"]
# Checkbox labels on the human evidence screen.
EV_A = "Response A provides evidence"
EV_B = "Response B provides evidence"
EVIDENCE_COMPARE_TITLE = "EVIDENTIAL SUPPORT — COMPARISON"
SIGNED = {"Strong A": -2, "Weak A": -1, "Weak B": 1, "Strong B": 2}
MARGIN = {"Strong A": 2, "Weak A": 1, "Weak B": 1, "Strong B": 2}
FLIP = {"Strong A": "Strong B", "Weak A": "Weak B", "Weak B": "Weak A", "Strong B": "Strong A"}

METRICS = ["cogency", "effectiveness", "evidence"]
# Column prefixes used by the human annotation CSVs, so LLM output lines up 1:1.
HUMAN_PREFIX = {"cogency": "cogency", "effectiveness": "effect", "evidence": "evidence"}
EXAMPLE_INDEX = {"cogency": [0], "effectiveness": [1], "evidence": [2, 3]}


# ---------------------------------------------------------------------------
# 1. Mechanical adaptations of the human protocol (the ONLY wording changes)
# ---------------------------------------------------------------------------
def _replace_exact(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, f"Protocol text changed; cannot find: {old[:70]!r}"
    return text.replace(old, new)

METRIC_NAME = {"cogency": "Cogency",
               "effectiveness": "Expected Rhetorical Effectiveness",
               "evidence": "Evidential Support"}

def adapted_overview(metric: str) -> str:
    t = PROTOCOL["overview"]
    t = _replace_exact(t,
        "You will make three judgments in this order: Cogency, Expected Rhetorical "
        "Effectiveness, and Evidential Support.",
        f"You will make one judgment: {METRIC_NAME[metric]}.")
    t = _replace_exact(t, "Do not search the web, use AI assistants, look up the users,",
                          "Do not search the web, look up the users,")
    t = _replace_exact(t,
        " Judge each displayed pair on its own. Do not revisit an earlier answer merely to "
        "make your answers form a perfectly consistent ranking across all responses.",
        " Judge the displayed pair on its own.")
    return t

def adapted_scale_intro(metric: str) -> str:
    """The human scale intro names all three metrics; keep only the one being judged."""
    t = PROTOCOL["scale_intro"]
    if metric == "evidence":
        t = _replace_exact(t,
            "For Cogency and Expected Rhetorical Effectiveness, choose exactly one",
            "If both responses provide evidence, choose exactly one")
    else:
        t = _replace_exact(t,
            "For Cogency and Expected Rhetorical Effectiveness, choose exactly one",
            "Choose exactly one")
    t = _replace_exact(t,
        " The same four-way scale appears for Evidential Support only when both responses "
        "are marked as providing evidence.", "")
    return t

def adapted_definition(metric: str) -> str:
    """The effectiveness definition refers to 'your cogency judgment', which the model
    never makes in a single-metric call."""
    t = PROTOCOL[metric]["full"]
    if metric == "effectiveness":
        t = _replace_exact(t,
            "Cogency may contribute to rhetorical effectiveness, but do not simply repeat "
            "your cogency judgment. ", "")
    return t

def adapted_unusual() -> str:
    t = PROTOCOL["unusual_responses"]
    t = _replace_exact(t,
        " At the bottom of every annotation screen there are optional checkboxes labeled "
        "A: Nonargumentative, B: Nonargumentative, A: Unreadable / truncated, and B: Unreadable / "
        "truncated. Check Nonargumentative only when that response clearly provides no supporting "
        "reason or argumentative contribution. Check Unreadable / truncated only when the text "
        "itself cannot reasonably be evaluated. A flag does not replace the annotation: make the "
        "requested judgments as best you can.",
        " Make the requested judgment as best you can.")
    return t

ADAPTATIONS = [
    ("Overview", "\"You will make three judgments in this order: ...\"",
     "\"You will make one judgment: <metric>.\"",
     "Supervisor requirement: one metric per API call."),
    ("Overview", "\"Do not search the web, use AI assistants, look up the users,\"",
     "\"Do not search the web, look up the users,\"",
     "Instruction addressed to humans; meaningless for the model itself."),
    ("Overview", "\"Judge each displayed pair on its own. Do not revisit an earlier answer ...\"",
     "\"Judge the displayed pair on its own.\"",
     "Each call contains a single pair; there are no earlier answers to revisit."),
    ("Scale introduction",
     "\"For Cogency and Expected Rhetorical Effectiveness, choose exactly one ... The same "
     "four-way scale appears for Evidential Support only when both responses are marked ...\"",
     "Cogency/effectiveness: \"Choose exactly one ...\"; evidence: \"If both responses "
     "provide evidence, choose exactly one ...\"",
     "Each prompt names only the metric being judged."),
    ("Effectiveness definition",
     "\"Cogency may contribute to rhetorical effectiveness, but do not simply repeat your "
     "cogency judgment.\"",
     "(removed)",
     "The model makes no cogency judgment in an effectiveness call; the sentence would "
     "refer to something that does not exist."),
    ("Non-argumentative responses", "Paragraph describing the four optional UI checkboxes",
     "\"Make the requested judgment as best you can.\"",
     "Checkboxes are a UI element not collected from the model; the decision rule "
     "(still judge the pair) is kept."),
    ("Worked examples", "All four examples shown once before annotating",
     "Only the example(s) for the metric being judged",
     "Each call defines only one metric; examples for other metrics would illustrate "
     "criteria the model is not applying. Switch with --examples all."),
    ("Worked examples heading", "\"Worked examples\"",
     "\"Worked examples\" (unchanged; no added preamble)", "Matches the instructions page."),
    ("Answer format", "Clicking a slider / checkbox",
     "JSON with a one-sentence reasoning field written before the label",
     "Supervisor requirement: one sentence of reasoning; machine-checkable output. The "
     "instruction is identical for all metrics and adds no judging criteria."),
]


# ---------------------------------------------------------------------------
# 2. Text rendering: show the model what the annotator saw
# ---------------------------------------------------------------------------
_MD_LINK = re.compile(r'\[([^\]\n]+)\]\(\s*(\S+?)(?:\s+"[^)]*")?\s*\)')

def _short_url(u: str) -> str:
    m = re.match(r'(?:https?://)?(?:www\.)?([^/\s]+)', u)
    return m.group(1) if m else u

def render_plain(src) -> str:
    """Plain-text equivalent of the annotation UI's render_text():
    HTML entities unescaped, line endings normalised, 3+ blank lines collapsed,
    markdown links shown as 'anchor text [domain]' exactly as annotators saw them."""
    s = html.unescape(str(src or "")).replace("\r\n", "\n").replace("\r", "\n")
    s = _MD_LINK.sub(lambda m: f"{m.group(1)} [{_short_url(m.group(2))}]", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s or "(empty)"


# ---------------------------------------------------------------------------
# 3. Prompt templates
# ---------------------------------------------------------------------------
# Reasoning instruction, in the supervisor's exact wording. It adds no judging criteria of
# its own, so every statement about HOW to judge comes verbatim from the human protocol.
_COT = ("Before answering, give one sentence of reasoning about the pair, applying the "
        "instructions and definition above, and write that reasoning in the \"reasoning\" field.")
COT = {m: _COT for m in ("cogency", "effectiveness", "evidence")}

def _examples_block(metric: str, mode: str) -> str:
    idx = EXAMPLE_INDEX[metric] if mode == "metric" else range(len(PROTOCOL["examples"]))
    out = []
    for i in idx:
        ex = PROTOCOL["examples"][i]
        out.append(f"### {ex['title']}\n"
                   f"Original post: {ex['post']}\n\n"
                   f"Response A: {ex['a']}\n\n"
                   f"Response B: {ex['b']}\n\n"
                   f"Illustration: {ex['lesson']}")
    return "\n\n".join(out)

def system_prompt(metric: str, examples: str = "metric") -> str:
    q = PROTOCOL[metric]
    scale = "\n".join(f"- {k}: {v}" for k, v in PROTOCOL["scale"].items())
    if metric == "evidence":
        decision = (f"First: {q['presence_question']}\n"
                    f"If both are checked: {q['comparison_question']}")
        answer = (
            "Respond with a JSON object with these fields, in this order:\n"
            "- \"reasoning\": your single-sentence reasoning.\n"
            f"- \"evidence_present\": the boxes you check: a list containing \"{EV_A}\" "
            f"and/or \"{EV_B}\", or an empty list if you check neither.\n"
            "- \"choice\": if both are checked, exactly one of \"Strong A\", \"Weak A\", "
            "\"Weak B\", \"Strong B\"; otherwise null."
        )
    else:
        decision = f"Decision question: {q['question']}"
        answer = (
            "Respond with a JSON object with these fields, in this order:\n"
            "- \"reasoning\": your single-sentence reasoning.\n"
            "- \"choice\": exactly one of \"Strong A\", \"Weak A\", \"Weak B\", \"Strong B\"."
        )
    return "\n\n".join([
        "## OVERVIEW\n" + adapted_overview(metric),
        "## FOUR-WAY COMPARATIVE SCALE\n" + adapted_scale_intro(metric) + "\n" + scale,
        f"## {q['title']}\n{adapted_definition(metric)}\n\n{decision}",
        "## RESPONSES THAT ARE NOT CLEAR ARGUMENTS\n" + adapted_unusual(),
        "## Worked examples\n" + _examples_block(metric, examples),
        "## HOW TO ANSWER\n" + COT[metric] + "\n\n" + answer,
    ])

def user_prompt(metric: str, op_title: str, op_text: str, text_a: str, text_b: str) -> str:
    """The per-pair annotation screen: post, both responses, then the question box(es)
    with the same title, reminder, question, scale line and answer options."""
    q = PROTOCOL[metric]
    options = "\n".join(CHOICES)
    parts = [
        "THE ORIGINAL POST\n" + f"{render_plain(op_title)}\n\n{render_plain(op_text)}",
        "RESPONSE A\n" + render_plain(text_a),
        "RESPONSE B\n" + render_plain(text_b),
    ]
    if metric == "evidence":
        parts.append(f"{q['title']}\n{q['short']}\n{q['presence_question']}\n{EV_A}\n{EV_B}")
        parts.append(f"If both are checked:\n{EVIDENCE_COMPARE_TITLE}\n{EVIDENCE_COMPARE_REMINDER}\n"
                     f"{q['comparison_question']}\n{SCALE_UI_TEXT}\n{options}")
    else:
        parts.append(f"{q['title']}\n{q['short']}\n{q['question']}\n{SCALE_UI_TEXT}\n{options}")
    return "\n\n---\n\n".join(parts)

def anthropic_schema(metric: str) -> dict:
    """Same schema, with nullable enums written as anyOf. Anthropic rejects an enum under
    a type list such as ["string", "null"]; anyOf[string enum, null] accepts exactly the
    same answers."""
    import copy
    sch = copy.deepcopy(response_schema(metric)["schema"])
    for name, prop in sch["properties"].items():
        if isinstance(prop.get("type"), list) and "enum" in prop:
            values = [v for v in prop["enum"] if v is not None]
            types = [t for t in prop["type"] if t != "null"]
            alts = [{"type": types[0], "enum": values}]
            if "null" in prop["type"]:
                alts.append({"type": "null"})
            sch["properties"][name] = {"anyOf": alts}
    return sch

def response_schema(metric: str) -> dict:
    props = {"reasoning": {"type": "string"}}
    if metric == "evidence":
        props["evidence_present"] = {"type": "array",
                                     "items": {"type": "string", "enum": [EV_A, EV_B]}}
        props["choice"] = {"type": ["string", "null"], "enum": CHOICES + [None]}
    else:
        props["choice"] = {"type": "string", "enum": CHOICES}
    return {"name": f"cmv_{metric}_judgment", "strict": True,
            "schema": {"type": "object", "properties": props,
                       "required": list(props), "additionalProperties": False}}


# ---------------------------------------------------------------------------
# 4. Loading the annotation sample and building the pair set
# ---------------------------------------------------------------------------
def load_sample(path: str):
    import pandas as pd
    raw = pd.read_csv(path, dtype={"post_id": str, "response_id": str}, encoding="utf-8-sig")
    need = ["post_id", "response_id", "op_title", "op_text_clean", "response_text_clean"]
    missing = [c for c in need if c not in raw.columns]
    assert not missing, f"Missing columns: {missing}"
    # Behavioural outcomes are dropped here, exactly as in the human notebook.
    keep = need + (["sample_post_order"] if "sample_post_order" in raw.columns else [])
    data = raw[keep].copy()
    for c in ("op_title", "op_text_clean", "response_text_clean"):
        data[c] = data[c].fillna("").astype(str)
    if "sample_post_order" not in data.columns:
        order = {p: i for i, p in enumerate(data["post_id"].drop_duplicates())}
        data["sample_post_order"] = data["post_id"].map(order)
    assert not data.duplicated(["post_id", "response_id"]).any()
    assert (data.groupby("post_id").size() == 6).all(), "Every OP must have 6 responses."
    blob = "\n".join(data["op_text_clean"].tolist() + data["response_text_clean"].tolist())
    bad = {t: blob.count(t) for t in ("�", "â€™", "â€œ", "Ã©") if t in blob}
    if bad:
        print(f"WARNING: encoding damage in input text: {bad}", file=sys.stderr)
    return data

def build_pairs(data, calibration_only=False, main_only=False):
    """All 15 unordered pairs per OP. pair_key matches the human CSVs: post|lo|hi,
    where lo<hi are the response ids sorted as in the notebook (by response_id)."""
    posts = (data[["post_id", "sample_post_order"]].drop_duplicates()
             .sort_values(["sample_post_order", "post_id"])["post_id"].tolist())
    if calibration_only:
        posts = posts[:5]       # 5 calibration OPs -> 75 pairs
    elif main_only:
        posts = posts[5:]       # 115 main-round OPs -> 1,725 pairs
    out = []
    for pid in posts:
        g = data[data.post_id == pid].sort_values("response_id")
        for lo, hi in itertools.combinations(g.response_id.tolist(), 2):
            out.append({"post_id": pid, "lo": lo, "hi": hi, "pair_key": f"{pid}|{lo}|{hi}"})
    return out, posts


# ---------------------------------------------------------------------------
# 5. Batch request lines
# ---------------------------------------------------------------------------
# Anthropic requires custom_id to match ^[a-zA-Z0-9_-]{1,64}$ (OpenAI accepts it too), so ids
# are hyphen-separated. Reddit post/comment ids are base-36 and contain no hyphens.
_ID_OK = re.compile(r"^[A-Za-z0-9]+$")
_CID_OK = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

def custom_id(metric, pair_key, orient, run):
    post_id, lo, hi = pair_key.split("|")
    for x in (post_id, lo, hi):
        assert _ID_OK.match(x), f"id {x!r} is not alphanumeric; custom_id scheme needs updating"
    cid = f"{metric}-{post_id}-{lo}-{hi}-{orient}-r{run}"
    assert _CID_OK.match(cid), f"custom_id too long or invalid: {cid}"
    return cid

def parse_custom_id(cid):
    metric, post_id, lo, hi, orient, run = cid.split("-")
    return dict(metric=metric, pair_key=f"{post_id}|{lo}|{hi}", post_id=post_id, lo=lo, hi=hi,
                orient=orient, run=int(run[1:]))

def request_line(provider, model, metric, sys_txt, usr_txt, cid, reasoning_effort=None,
                 max_tokens=None, thinking=None):
    if provider == "anthropic":
        # Message Batches API: {"custom_id", "params"} per request.
        params = {
            "model": model,
            "max_tokens": max_tokens or 1024,
            "system": sys_txt,
            "messages": [{"role": "user", "content": usr_txt}],
            "output_config": {"format": {"type": "json_schema",
                                         "schema": anthropic_schema(metric)}},
        }
        if reasoning_effort:
            params["output_config"]["effort"] = reasoning_effort
        if thinking:
            params["thinking"] = {"type": thinking}
        return {"custom_id": cid, "params": params}
    max_completion_tokens = max_tokens
    body = {
        "model": model,
        "messages": [{"role": "system", "content": sys_txt},
                     {"role": "user", "content": usr_txt}],
        "response_format": {"type": "json_schema", "json_schema": response_schema(metric)},
    }
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    if max_completion_tokens:
        body["max_completion_tokens"] = max_completion_tokens
    return {"custom_id": cid, "method": "POST", "url": "/v1/chat/completions", "body": body}

def cmd_build(a):
    data = load_sample(a.input)
    assert not (a.calibration_only and a.main_only), "choose one subset"
    pairs, posts = build_pairs(data, a.calibration_only, a.main_only)
    text = dict(zip(data.response_id, data.response_text_clean))
    op = {p: (g.op_title.iloc[0], g.op_text_clean.iloc[0]) for p, g in data.groupby("post_id")}
    sys_by_metric = {m: system_prompt(m, a.examples) for m in METRICS}
    orients = ["AB", "BA"] if a.orientations == "both" else ["AB"]
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    lines = []
    for m in METRICS:  # grouped by metric so the shared system prefix is cached
        for p in pairs:
            for o in orients:
                ra, rb = (p["lo"], p["hi"]) if o == "AB" else (p["hi"], p["lo"])
                usr = user_prompt(m, *op[p["post_id"]], text[ra], text[rb])
                for r in range(1, a.runs + 1):
                    lines.append(request_line(a.provider, a.model, m, sys_by_metric[m], usr,
                                              custom_id(m, p["pair_key"], o, r),
                                              a.reasoning_effort, a.max_tokens, a.thinking))
    assert len({l["custom_id"] for l in lines}) == len(lines)

    # OpenAI: 50,000 requests / 200 MB per input file. Anthropic: 100,000 / 256 MB per batch,
    # but the whole batch is sent in one HTTP request, so keep each part small.
    max_n, max_bytes = (50_000, 190_000_000) if a.provider == "openai" else (2_500, 40_000_000)
    chunks, cur, size = [], [], 0
    for l in lines:
        s = len(json.dumps(l, ensure_ascii=False).encode()) + 1
        if cur and (len(cur) >= max_n or size + s > max_bytes):
            chunks.append(cur); cur, size = [], 0
        cur.append(l); size += s
    chunks.append(cur)
    tag = "calibration" if a.calibration_only else "main" if a.main_only else "full"
    files = []
    for i, ch in enumerate(chunks, 1):
        f = out / f"batch_{tag}_{a.model}_part{i:02d}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for l in ch:
                fh.write(json.dumps(l, ensure_ascii=False) + "\n")
        files.append(f)

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
        "provider": a.provider, "model": a.model, "reasoning_effort": a.reasoning_effort,
        "thinking": a.thinking, "max_tokens": a.max_tokens, "examples": a.examples,
        "orientations": orients, "runs": a.runs, "n_posts": len(posts), "n_pairs": len(pairs),
        "n_requests": len(lines), "files": [f.name for f in files],
        "system_prompt_sha256": {m: hashlib.sha256(s.encode()).hexdigest()
                                 for m, s in sys_by_metric.items()},
    }
    (out / f"manifest_{tag}_{a.model}.json").write_text(json.dumps(manifest, indent=2))
    for m, s in sys_by_metric.items():
        (out / f"system_prompt_{m}.txt").write_text(s, encoding="utf-8")
    print(f"{len(posts)} OPs, {len(pairs)} pairs, {len(METRICS)} metrics, "
          f"{len(orients)} orientation(s), {a.runs} run(s) -> {len(lines)} requests")
    for f in files:
        print(f"  {f}")


# ---------------------------------------------------------------------------
# 6. Preview and diff
# ---------------------------------------------------------------------------
def cmd_preview(a):
    data = load_sample(a.input)
    pairs, _ = build_pairs(data)
    p = pairs[a.pair_index]
    text = dict(zip(data.response_id, data.response_text_clean))
    g = data[data.post_id == p["post_id"]].iloc[0]
    doc = [f"# LLM prompt preview — pair {p['pair_key']}\n",
           f"Protocol: `{PROTOCOL_VERSION}`. One request per metric; A = {p['lo']}, B = {p['hi']}.\n"]
    for m in METRICS:
        doc += [f"\n\n## {METRIC_NAME[m]}\n", "### System message\n", "```text",
                system_prompt(m, a.examples), "```", "\n### User message\n", "```text",
                user_prompt(m, g.op_title, g.op_text_clean, text[p["lo"]], text[p["hi"]]), "```",
                "\n### Output schema\n", "```json", json.dumps(response_schema(m), indent=2), "```"]
    Path(a.out).write_text("\n".join(doc), encoding="utf-8")
    print(f"wrote {a.out}")

def cmd_diff(a):
    print("Every change between the human protocol and the LLM prompt:\n")
    for i, (where, human, llm, why) in enumerate(ADAPTATIONS, 1):
        print(f"{i}. [{where}]\n   human: {human}\n   LLM:   {llm}\n   why:   {why}\n")
    print("Additions (not wording changes): the one-sentence reasoning instruction and the "
          "JSON answer format.")


# ---------------------------------------------------------------------------
# 7. Token and cost estimate
# ---------------------------------------------------------------------------
def _counter():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        return (lambda s: len(enc.encode(s))), "tiktoken o200k_base"
    except Exception:
        return (lambda s: max(1, round(len(s) / 4))), "approx (chars/4)"

def cmd_estimate(a):
    count, how = _counter()
    n, tin, sys_tokens = 0, 0, {}
    for path in a.requests:
        for line in open(path, encoding="utf-8"):
            r = json.loads(line); n += 1
            if "params" in r:   # Anthropic
                sys_txt, usr_txt = r["params"]["system"], r["params"]["messages"][0]["content"]
            else:               # OpenAI
                msgs = r["body"]["messages"]
                sys_txt, usr_txt = msgs[0]["content"], msgs[1]["content"]
            st = count(sys_txt)
            sys_tokens[parse_custom_id(r["custom_id"])["metric"]] = st
            tin += st + count(usr_txt) + 12
    tout = n * a.out_tokens
    print(f"Token counter: {how}")
    print(f"Requests: {n:,}   input tokens: {tin:,}   visible output tokens (assumed "
          f"{a.out_tokens}/request): {tout:,}")
    print("System prompt tokens per metric:", sys_tokens)
    print("NOTE: reasoning models also bill hidden reasoning tokens as output; set --out-tokens "
          "from a pilot run's usage.completion_tokens, not from the visible JSON length.")
    if a.pricing:
        print(f"\n{'model':<28}{'input $/1M':>12}{'output $/1M':>13}{'batch cost':>13}")
        for row in csv.DictReader(open(a.pricing)):
            if not row.get("batch_input_per_1m"):
                continue
            cost = tin / 1e6 * float(row["batch_input_per_1m"]) + \
                   tout / 1e6 * float(row["batch_output_per_1m"])
            print(f"{row['model']:<28}{float(row['batch_input_per_1m']):>12.3f}"
                  f"{float(row['batch_output_per_1m']):>13.3f}{cost:>12.2f}$")


# ---------------------------------------------------------------------------
# 8. Validation, canonical output, resubmission
# ---------------------------------------------------------------------------
_CANON = {x.lower(): x for x in CHOICES + [EV_A, EV_B]}

def _norm(x):
    """Anthropic may return enum values with different capitalization; map them back."""
    return _CANON.get(x.lower(), x) if isinstance(x, str) else x

def unpack_result(res):
    """Normalize one result line from either provider.
    Returns (text, usage, model, error_reason). usage uses prompt_/completion_tokens keys."""
    if "result" in res:                                   # Anthropic Message Batches
        r = res["result"] or {}
        if r.get("type") != "succeeded":
            err = (r.get("error") or {}).get("error", {}).get("type") or r.get("type")
            return None, {}, None, f"anthropic_{err}"
        msg = r.get("message") or {}
        stop = msg.get("stop_reason")
        if stop == "refusal":
            return None, {}, None, "refusal"
        if stop != "end_turn":
            return None, {}, None, f"stop_reason_{stop}"
        text = next((b.get("text") for b in msg.get("content", []) if b.get("type") == "text"), None)
        u = msg.get("usage") or {}
        usage = {"prompt_tokens": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                 + (u.get("cache_creation_input_tokens") or 0),
                 "completion_tokens": u.get("output_tokens"),
                 "cached_tokens": u.get("cache_read_input_tokens")}
        return text, usage, msg.get("model"), None
    # OpenAI Batch (chat completions)
    if res.get("error"):
        return None, {}, None, f"api_error: {res['error']}"
    resp = res.get("response") or {}
    if resp.get("status_code") != 200:
        return None, {}, None, f"http_{resp.get('status_code')}"
    body = resp.get("body") or {}
    try:
        choice = body["choices"][0]
    except (KeyError, IndexError, TypeError):
        return None, {}, None, "no_choices"
    msg = choice.get("message", {})
    if msg.get("refusal"):
        return None, {}, None, "refusal"
    if choice.get("finish_reason") != "stop":
        return None, {}, None, f"finish_reason_{choice.get('finish_reason')}"
    u = body.get("usage") or {}
    usage = {"prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
             "cached_tokens": (u.get("prompt_tokens_details") or {}).get("cached_tokens")}
    return msg.get("content"), usage, body.get("model"), None

def check_result(metric, res):
    """Return (parsed_dict, usage, model, None) if valid, else (None, None, None, reason)."""
    text, usage, model, err = unpack_result(res)
    if err:
        return None, None, None, err
    try:
        out = json.loads(text or "")
    except json.JSONDecodeError:
        return None, None, None, "bad_json"
    if not isinstance(out, dict):
        return None, None, None, "bad_json"
    if not isinstance(out.get("reasoning"), str) or not out["reasoning"].strip():
        return None, None, None, "empty_reasoning"
    out["choice"] = _norm(out.get("choice"))
    if metric == "evidence":
        checked = out.get("evidence_present")
        if not isinstance(checked, list):
            return None, None, None, "bad_presence"
        checked = [_norm(x) for x in checked]
        if any(x not in (EV_A, EV_B) for x in checked):
            return None, None, None, "bad_presence"
        a, b, c = EV_A in checked, EV_B in checked, out.get("choice")
        if (a and b) and c not in CHOICES:
            return None, None, None, "missing_comparison"
        if not (a and b) and c is not None:
            return None, None, None, "comparison_without_both"
        out["evidence_a_present"], out["evidence_b_present"] = a, b
    elif out.get("choice") not in CHOICES:
        return None, None, None, "bad_choice"
    return out, usage, model, None

def to_record(cid, out, usage, model):
    """One row in the same column convention as the human CSVs.
    A/B are as displayed to the model; *_canon fields are re-expressed with A = lo id."""
    k = parse_custom_id(cid)
    ra, rb = (k["lo"], k["hi"]) if k["orient"] == "AB" else (k["hi"], k["lo"])
    p = HUMAN_PREFIX[k["metric"]]
    rec = {"custom_id": cid, "model": model, "metric": k["metric"], "pair_key": k["pair_key"],
           "post_id": k["post_id"], "orientation": k["orient"], "run": k["run"],
           "response_id_a": ra, "response_id_b": rb, "reasoning": out["reasoning"],
           "prompt_tokens": usage.get("prompt_tokens"),
           "completion_tokens": usage.get("completion_tokens"),
           "cached_tokens": usage.get("cached_tokens")}
    if k["metric"] == "evidence":
        a, b = out["evidence_a_present"], out["evidence_b_present"]
        rec["evidence_a_present"], rec["evidence_b_present"] = a, b
        rec["evidence_presence_pattern"] = ("both" if a and b else "A_only" if a
                                            else "B_only" if b else "neither")
        # canonical presence: lo / hi
        lo_p, hi_p = (a, b) if k["orient"] == "AB" else (b, a)
        rec["evidence_lo_present"], rec["evidence_hi_present"] = lo_p, hi_p
    c = out.get("choice")
    if c in CHOICES:
        rec[f"{p}_choice"] = c
        rec[f"{p}_winner_response_id"] = ra if c.endswith("A") else rb
        rec[f"{p}_margin"] = MARGIN[c]
        rec[f"{p}_signed"] = SIGNED[c]
        canon = c if k["orient"] == "AB" else FLIP[c]
        rec[f"{p}_choice_canon"] = canon
        rec[f"{p}_signed_canon"] = SIGNED[canon]   # negative = lo id preferred
    return rec

def cmd_validate(a):
    reqs = {}
    for path in a.requests:
        for line in open(path, encoding="utf-8"):
            r = json.loads(line); reqs[r["custom_id"]] = r
    seen, good, faulty = set(), {}, {}
    for path in a.results:  # later result files override earlier ones (resubmissions)
        for line in open(path, encoding="utf-8"):
            res = json.loads(line); cid = res["custom_id"]; seen.add(cid)
            metric = parse_custom_id(cid)["metric"]
            out, usage, model, why = check_result(metric, res)
            if out is not None:
                good[cid] = to_record(cid, out, usage, model)
                faulty.pop(cid, None)
            elif cid not in good:
                faulty[cid] = why
    for cid in reqs:
        if cid not in seen and cid not in good:
            faulty[cid] = "missing_from_results"

    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    df = pd.DataFrame(list(good.values()))
    for m in METRICS:
        sub = df[df.metric == m].dropna(axis=1, how="all").copy() if len(df) else df
        for c in sub.columns:
            if c.endswith(("_margin", "_signed", "_signed_canon", "_tokens")):
                sub[c] = sub[c].astype("Int64")
        sub.to_csv(od / f"llm_annotations_{m}.csv", index=False, encoding="utf-8-sig")
    with (od / "faulty_report.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["custom_id", "reason"])
        w.writerows(sorted(faulty.items()))
    if faulty:
        rnd = a.round
        f = od / f"resubmit_round{rnd:02d}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for cid in sorted(faulty):
                fh.write(json.dumps(reqs[cid], ensure_ascii=False) + "\n")
        print(f"{len(good):,} valid, {len(faulty):,} faulty -> resubmit {f}")
        from collections import Counter
        for why, n in Counter(faulty.values()).most_common():
            print(f"   {n:>6}  {why}")
    else:
        print(f"All {len(good):,} requests valid. Annotation CSVs in {od}")


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("--input", required=True); b.add_argument("--model", required=True)
    b.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    b.add_argument("--thinking", default=None,
                   help="Anthropic only: thinking type, e.g. between_tools (no up-front thinking)")
    b.add_argument("--out-dir", default="batch_input")
    b.add_argument("--orientations", choices=["both", "ab"], default="both")
    b.add_argument("--runs", type=int, default=1)
    b.add_argument("--examples", choices=["metric", "all"], default="metric")
    b.add_argument("--reasoning-effort", default=None,
                   help="OpenAI: reasoning_effort. Anthropic: output_config.effort. e.g. low")
    b.add_argument("--max-tokens", "--max-completion-tokens", dest="max_tokens", type=int,
                   default=None, help="output token cap (includes any hidden reasoning)")
    b.add_argument("--calibration-only", action="store_true",
                   help="only the 5 calibration OPs: 75 pairs (pilot run)")
    b.add_argument("--main-only", action="store_true",
                   help="only the 115 main-round OPs: 1,725 pairs (run after the pilot)")
    p = sp.add_parser("preview")
    p.add_argument("--input", required=True); p.add_argument("--pair-index", type=int, default=0)
    p.add_argument("--examples", choices=["metric", "all"], default="metric")
    p.add_argument("--out", default="prompt_preview.md")
    sp.add_parser("diff")
    e = sp.add_parser("estimate")
    e.add_argument("--requests", nargs="+", required=True)
    e.add_argument("--pricing"); e.add_argument("--out-tokens", type=int, default=300)
    v = sp.add_parser("validate")
    v.add_argument("--requests", nargs="+", required=True)
    v.add_argument("--results", nargs="+", required=True)
    v.add_argument("--out-dir", default="llm_output"); v.add_argument("--round", type=int, default=1)
    a = ap.parse_args(argv)
    {"build": cmd_build, "preview": cmd_preview, "diff": cmd_diff,
     "estimate": cmd_estimate, "validate": cmd_validate}[a.cmd](a)

if __name__ == "__main__":
    main()
