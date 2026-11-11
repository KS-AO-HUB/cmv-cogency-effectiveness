# Cogency, Expected Rhetorical Effectiveness, and Persuasion on r/ChangeMyView

**TL;DR:** Can LLMs tell a *well-reasoned* argument from one that is *likely to change this particular person's mind*, and do their judgments track real persuasion? On 115 r/ChangeMyView discussions, Claude agreed with a trained human annotator at least as often as human annotators agreed with each other, yet neither the models nor the humans clearly separated the two qualities, and two models that both "agree with humans" credited persuasion to *different* qualities. Agreement with humans is not enough to validate an LLM measurement.

**What this project involved**

- **Data engineering:** reconstructed which replies changed the poster's view from 123,560 posts and 5.1 million comments (2013–2018), then drew a behavior-stratified sample with a fixed seed.
- **LLM evaluation at scale:** about 20,700 batch requests to two providers (Anthropic and OpenAI), every pair judged in both presentation orders, with prompts audited against the human protocol and byte-identical rebuilds of every request.
- **Human annotation:** a custom notebook interface, a calibration round and three annotators.
- **Statistics:** Bradley–Terry ranking, multitrait–multimethod validity tests, conditional logit models with Holm-adjusted tests, held-out prediction with cross-validation, and post-level bootstrap intervals.
- **Reproducibility:** every table in the thesis regenerates exactly from this repository, with no API calls.

Code and data for an M.S. thesis that tests whether large language models (LLMs) can measure two related qualities of an argument, and whether those measurements relate to persuasion:

- **Cogency:** whether a reply offers acceptable, relevant and sufficient reasons.
- **Expected rhetorical effectiveness:** how likely a reply is to change the original poster's (OP's) stated view, judged from the post alone.

The data are 120 r/ChangeMyView posts (2013–2018), six direct replies each. Human annotators and two LLMs compared every pair of replies within a post on both qualities.

The thesis has three studies:

1. **Correspondence:** a multitrait–multimethod test of whether LLM judgments agree with human judgments and keep the two qualities apart.
2. **Behavior:** associations with acknowledged persuasion (the OP's delta), OP engagement and community score.
3. **Prediction:** whether the measurements improve held-out prediction beyond reply length, timing and position.

## Key findings

Human reference: annotator H1 on all 115 main-round posts (1,725 pairs). Every number below is in `results/tables/` (table name in brackets).

1. **A judge's own uncertainty marks its instability.** Every pair was judged in both A/B orders. 97–100% of each model's order-dependent flips occurred on pairs the model itself labeled "Weak" in both orders, and neither model ever flipped on a pair it labeled "Strong" in both orders (2,987 pairs). [X4]
2. **Model consensus flags where humans are needed, but not every error.** When all four judgments of a pair agreed (two models × two orders; 74–75% of pairs), they matched the human 94% (cogency) and 90% (effectiveness) of the time; when they split 3 to 1, the majority matched only 70% and 68%. But 53% and 64% of the pairs where the model majority disagreed with the human were unanimous, so a consensus filter alone would miss most of those errors. [X5]
3. **Human-level agreement without separating the constructs.** Claude picked the human's winner on 86% (cogency) and 80% (effectiveness) of judgments and GPT on 81% and 82%, while pairs of human annotators agreed on 73–79%. Yet a multitrait–multimethod test did not establish that either model keeps cogency and effectiveness apart: the selective contrasts were not significant after Holm adjustment, and the human and the models coupled the two constructs about equally. [B1, A2, C1]
4. **The choice of judge changes the scientific conclusion.** All three measurements link overall quality to the OP's delta (shared-quality odds ratios 3.03 for the human, 3.00 for Claude, 3.43 for GPT, for a 25th-to-75th within-post percentile move). But they attribute it differently: the human and Claude to cogency (odds ratios 3.34 [1.58, 8.12] and 2.24 [1.03, 5.79]), GPT to effectiveness (3.41 [1.39, 8.46]). [S2_outcomes, S2_level_difference, S2_human_supplementary]
5. **Redundant with length, not worthless.** On held-out posts, quality rankings alone pick the delta-winning reply within a post 73–75% of the time (human H1 .75, GPT .75, Claude .73; chance is .50). But reply length alone does about as well (.73), and length, timing and position together reach .77, which adding quality does not improve. Every quality ranking, human and LLM, correlates with reply length within a post (.47 to .72). Either longer replies really are better argued, or annotators and models reward length, and this design cannot tell which. A length-matched comparison would separate the two. [S3_quality_alone, S3_incremental, S3_overlap_controls]
6. **Humans differed more from each other than from the models in separating the constructs.** The annotators picked different cogency and effectiveness winners on 12.2% (H1), 8.3% (H3) and 0.5% (H2, 9 of 1,725) of pairs; the models fell inside that range (GPT 9.7%, Claude 7.1%). H2, with a median of 17 seconds per pair, effectively gave one ranking for both questions, and the models agree less with H2 (71–77%) than with H1, so Study 1 is reported against every human reference. [S3_discordance, A1, C2]

**Design note.** Claude was designated the primary model, and H1 the principal human reference, after data collection; neither choice was preregistered. Both models are reported for every analysis, and Part C of `analysis/02_studies.ipynb` repeats Study 1 with each annotator as the reference.

## Repository layout

```text
sampling/
  scrape_and_sample.ipynb       downloads the 2013–2018 archive, reconstructs deltas, draws the sample, writes the two data files below
data/
  annotation_input.csv          the 120 posts × 6 replies shown to annotators and models (text only, no outcomes)
  outcomes.csv                  behavioral outcome, timing, position and sampling probability of each reply
  human/
    calibration_H{1,2,3}.csv    calibration round: 5 posts, 75 pairs, all three annotators
    main_H{1,2,3}.csv           main round: H1 and H2 115 posts (1,725 pairs), H3 58 posts (870 pairs)
annotation/
  human_annotation.ipynb        the annotation interface: protocol, worked examples, calibration and main rounds
llm_annotation/
  cmv_llm_batch.py              builds prompts and batch files, validates responses, parses labels
  run_llm_batches.ipynb         runs both models through their batch APIs (costs money; not needed to reproduce)
  annotation_protocol_*.json    the human protocol, read verbatim by the prompt builder
  system_prompt_*.txt, prompt_preview.md, PROMPT_DESIGN.md, PROMPT_AUDIT.md, audit_prompts.py
  runs/{claude,gpt}/results/    raw batch API responses
  runs/{claude,gpt}/llm_output/ parsed labels, one row per request
analysis/
  01_calibration_agreement.ipynb   calibration-round agreement (Krippendorff's α)
  02_studies.ipynb                 Studies 1–3 and all supporting tables
results/
  calibration/                  outputs of 01
  tables/                       outputs of 02, as .csv and .tex
```

## Reproducing the results

No API calls are needed; every analysis runs from the files in this repository.

```bash
pip install -r requirements.txt
jupyter lab            # then run analysis/01_calibration_agreement.ipynb and analysis/02_studies.ipynb
```

The notebooks find the repository root on their own, so they run from any folder inside it. In Google Colab, clone the repository first (`!git clone <repo-url>`, then `%cd` into it). `02_studies.ipynb` takes about 10 minutes; all bootstraps use fixed seeds, so the tables in `results/` are reproduced exactly.

The LLM step can be checked without spending anything:

- `python llm_annotation/cmv_llm_batch.py build ...` (section 3 of `run_llm_batches.ipynb`) rebuilds the batch request files; they come out byte-identical to the ones submitted.
- `python llm_annotation/cmv_llm_batch.py validate ...` (section 8) re-parses the raw responses in `runs/*/results/` into the label files in `runs/*/llm_output/`, also byte-identically.

## Annotation

**Humans.** Three trained research assistants, referred to as H1, H2 and H3, judged each pair of replies on a four-point scale (Strong A, Weak A, Weak B, Strong B; no ties), using the instructions in `annotation/human_annotation.ipynb`. All three labeled the same five calibration posts. H1 and H2 then labeled all 115 main-round posts, and H3 labeled 58 of them. H1 is the main human reference. Each annotator saw the pairs in their own A/B order; the label files record the order shown, and the analysis restates every label with A = the lower response ID.

**LLMs.** Claude Sonnet 5.5 (`claude-sonnet-5-5`, primary) and GPT-6.1 Sol (`gpt-6.1-sol`, robustness check), each at its lowest reasoning setting. The prompts reproduce the human instructions verbatim, one quality per request, and every pair was sent in both A/B orders: 1,725 pairs × 3 questions × 2 orders = 10,350 requests per model. The third question, evidential support, was collected but is not analyzed. `PROMPT_DESIGN.md` lists every wording change from the human instructions.

## Data notes

- Post and reply texts are public Reddit content from r/ChangeMyView. Delta markers were removed from the text before annotation, and no outcome was shown to annotators or models.
- Released data contain no Reddit usernames, URLs or timestamps; `outcomes.csv` keeps only the columns the analyses use.
- Annotator identities are replaced by H1, H2 and H3. Submission timestamps are removed from the human label files; time spent per pair (`seconds_on_pair_total`) is kept.
- Column definitions are in `data/README.md`.

## Sampling

`sampling/scrape_and_sample.ipynb` downloads every r/ChangeMyView post and comment from 2013–2018 from the public [Arctic Shift](https://arctic-shift.photon-reddit.com) archive (123,560 posts, 5,104,531 comments), reconstructs which direct replies earned a delta, and draws a behavior-stratified sample with a fixed seed: 100 posts with a delta and 20 without, six replies each (one delta, two the OP answered without a delta and three the OP did not answer; or two and four in posts without a delta). Its outputs from the original run are kept in the notebook. Rerunning the download takes several hours and about 1.6 GB, written to `data/archive/` (ignored by git). Its last cell rebuilds `data/annotation_input.csv` and `data/outcomes.csv` byte-for-byte from the drawn sample.

## Use

All rights reserved until the thesis and the accompanying paper are published. Please contact the author (Ariel Gomez Garcia, University of South Florida) by opening an issue on this repository before reusing the data, annotations or code. Post and reply texts in `data/` are public Reddit content that remains subject to Reddit's terms.

## Citation

```bibtex
@mastersthesis{gomezgarcia2026cogency,
  author = {Gomez Garcia, Ariel},
  title  = {Cogency, Expected Rhetorical Effectiveness, and Persuasion in Online Disagreement:
            Human and Large Language Model Judgments of r/ChangeMyView Arguments},
  school = {University of South Florida},
  year   = {2026}
}
```
