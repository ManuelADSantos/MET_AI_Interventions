# API Cost Analysis — gpt-5.4-mini (low reasoning)

> Estimated 2026-07-09. Pricing from [OpenAI API](https://developers.openai.com/api/docs/pricing).

## Pricing

| | Per 1M tokens |
|---|---|
| **Input** | $0.75 |
| **Output** (incl. reasoning) | $4.50 |

## Study structure

- **Model:** `gpt-5.4-mini` with `reasoning_effort: low`
- **System prompt:** "You are a helpful logical reasoning assistant" (~8 tokens)
- **Questions:** 12 (4 scenarios × 3 questions each)
- **Chat required on:** pages 3–99 (`require_ai_prompt_pages`)
- **Only `ai` condition costs anything** — `no-ai` participants = $0

## Per-question token estimates

| | First message | Follow-up message |
|---|---|---|
| **Input** | ~550 tokens (system + copied scenario ~400 + question ~100) | ~1,150 tokens (history replay + new message) |
| **Output** | ~300 tokens (low-effort reasoning + answer) | ~300 tokens |

## Per-participant cost (12 questions)

| Scenario | Msgs/question | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| **Minimum** | 1 | 6,600 | 3,600 | **~$0.02** |
| **Typical** | 2 | 18,600 | 7,200 | **~$0.05** |
| **Heavy** | 3 | 41,400 | 10,800 | **~$0.08** |

### Cost breakdown by scenario

```
         Input cost    Output cost    Total
Min      $0.005        $0.016         $0.021
Typical  $0.014        $0.032         $0.046
Heavy    $0.031        $0.049         $0.080
```

## At scale

| Participants | Minimum | Typical | Heavy |
|---|---|---|---|
| 100 | $2 | $5 | $8 |
| 500 | $10 | $25 | $40 |
| 1,000 | $20 | $50 | $80 |

## Notes

- Current `ai_tasks.md` only has 3 questions (1 scenario). With 3 questions: ~$0.01/participant typical.
- Estimates assume participants use the copy button to paste scenario context (most likely path given `require_ai_prompt`).
- `reasoning_effort: none` (config default) would be slightly cheaper — no reasoning tokens generated.
- Conversation history resets per page; no cross-question accumulation.
