# LLM Annotation Prompts — Design and Rationale

Protocol: `cmv_annotation_v4_2026_09_24` (the version the human annotators used)
Models: GPT-6.1 Sol (OpenAI, `gpt-6.1-sol`) and Claude Sonnet 5.5 (Anthropic, `claude-sonnet-5-5`), each at its lowest reasoning setting, via each provider's batch API with structured outputs

---

## 1. Summary

The model receives **the same instructions, the same worked examples, the same four labels, and the same rendered text** that the human annotators saw, loaded programmatically from the protocol file the annotation notebook displayed; the only wording changes are the mechanical edits forced by the one-metric-per-call design, each listed below. No prompt mentions any metric other than the one being judged; `audit_prompts.py` fails if one does.

## 2. Requirements and how each is met

| Requirement | Implementation |
|---|---|
| Two models, lowest reasoning | GPT-6.1 Sol: `reasoning_effort="low"`, the lowest it accepts (`none`/`minimal` are not supported), via the OpenAI Batch API on `/v1/chat/completions`. Claude Sonnet 5.5: `output_config.effort="low"` with `thinking={"type":"between_tools"}`, which turns off up-front thinking (this model rejects `"disabled"`), via the Message Batches API. Both get identical system and user messages. Settings are recorded in each batch manifest |
| Prompts match human instructions: exact definitions, examples, labels | All guidance text is read from `annotation_protocol_cmv_annotation_v4_2026_09_24.json`, extracted directly from the notebook's `PROTOCOL` dict. Its SHA-256 is written to every batch manifest. Labels are enforced by a JSON-schema enum: `Strong A`, `Weak A`, `Weak B`, `Strong B` |
| One metric per call | Three system prompts (cogency, effectiveness, evidence); each request carries exactly one |
| One A/B pair + its OP per call | User message = the per-pair annotation screen: OP title + text, Response A, Response B, then the metric's question box exactly as displayed (title, reminder, question, scale line, answer options; for evidence, the two checkbox labels and the "EVIDENTIAL SUPPORT — COMPARISON" box) |
| One sentence of reasoning | The supervisor's wording, identical in all three prompts: "Before answering, give one sentence of reasoning about the pair, applying the instructions and definition above, and write that reasoning in the "reasoning" field." The schema puts `reasoning` **before** the answer fields, so it is written first. It adds no judging criteria of its own |
| Batching | `CMV_LLM_Batch_Runner.ipynb` builds, submits, downloads and validates both batches. OpenAI files split at 50,000 requests / 200 MB; Anthropic batches at 2,500 requests, since each is uploaded in one HTTP request. Request IDs use only letters, digits and hyphens, as Anthropic requires |
| Token and cost estimate | Notebook section 4 (both models: $1 input / $5 output per 1M tokens at batch prices); section 5 measures real output tokens on 6 live requests per model |
| Re-submit faulty rows until clean | `validate` writes clean CSVs plus `resubmit_roundNN.jsonl` containing only failed requests, byte-identical to the originals; repeat until it reports zero faulty |

## 3. Every wording change (run `python cmv_llm_batch.py diff`)

| # | Where | Human version | LLM version | Why |
|---|---|---|---|---|
| 1 | Overview | "You will make three judgments in this order: Cogency, …" | "You will make one judgment: *metric*." | One metric per call |
| 2 | Overview | "Do not search the web, use AI assistants, look up the users …" | "… search the web, look up the users …" | Instruction addressed to humans |
| 3 | Overview | "Judge each displayed pair on its own. Do not revisit an earlier answer …" | "Judge the displayed pair on its own." | One pair per call; nothing to revisit |
| 4 | Scale introduction | "For Cogency and Expected Rhetorical Effectiveness, choose exactly one … The same four-way scale appears for Evidential Support only when …" | Cogency and effectiveness: "Choose exactly one …". Evidence: "If both responses provide evidence, choose exactly one …" | Each prompt names only the metric being judged |
| 5 | Effectiveness definition | "Cogency may contribute to rhetorical effectiveness, but do not simply repeat your cogency judgment." | Removed | The model makes no cogency judgment in an effectiveness call |
| 6 | Non-argumentative responses | Paragraph describing the four optional UI checkboxes | "Make the requested judgment as best you can." | Checkboxes are a UI element; the decision rule is kept |
| 7 | Worked examples | All four shown before annotating | Only the metric's own examples (1 → cogency, 2 → effectiveness, 3 and 4 → evidence) | Each call defines one metric. Switchable with `--examples all` |
| 8 | Answer format | Slider / checkboxes | JSON: one sentence of reasoning, then the answer | Supervisor's reasoning requirement; machine-checkable |

`python audit_prompts.py` checks this sentence by sentence and writes `PROMPT_AUDIT.md`: every notebook sentence not used verbatim, and every prompt line that is not annotation text. The only added text is the HOW TO ANSWER block: the supervisor's one-sentence reasoning instruction and the JSON answer format. There is no role statement, and no examples preamble; the main-round app showed only the heading "Worked examples".

**Why the reasoning instruction is generic.** An earlier draft gave each metric its own reasoning steps, paraphrased from the definitions. Paraphrase can shift emphasis. For example, "assess how each response engages with the OP's concerns" would have steered the model toward one cue, while annotators were told that credibility, emotional appeal, clarity and "other aspects" may matter. So the reasoning instruction says only *how to answer* (one sentence of reasoning, then the label), never *what to look for*. The supervisor then shortened it from step-by-step reasoning to a single sentence, which keeps every label auditable at a fraction of the output tokens.

Everything else is verbatim: the rest of the scale introduction and the four label definitions, each construct's full definition (apart from edit 5) and decision question, the short on-screen reminder, the "No ties … use Weak" line shown under every scale, and the evidence-comparison reminder.

## 4. Design decisions

**Why does the model see links as "anchor text [domain]" instead of full URLs?** Because that is what annotators saw: the annotation UI rendered `[text](url)` as the anchor plus the domain, unescaped HTML entities, and collapsed blank lines. `render_plain()` reproduces that transformation, so both judges read the same text. Neither could open links.

**Why send every pair twice, with A and B swapped?** LLMs show position bias in pairwise judgments. Scoring both orientations (a) lets us measure that bias directly, (b) supplies the LLM reliability estimate the proposal specifies (orientation-flip disagreement, Section "Reliability and Disattenuation"), and (c) mirrors the human design, where A/B orientation was randomised per annotator. Outputs carry both the displayed-orientation label and a canonical label (A = lower response ID) so the two runs can be compared and averaged.

**Why one run per orientation rather than three repeated runs?** The proposal itself argues that repeated runs under fixed decoding overstate reliability, and names orientation flip as the preferred estimate. `--runs 3` is available if time allows.

**Is the visible reasoning the model's "real" reasoning?** No, and we don't claim so. It is a one-sentence stated rationale that makes every label auditable and gives qualitative examples for the results chapter. GPT-6.1 Sol also reasons internally even at `low` effort; that hidden reasoning is billed as output but not returned. Claude Sonnet 5.5 with `between_tools` does no up-front thinking. The two models therefore differ in how much hidden reasoning precedes the label, which belongs in Limitations.

**Why Structured Outputs?** The schema restricts answers to the exact human labels: `choice` to "Strong A", "Weak A", "Weak B", "Strong B", and the evidence checkboxes to "Response A provides evidence" and "Response B provides evidence". There is no free-text parsing and no invented label. For evidence, the validator also enforces the human rule that a comparison exists only when both boxes are checked; otherwise `choice` is null, just as the human comparison box never appeared.

**Why no tie option?** The human protocol has none ("No ties: if they seem nearly equal, choose the side you lean toward and use Weak"). Matching that is the point.

**Could the model know the outcome?** The prompt contains only sanitised post and response text; delta, reply, and score columns are dropped on load, as in the human notebook. The model may still have seen 2013–2018 CMV threads in training. That is a stated limitation; the post-cutoff replication in the proposal is the proper test and is deferred.

## 5. Known differences between the human and LLM conditions

1. **Order and carry-over.** Humans judged cogency, then effectiveness, then evidence on one screen, in fixed order (`task_order = cogency_first`). The model judges each metric in isolation. The human effectiveness judgment may therefore be anchored on the cogency judgment just made; the model's cannot be. For the same reason, the definition's warning "do not simply repeat your cogency judgment" was removed from the model's prompt (edit 5): humans needed it, but the model has no cogency judgment to repeat. If humans show tighter cogency–effectiveness coupling than the model, this asymmetry is one explanation.
2. **Context across pairs.** Humans saw all 15 pairs from an OP consecutively and built familiarity with its responses; each model call is independent.
3. **Response flags.** Humans could flag responses as nonargumentative or unreadable; the model does not. Those human flags can still be used to stratify the comparison.
4. **Examples.** Humans read all four examples up front; the model sees only its metric's examples (unless `--examples all`).
5. **Two models, one prompt.** GPT-6.1 Sol and Claude Sonnet 5.5 come from different families, which tests whether results hold across providers, but both use one prompt per metric. They also differ in hidden reasoning (see section 4). Results are a property of these models and this prompt, not of "LLMs".

## 6. Protocol as run

The prompts follow the annotation notebook, that is, what the annotators actually did:

- **No ties.** Forced choice with a Strong/Weak margin; there is no tie option.
- **Construct assignment.** Each annotator judged all three metrics on every pair, in a fixed order.
- **Evidential Support** was collected as a third metric; it is not analyzed in the thesis.
- **Cogency reference audience.** The prompts quote the annotator definition exactly.

## 7. Run order (`run_llm_batches.ipynb`)

1. Build both models' batches for the 1,725 main-round pairs: 1,725 × 3 metrics × 2 orientations = 10,350 requests per model.
2. Cost estimate, then the smoke test: 6 live requests per model, checked by the validator, measuring real output tokens.
3. Submit, download, then validate → resubmit → validate until both models have zero faulty rows.

## 8. Analyses this output supports

Report per metric, against each human annotator and against the human majority:

- **Direction agreement:** % of pairs where the model picks the same winner.
- **Nuance agreement:** weighted κ on the four-point signed scale (−2, −1, +1, +2), plus the Strong/Weak mix; does the model overuse "Strong"?
- **Human ceiling:** the same statistics between pairs of humans. LLM–human agreement means little unless placed next to human–human agreement on the same pairs.
- **Position bias:** % of pairs where the AB and BA runs disagree in direction.
- **Evidence presence:** agreement on the present/absent decision separately from the comparison.
