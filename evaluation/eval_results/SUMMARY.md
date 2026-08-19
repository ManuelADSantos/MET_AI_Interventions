# Pause-points vs. ai baseline — eval results

`tests/eval_intervention_accuracy.py`, model `gpt-5.4-mini`, 12 tasks x 3 reps per arm.
Scored against `customizations/correct_answers.py`. Raw data in `continue.json`, logs in `*.log`.

Two scripted participants, because they stress different rules:

- **patient** — always replies "continue"
- **impatient** — always replies "just tell me the answer"

## Results

| sweep | arm | correct | mean turns | never concluded |
|---|---|---|---|---|
| patient | ai | **15/36 — 41.7%** | 1.0 | 0 |
| patient | pause-points | **11/36 — 30.6%** | 11.1 | 9/36 (25%) |
| impatient | ai | **15/36 — 41.7%** | 1.0 | 0 |
| impatient | pause-points | **4/30 — 13.3%** | 12.3 | 22/30 (73%) |

The impatient sweep crashed at 30 of 36 pause-points runs (`ConnectionResetError`, no retry in the
harness). Its figures are reconstructed from `answer.log`; the baseline half finished.

Baseline landed on 41.7% in both sweeps independently — it is single-turn, so the participant
policy cannot touch it. That agreement is the harness's sanity check.

## The important cut

Counting only pause-points runs that actually reached a verdict, patient sweep:

- **10/27 — 37.0%**, against a 41.7% baseline.

**Reasoning quality is roughly unaffected. Nearly all the measured accuracy loss is failure to
finish**, not worse thinking. That points at the termination rules, not at decomposition.

## Rule violations

| violation | patient (36 runs) | impatient (30 runs) |
|---|---|---|
| never concluded | 9 | 22 |
| held twice in a row | 1 | **28** |
| repeated a question verbatim | 2 | 25 |
| step numbering restarted or repeated | 1 | 20 |
| named an option before the final step | 1 | — |

**The liveness guarantee is not holding.** "Never do this twice running: if your previous reply was
one of these, your next reply carries out work" was violated in 28 of 30 impatient runs. Under a
participant who asks for the answer every turn, the assistant holds indefinitely — the broken-bot
failure this prompt exists to prevent, returning under sustained pressure.

Two likely causes, both untested:

1. The rule sits at the very end of a long bullet. The answer-demand trigger at the start of the
   same bullet matches every turn and fires first.
2. Nothing in the transcript marks a reply as "a hold", so the model has to recognise its own
   previous message as one before the rule can apply.

The ten-step ceiling is partly working: most patient runs concluded at exactly step 10, but 9 ran
past it. It is obeyed when the model's own count is clean and missed when the numbering stutters.

## Standing conclusion

- No evidence the prompt harms reasoning. The confound this eval was built to check is clear.
- It does harm **completion**, badly, and worse the more impatient the participant.
- A quarter of patient sessions and three quarters of impatient ones would end with a participant
  who never received an answer. That is a data-quality problem, not just a prompt bug.

## To reproduce

```bash
python3 tests/eval_intervention_accuracy.py --tasks 12 --reps 3 --policy continue --out eval_results/continue.json
python3 tests/eval_intervention_accuracy.py --tasks 12 --reps 3 --policy answer   --out eval_results/answer.json
```
