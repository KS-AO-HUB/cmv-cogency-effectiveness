# Data dictionary

All IDs are Reddit base-36 IDs. A `pair_key` is `post_id|lo|hi`, where `lo` and `hi` are the pair's two response IDs in lexicographic order.

## `annotation_input.csv`

One row per sampled reply (120 posts × 6 replies = 720 rows).

| Column | Meaning |
|---|---|
| `sample_post_order`, `sample_response_order` | Fixed order of the sample. The first five posts by `sample_post_order` are the calibration set |
| `post_id`, `response_id` | Reddit IDs |
| `op_title`, `op_text_clean` | The original post, as shown to annotators and models |
| `response_text_clean` | The reply, as shown |

## `human/calibration_H*.csv` and `human/main_H*.csv`

One row per pair judged by one annotator.

| Column | Meaning |
|---|---|
| `pair_key`, `post_id`, `pair_in_post` | The pair and its post |
| `annotator_id` | H1, H2 or H3 |
| `instruction_version` | Annotation protocol version (`llm_annotation/annotation_protocol_*.json`) |
| `phase_of_last_edit` | `calibration_initial` or `main_annotation` |
| `sample_post_order` | Position of the post in the sample |
| `response_id_a`, `response_id_b`, `ab_flipped` | Which reply this annotator saw as Response A and as Response B |
| `task_order` | Order of the questions on screen (`cogency_first`) |
| `cogency_choice`, `effect_choice` | Strong A, Weak A, Weak B or Strong B, relative to the A/B order shown |
| `*_winner_response_id` | The reply chosen |
| `*_margin` | 2 = Strong, 1 = Weak |
| `*_signed` | −2, −1, +1, +2 (negative = A preferred), relative to the A/B order shown |
| `evidence_*` | Evidential-support judgment (collected, not analyzed) |
| `a_nonargumentative`, `b_nonargumentative`, `a_unreadable`, `b_unreadable` | Optional flags on each reply |
| `notes` | Optional free-text note |
| `seconds_on_pair_total` | Time spent on the pair |
| `revision_count` | Times the judgment was edited |

`effect` = expected rhetorical effectiveness.

## `../llm_annotation/runs/{claude,gpt}/llm_output/llm_annotations_{cogency,effectiveness,evidence}.csv`

One row per request (1,725 pairs × 2 orders = 3,450 rows per file).

| Column | Meaning |
|---|---|
| `custom_id` | Request ID: metric, post, both response IDs, orientation, run |
| `model`, `metric`, `run` | Model ID, question, run number |
| `pair_key`, `post_id` | The pair |
| `orientation` | `AB` = lower ID shown as Response A, `BA` = swapped |
| `response_id_a`, `response_id_b` | Order shown in this request |
| `reasoning` | The model's one-sentence reasoning |
| `prompt_tokens`, `completion_tokens`, `cached_tokens` | Token usage |
| `*_choice`, `*_winner_response_id`, `*_margin`, `*_signed` | As in the human files |
| `*_choice_canon`, `*_signed_canon` | The label restated with A = the lower response ID |

## `outcomes.csv`

One row per sampled reply (720 rows), written by `sampling/scrape_and_sample.ipynb`.

| Column | Meaning |
|---|---|
| `post_id`, `response_id` | Reddit IDs |
| `op_stratum` | `delta_positive` (post has a delta reply) or `no_delta` |
| `behavior_state`, `behavior_state_star` | D = the OP awarded this reply a delta; R = the OP replied without a delta; N = no OP reply. `_star` is the version used in the analyses |
| `op_reply`, `op_delta` | Whether the OP replied to it, and whether the OP awarded it a delta |
| `response_score`, `community_score_percentile` | Reddit score, and its percentile among the post's eligible direct replies |
| `hours_since_op` | Hours between the post and the reply |
| `response_order` | Position of the reply among the post's direct replies |
| `n_eligible_direct_responses` | Number of eligible direct replies to the post |
| `inclusion_stratum`, `n_available_in_stratum`, `inclusion_prob_within_op` | Sampling stratum of the reply, how many replies were available in it, and the reply's probability of selection within its post |
