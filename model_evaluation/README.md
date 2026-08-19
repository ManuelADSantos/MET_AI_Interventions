# Model Evaluation Harness

This is separate from the study app. It repeatedly asks multiple-choice tasks to one or more OpenAI-compatible models and stores raw outputs plus accuracy summaries.

## Files

- `model_eval.py`: runner script
- `tasks.example.yml`: copy this and add your real tasks
- `runs/<timestamp>_model-<model>_reasoning-<level>_mode-<mode>/raw_results.jsonl`: every answer, reasoning, raw API response, latency, token usage, reasoning effort, response mode, extractor output, and error
- `runs/<timestamp>_model-<model>_reasoning-<level>_mode-<mode>/summary_by_model_task.csv`: accuracy and token totals per model, reasoning effort, response mode, extractor, and task
- `runs/<timestamp>_model-<model>_reasoning-<level>_mode-<mode>/summary_by_model.csv`: average accuracy and token totals per model, reasoning effort, response mode, and extractor
- `runs/<timestamp>_model-<model>_reasoning-<level>_mode-<mode>/summary_by_task.csv`: average accuracy and token totals per task, reasoning effort, response mode, and extractor

## Task Format

Use one YAML item per question:

```yaml
tasks:
  - id: future_days_02
    correct: A
    question: >
      Which statement is correct?
    options:
      A: Only statement 1 is correct.
      B: Only statement 2 is correct.
      C: Both statements are correct.
      D: Neither statement is correct.
    context: |
      Paste all information the model needs here.
```

This explicit file is more practical for evaluation than parsing `ai_tasks.md`, because you can audit the exact context, question, answer choices, and correct answer.

## API Key

PowerShell:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

For another OpenAI-compatible provider, add another provider with its `base_url` and `api_key_env`.

## Run

From the repo root:

```powershell
cd MET_AI_Interventions
python evaluation/model_eval.py --config evaluation/tasks.example.yml --n 10
```

Use `--n 100` for 100 repeated prompts per task/model.

Use `--workers` to run API calls in parallel:

```powershell
python evaluation/model_eval.py --config evaluation/tasks.example.yml --n 100 --workers 8
```

## Natural Responses

Use `response_mode: natural` when you want the evaluated model to answer like a normal GPT assistant instead of returning machine-readable JSON. In this mode, configure a smaller `answer_extractor` model to read the natural response and extract the answer letter for scoring:

```yaml
response_mode: natural
system_prompt: >
  You are a careful logical reasoning assistant. Solve the task independently.
  Answer naturally, like a normal GPT assistant.

answer_extractor:
  provider: openai
  name: gpt-5.4-nano
  max_completion_tokens: 200
```

The natural response is stored in `response_text`. The extractor output is stored separately in `extraction_response_text` and `extraction_raw_response`.

## Analyze Wrong Responses

Create a paste-ready file with the task context, question, answer choices, correct answer, and all wrong responses for one task:

```powershell
python evaluation/extract_wrong_responses.py evaluation/evaluation/runs/<run>/raw_results.jsonl --task-id future_days_01 --out wrong_future_days_01.txt
```

Use `--responses-only` if you only want the wrong response texts.

## Notes

- The script does not send `temperature`, because some newer GPT-style models reject it.
- The script sends `max_completion_tokens`, because newer GPT-style models reject the older `max_tokens` parameter.
- Add `reasoning_effort` to a model entry to record and send a reasoning level, for example `reasoning_effort: low` or `reasoning_effort: minimal`.
- Default run folders include the model name, reasoning effort, response mode, and extractor model where applicable. Explicit `--out` paths are used exactly as provided.
- Token counts are read from the API response `usage` field: prompt, completion, total, cached, and reasoning tokens where available. If a provider does not return usage, token columns will be `0` in summaries and `null` in raw results.
- Higher `--workers` values are faster but can hit provider rate limits. Start with `--workers 4` or `--workers 8` and increase only if the run is stable.
- In `response_mode: json`, the model is asked to return JSON with `reasoning` and `answer`; imperfect responses are still parsed with fallback extraction where possible.
