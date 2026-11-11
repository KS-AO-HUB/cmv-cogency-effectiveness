# LLM annotation

| File | What it is |
|---|---|
| `run_llm_batches.ipynb` | Builds, estimates, smoke-tests, submits, downloads, validates and resubmits both models' batches. Sections 5–8 call the APIs and cost money |
| `cmv_llm_batch.py` | Prompt builder, batch-file builder, validator and cost estimator used by the notebook |
| `annotation_protocol_cmv_annotation_v4_2026_09_24.json` | The human protocol, extracted verbatim from the annotation notebook. Do not edit; the prompt builder reads it and records its SHA-256 |
| `audit_prompts.py` → `PROMPT_AUDIT.md` | Sentence-by-sentence check of the prompts against the human instructions |
| `prompt_preview.md`, `system_prompt_*.txt` | The exact prompts |
| `PROMPT_DESIGN.md` | Rationale, every wording change from the human instructions, known differences between the human and LLM conditions |
| `runs/{claude,gpt}/manifest_*.json` | Settings, counts and hashes of the submitted batch files |
| `runs/{claude,gpt}/results/` | Raw batch API responses |
| `runs/{claude,gpt}/llm_output/` | Parsed labels used by the analysis |
| `runs/state.json` | Batch IDs and submission times |

## Models

| | Claude Sonnet 5.5 (primary) | GPT-6.1 Sol (robustness) |
|---|---|---|
| API model ID | `claude-sonnet-5-5` | `gpt-6.1-sol` |
| Lowest reasoning setting used | `effort="low"`, `thinking={"type":"between_tools"}` (no up-front thinking) | `reasoning_effort="low"` (lowest accepted) |
| Batch API | Anthropic Message Batches | OpenAI Batch, `/v1/chat/completions` |
| Max output tokens | 1,024 | 4,000 |

Each model received 1,725 main-round pairs × 3 questions × 2 A/B orders = 10,350 requests; all responses were valid on the first submission.

## Checking the run without API calls

Run from the repository root:

```bash
# Rebuild the batch request files (byte-identical to the submitted ones; see the manifests)
python llm_annotation/cmv_llm_batch.py build --input data/annotation_input.csv --provider anthropic \
    --model claude-sonnet-5-5 --reasoning-effort low --max-tokens 1024 --thinking between_tools \
    --out-dir llm_annotation/runs/claude/batch_input --main-only
python llm_annotation/cmv_llm_batch.py build --input data/annotation_input.csv --provider openai \
    --model gpt-6.1-sol --reasoning-effort low --max-tokens 4000 \
    --out-dir llm_annotation/runs/gpt/batch_input --main-only

# Re-parse the raw responses into the label files (byte-identical to runs/*/llm_output/)
python llm_annotation/cmv_llm_batch.py validate --requests llm_annotation/runs/claude/batch_input/*.jsonl \
    --results llm_annotation/runs/claude/results/*.jsonl --out-dir /tmp/claude_check --round 1
```

## Output format

`llm_annotations_{cogency,effectiveness,evidence}.csv` contain one row per request, using the human files' column names (`cogency_choice`, `effect_signed`, `evidence_a_present`, …) plus:

- `pair_key` (`post|lo|hi`, identical to the human files) and `orientation` (`AB` = lo shown as A, `BA` = swapped)
- `*_choice_canon`, `*_signed_canon`: the label restated with A = the lower response ID, so both orders, both models and all humans compare on one scale
- `reasoning` (one sentence), token usage, and the model that answered

Request IDs look like `cogency-1dzqaz-c9abc12-c9xyz34-AB-r1` (metric, post, the two response IDs, orientation, run).
