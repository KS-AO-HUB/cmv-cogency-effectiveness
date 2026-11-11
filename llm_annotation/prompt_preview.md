# LLM prompt preview — calibration OP 1, pair 1

Protocol `cmv_annotation_v4_2026_09_24`. This is exactly what one batch request sends: a system message (identical for every request of that metric, so it is cached) and a user message (the OP and one A/B pair). Three requests per pair, one per metric; each pair is also sent with A and B swapped.





---

## Cogency

### System message

```text
## OVERVIEW
In each annotation, you will see one original r/ChangeMyView post and two direct responses to that post, labeled Response A and Response B. You will make one judgment: Cogency. Judge only the material shown to you. Do not search the web, look up the users, or use information from later discussion. Base your judgments about the OP on the original post and reasonable inferences from what the OP says. Do not assume facts about the OP that are unsupported by the post or use outside information about the user. Judge the displayed pair on its own.

## FOUR-WAY COMPARATIVE SCALE
Choose exactly one of four positions on the comparative scale: Strong A, Weak A, Weak B, or Strong B. Every position selects either A or B; the Strong/Weak distinction records how large the difference seems. Use Strong when one response is clearly better on the question being asked. Use Weak when one response is only somewhat better or you have only a slight preference. There is no tie option. If the responses seem nearly equal, choose the side you lean toward and use Weak. Strong/Weak describes the strength of the comparative preference, not your confidence in your own judgment.
- Strong A: Response A is clearly better on the target question.
- Weak A: Response A is somewhat better, or you only slightly prefer A.
- Weak B: Response B is somewhat better, or you only slightly prefer B.
- Strong B: Response B is clearly better on the target question.

## COGENCY — QUALITY OF THE ARGUMENT
A cogent argument offers reasons that adequately support its conclusion. Judge the argument advanced by the response itself. Consider three aspects: Acceptability — are the premises reasonable enough to serve as support for the conclusion? Relevance — do the premises actually bear on the conclusion? Sufficiency — taken together, do the premises provide enough support for drawing the conclusion? Do not judge cogency by whether you personally agree with the conclusion or by whether this particular OP is likely to be persuaded. Use the material shown and ordinary background knowledge. Do not conduct external fact-checking. A response does not need citations or formal evidence to be cogent.

Decision question: Which response advances the more cogent argument?

## RESPONSES THAT ARE NOT CLEAR ARGUMENTS
Some randomly sampled responses may be questions, jokes, insults, simple agreement or disagreement, bare assertions, or otherwise provide little argumentative content. This is expected. Make the requested judgment as best you can.

## Worked examples
### Example 1 — Cogency
Original post: CMV: Campus dining does not need to stay open after 8 p.m. because students can simply eat earlier.

Response A: Some required evening classes end after 8 p.m. Students on meal plans may therefore lose access to food they have already paid for.

Response B: Campus dining should stay open later because 8 p.m. is too early, and many students probably prefer eating later anyway.

Illustration: Response A may be more cogent because its reasons are directly relevant to the conclusion and provide clearer support for it. The example illustrates the cogency criteria; real annotations may be less clear-cut.

## HOW TO ANSWER
Before answering, give one sentence of reasoning about the pair, applying the instructions and definition above, and write that reasoning in the "reasoning" field.

Respond with a JSON object with these fields, in this order:
- "reasoning": your single-sentence reasoning.
- "choice": exactly one of "Strong A", "Weak A", "Weak B", "Strong B".
```

### User message

```text
THE ORIGINAL POST
I believe that the new "score hiding" system is poorly done and only makes viewing comment threads more annoying. CMV

The intention is to allow people to not upvote other posts simply because they already have upvotes, but it didn't address the reason that upvoted posts gather more upvotes. No one looks at a comment and thinks, "Wow, 2140 other people liked this, certainly it's worth another!" Rather, the reason that upvoted posts accumulate upvotes is simply because they get seen more. People stop scrolling down at some point. And even with votes hidden, *reddit doesn't change the sort order*. Upvoted posts still gather upvotes like a torrent.

---

RESPONSE A
Often I find myself following the opinion of the mass. When I see a comment is controversial, I become especially critical to what is being said. And when I see a comment that has a very good upvote downvote ratio I rarely disagree, because I don't expect myself to.

So I think it forces people to think more for themselves and not follow the hive mind.

It's true that the sort order wasn't changed, this is necessary to not change the concept of Reddit's upvote system too much. It's a good compromise in my opinion, especially for discussion based subreddits like CMV.

---

RESPONSE B
To some extent, our opinions and perspectives are affected by the impressions of others, or the group dynamic. If you think about it - we always read the comment score, when really why should we? Shouldn't the content of the comment be valid enough? Is it that important to see what other people think before thinking ourselves?

For example: seeing a comment that reads 'wow that's great' with many down votes will subconsciously make us read it in a negative, sarcastic tone (or at least make us believe that was its intent). It takes just one person commenting on a comment: 'I don't know why your being downvoted' to sway people into sympathising a little with the original commenter - such is the power of social affirmation and mob mentality.

Getting rid of the comment score does more good than harm - it's really irrelevant meta-information that gives us a sense that we're more informed, which is nice but not when it has an adverse effect on effective discussion.

---

COGENCY — QUALITY OF THE ARGUMENT
Which response advances the more cogent argument? Consider whether its reasons are acceptable, relevant, and sufficient. Judge argument quality, not whether this particular OP would be persuaded.
Which response advances the more cogent argument?
Weak = one response is somewhat better or you only slightly prefer it. Strong = one response is clearly better. No ties: if they seem nearly equal, choose the side you lean toward and use Weak.
Strong A
Weak A
Weak B
Strong B
```

### Enforced output schema (OpenAI Structured Outputs; Anthropic uses the inner "schema")

```json
{
  "name": "cmv_cogency_judgment",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "reasoning": {
        "type": "string"
      },
      "choice": {
        "type": "string",
        "enum": [
          "Strong A",
          "Weak A",
          "Weak B",
          "Strong B"
        ]
      }
    },
    "required": [
      "reasoning",
      "choice"
    ],
    "additionalProperties": false
  }
}
```

---

## Expected Rhetorical Effectiveness

### System message

```text
## OVERVIEW
In each annotation, you will see one original r/ChangeMyView post and two direct responses to that post, labeled Response A and Response B. You will make one judgment: Expected Rhetorical Effectiveness. Judge only the material shown to you. Do not search the web, look up the users, or use information from later discussion. Base your judgments about the OP on the original post and reasonable inferences from what the OP says. Do not assume facts about the OP that are unsupported by the post or use outside information about the user. Judge the displayed pair on its own.

## FOUR-WAY COMPARATIVE SCALE
Choose exactly one of four positions on the comparative scale: Strong A, Weak A, Weak B, or Strong B. Every position selects either A or B; the Strong/Weak distinction records how large the difference seems. Use Strong when one response is clearly better on the question being asked. Use Weak when one response is only somewhat better or you have only a slight preference. There is no tie option. If the responses seem nearly equal, choose the side you lean toward and use Weak. Strong/Weak describes the strength of the comparative preference, not your confidence in your own judgment.
- Strong A: Response A is clearly better on the target question.
- Weak A: Response A is somewhat better, or you only slightly prefer A.
- Weak B: Response B is somewhat better, or you only slightly prefer B.
- Strong B: Response B is clearly better on the target question.

## EXPECTED RHETORICAL EFFECTIVENESS — LIKELIHOOD OF CHANGING THIS OP'S VIEW
Predict which response is more likely to change this particular OP's stated view. Use the original post to understand the OP's stated position, reasons, concerns, values, priorities, and other context they provide. You may make reasonable inferences from this information when predicting what might persuade them. In many cases, the OP will not explicitly state everything that matters, so use your best judgment based on the context available in the post. Do not assume unsupported personal characteristics or use information from outside the material shown. This is an ex ante judgment: predict which response is more likely to change the OP's view without knowing what actually happened afterward. If useful, you may consider rhetorical features such as credibility, emotional appeal, clarity, appropriateness, and arrangement. These are guidance, not a checklist, and they do not define the answer. Other aspects of the response may also matter. Do not judge whether you would be persuaded.

Decision question: Which response is more likely to change this particular OP's stated view?

## RESPONSES THAT ARE NOT CLEAR ARGUMENTS
Some randomly sampled responses may be questions, jokes, insults, simple agreement or disagreement, bare assertions, or otherwise provide little argumentative content. This is expected. Make the requested judgment as best you can.

## Worked examples
### Example 2 — Expected Rhetorical Effectiveness
Original post: CMV: I do not use two-factor authentication because I do not want to enter another code every time I log in.

Response A: Two-factor authentication adds an extra step, but the added security is worth the inconvenience because it makes accounts much harder to compromise.

Response B: Many services can remember a trusted device, so you may not need a code every time. That directly addresses the inconvenience you are worried about.

Illustration: Response B may be more likely to change this particular OP's stated view because it directly addresses the concern the OP identified. In many real annotations, you will need to make your best prediction from the contextual information in the OP's post. The task is not which response would persuade people in general.

## HOW TO ANSWER
Before answering, give one sentence of reasoning about the pair, applying the instructions and definition above, and write that reasoning in the "reasoning" field.

Respond with a JSON object with these fields, in this order:
- "reasoning": your single-sentence reasoning.
- "choice": exactly one of "Strong A", "Weak A", "Weak B", "Strong B".
```

### User message

```text
THE ORIGINAL POST
I believe that the new "score hiding" system is poorly done and only makes viewing comment threads more annoying. CMV

The intention is to allow people to not upvote other posts simply because they already have upvotes, but it didn't address the reason that upvoted posts gather more upvotes. No one looks at a comment and thinks, "Wow, 2140 other people liked this, certainly it's worth another!" Rather, the reason that upvoted posts accumulate upvotes is simply because they get seen more. People stop scrolling down at some point. And even with votes hidden, *reddit doesn't change the sort order*. Upvoted posts still gather upvotes like a torrent.

---

RESPONSE A
Often I find myself following the opinion of the mass. When I see a comment is controversial, I become especially critical to what is being said. And when I see a comment that has a very good upvote downvote ratio I rarely disagree, because I don't expect myself to.

So I think it forces people to think more for themselves and not follow the hive mind.

It's true that the sort order wasn't changed, this is necessary to not change the concept of Reddit's upvote system too much. It's a good compromise in my opinion, especially for discussion based subreddits like CMV.

---

RESPONSE B
To some extent, our opinions and perspectives are affected by the impressions of others, or the group dynamic. If you think about it - we always read the comment score, when really why should we? Shouldn't the content of the comment be valid enough? Is it that important to see what other people think before thinking ourselves?

For example: seeing a comment that reads 'wow that's great' with many down votes will subconsciously make us read it in a negative, sarcastic tone (or at least make us believe that was its intent). It takes just one person commenting on a comment: 'I don't know why your being downvoted' to sway people into sympathising a little with the original commenter - such is the power of social affirmation and mob mentality.

Getting rid of the comment score does more good than harm - it's really irrelevant meta-information that gives us a sense that we're more informed, which is nice but not when it has an adverse effect on effective discussion.

---

EXPECTED RHETORICAL EFFECTIVENESS — LIKELIHOOD OF CHANGING THIS OP'S VIEW
Which response is more likely to change this particular OP's stated view? Use the context available in the OP's post, including reasonable inferences from what the OP says, and make your best prediction. Optional cues include credibility, emotional appeal, clarity, appropriateness, and arrangement; these are guidance, not separate criteria.
Which response is more likely to change this particular OP's stated view?
Weak = one response is somewhat better or you only slightly prefer it. Strong = one response is clearly better. No ties: if they seem nearly equal, choose the side you lean toward and use Weak.
Strong A
Weak A
Weak B
Strong B
```

### Enforced output schema (OpenAI Structured Outputs; Anthropic uses the inner "schema")

```json
{
  "name": "cmv_effectiveness_judgment",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "reasoning": {
        "type": "string"
      },
      "choice": {
        "type": "string",
        "enum": [
          "Strong A",
          "Weak A",
          "Weak B",
          "Strong B"
        ]
      }
    },
    "required": [
      "reasoning",
      "choice"
    ],
    "additionalProperties": false
  }
}
```

---

## Evidential Support

### System message

```text
## OVERVIEW
In each annotation, you will see one original r/ChangeMyView post and two direct responses to that post, labeled Response A and Response B. You will make one judgment: Evidential Support. Judge only the material shown to you. Do not search the web, look up the users, or use information from later discussion. Base your judgments about the OP on the original post and reasonable inferences from what the OP says. Do not assume facts about the OP that are unsupported by the post or use outside information about the user. Judge the displayed pair on its own.

## FOUR-WAY COMPARATIVE SCALE
If both responses provide evidence, choose exactly one of four positions on the comparative scale: Strong A, Weak A, Weak B, or Strong B. Every position selects either A or B; the Strong/Weak distinction records how large the difference seems. Use Strong when one response is clearly better on the question being asked. Use Weak when one response is only somewhat better or you have only a slight preference. There is no tie option. If the responses seem nearly equal, choose the side you lean toward and use Weak. Strong/Weak describes the strength of the comparative preference, not your confidence in your own judgment.
- Strong A: Response A is clearly better on the target question.
- Weak A: Response A is somewhat better, or you only slightly prefer A.
- Weak B: Response B is somewhat better, or you only slightly prefer B.
- Strong B: Response B is clearly better on the target question.

## EVIDENTIAL SUPPORT
Evidence is concrete supporting information offered for a claim. It may include facts, data, statistics, research findings, documented real-world examples, or information attributed to an identifiable source. A bare assertion, opinion, value judgment, rhetorical question, insult, or simple restatement of a conclusion does not count as evidence by itself. First, indicate independently whether each response provides any concrete supporting information beyond a bare assertion, opinion, or restatement. If both responses provide evidence, compare their evidential support. Consider how specific and concrete the evidence is, how well it supports the claim being made, and, where relevant, whether the response identifies the source or basis of the evidence. Do not open links, search for sources, or independently fact-check claims. A citation or institutional source is not automatically stronger evidence.

First: Which responses provide evidence in support of their argument? Check all that apply.
If both are checked: Which response provides stronger evidential support for its argument?

## RESPONSES THAT ARE NOT CLEAR ARGUMENTS
Some randomly sampled responses may be questions, jokes, insults, simple agreement or disagreement, bare assertions, or otherwise provide little argumentative content. This is expected. Make the requested judgment as best you can.

## Worked examples
### Example 3 — Evidential Support: evidence present versus absent
Original post: CMV: My local bus service seems reliable enough.

Response A: The bus system is unreliable because everyone who uses Route 18 knows that buses are late all the time.

Response B: The city's 2025 transit report says Route 18 arrived more than five minutes late on 27% of recorded trips.

Illustration: Response A makes an empirical claim but provides no concrete supporting information, so its evidence box would remain unchecked. Response B provides a specific statistic and identifies its source, so its evidence box would be checked. You do not need to verify the report.

### Example 4 — Evidential Support: both responses contain evidence
Original post: CMV: Route 18 is reliable enough that occasional delays are not a real problem.

Response A: A local group called Transit Riders for Better Service surveyed 52 people at its 'Fix Our Buses' meeting. Forty-six said Route 18 is frequently late.

Response B: The city transit agency's automatic vehicle records show that Route 18 arrived more than five minutes late on 29% of 8,412 recorded trips during the last six months.

Illustration: Both responses provide evidence, so both evidence boxes would be checked. Response A gives concrete survey results, but the respondents are a small, self-selected group attending a meeting specifically about bus problems. Response B may provide stronger evidential support for a general claim about Route 18's reliability because it directly summarizes thousands of recorded trips over an extended period. The task is to judge how well the evidence presented supports the claim, not to verify either source externally.

## HOW TO ANSWER
Before answering, give one sentence of reasoning about the pair, applying the instructions and definition above, and write that reasoning in the "reasoning" field.

Respond with a JSON object with these fields, in this order:
- "reasoning": your single-sentence reasoning.
- "evidence_present": the boxes you check: a list containing "Response A provides evidence" and/or "Response B provides evidence", or an empty list if you check neither.
- "choice": if both are checked, exactly one of "Strong A", "Weak A", "Weak B", "Strong B"; otherwise null.
```

### User message

```text
THE ORIGINAL POST
I believe that the new "score hiding" system is poorly done and only makes viewing comment threads more annoying. CMV

The intention is to allow people to not upvote other posts simply because they already have upvotes, but it didn't address the reason that upvoted posts gather more upvotes. No one looks at a comment and thinks, "Wow, 2140 other people liked this, certainly it's worth another!" Rather, the reason that upvoted posts accumulate upvotes is simply because they get seen more. People stop scrolling down at some point. And even with votes hidden, *reddit doesn't change the sort order*. Upvoted posts still gather upvotes like a torrent.

---

RESPONSE A
Often I find myself following the opinion of the mass. When I see a comment is controversial, I become especially critical to what is being said. And when I see a comment that has a very good upvote downvote ratio I rarely disagree, because I don't expect myself to.

So I think it forces people to think more for themselves and not follow the hive mind.

It's true that the sort order wasn't changed, this is necessary to not change the concept of Reddit's upvote system too much. It's a good compromise in my opinion, especially for discussion based subreddits like CMV.

---

RESPONSE B
To some extent, our opinions and perspectives are affected by the impressions of others, or the group dynamic. If you think about it - we always read the comment score, when really why should we? Shouldn't the content of the comment be valid enough? Is it that important to see what other people think before thinking ourselves?

For example: seeing a comment that reads 'wow that's great' with many down votes will subconsciously make us read it in a negative, sarcastic tone (or at least make us believe that was its intent). It takes just one person commenting on a comment: 'I don't know why your being downvoted' to sway people into sympathising a little with the original commenter - such is the power of social affirmation and mob mentality.

Getting rid of the comment score does more good than harm - it's really irrelevant meta-information that gives us a sense that we're more informed, which is nice but not when it has an adverse effect on effective discussion.

---

EVIDENTIAL SUPPORT
First decide independently whether A and B provide concrete information in support of their arguments. If both do, compare how specific and concrete the evidence is, how well it supports the claim being made, and, where relevant, whether the response identifies the source or basis of the evidence. Do not open links or independently verify the claims.
Which responses provide evidence in support of their argument? Check all that apply.
Response A provides evidence
Response B provides evidence

---

If both are checked:
EVIDENTIAL SUPPORT — COMPARISON
Both responses provide evidence. Compare the evidence itself, not the overall writing or argument.
Which response provides stronger evidential support for its argument?
Weak = one response is somewhat better or you only slightly prefer it. Strong = one response is clearly better. No ties: if they seem nearly equal, choose the side you lean toward and use Weak.
Strong A
Weak A
Weak B
Strong B
```

### Enforced output schema (OpenAI Structured Outputs; Anthropic uses the inner "schema")

```json
{
  "name": "cmv_evidence_judgment",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "reasoning": {
        "type": "string"
      },
      "evidence_present": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "Response A provides evidence",
            "Response B provides evidence"
          ]
        }
      },
      "choice": {
        "type": [
          "string",
          "null"
        ],
        "enum": [
          "Strong A",
          "Weak A",
          "Weak B",
          "Strong B",
          null
        ]
      }
    },
    "required": [
      "reasoning",
      "evidence_present",
      "choice"
    ],
    "additionalProperties": false
  }
}
```