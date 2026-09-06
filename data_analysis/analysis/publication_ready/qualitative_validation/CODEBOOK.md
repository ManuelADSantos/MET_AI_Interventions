# Codebook v2 for the human coder pass

Multi-label coding: give every code that applies, separated by semicolons (e.g. `own_first_then_compare;ai_self_verify`). You may use the shorthand letter/digit in the first column instead (e.g. `b;d`, or `bd`, spaces and commas also work). Leave the cell empty when no code applies (the answer is vague, idiosyncratic, or off-topic). Code the literal content of the answer, not what you infer about the participant.

## Strategy question (rows whose question starts with STRATEGIES)

| Key | Code | Definition |
|---|---|---|
| a | `full_reliance` | Relied on / trusted the AI wholly |
| b | `own_first_then_compare` | Formed own answer first, then compared with the AI |
| c | `verify_against_source` | Checked the AI's answer against the scenario/brief text |
| d | `ai_self_verify` | Verification delegated to the AI itself (double-check, re-ask, confidence) |
| e | `reasoning_check` | Read/critiqued the AI's reasoning or logic |
| f | `effort_cost_time` | Workload/time pressure given as reason for reliance |
| g | `prompt_engineering` | Structured the interaction: decomposition, rephrasing, context hygiene |
| h | `manipulation_use` | Used the condition's own feature as a strategy (own condition only) |
| i | `overrode_ai` | Disagreed with / overruled / challenged the AI |
| j | `unspecified_verification` | Double-checked / verified without saying how (residual) |
| k | `no_strategy` | Explicitly no strategy / gut feeling (short answers only) |

`manipulation_use` applies only when the respondent describes using their own condition's feature (the reliability card, the two replies, the step-wise pauses, the reflection page) as a strategy.

## Manipulation question (rows whose question starts with MANIPULATION)

| Key | Code | Definition |
|---|---|---|
| 0 | `no_change` | The manipulation did not change anything (answer says no / nothing / not at all) |
| 1 | `more_careful` | Made the respondent more careful, cautious, critical, or attentive |
| 2 | `slowed_friction` | Slowed the respondent down, added friction or took longer |
| 3 | `trust_more` | Increased trust in the AI |
| 4 | `trust_less` | Decreased trust in the AI |

`no_change` is used only when nothing else applies.
