# Model Evaluation Harness

This is separate from the study app. It repeatedly asks multiple-choice tasks to one or more OpenAI-compatible models and stores raw outputs plus accuracy summaries.

## Files

- `model_eval.py`: runner script
- `tasks.example.yml`: copy this and add your real tasks
- `runs/<timestamp>_model-<model>_reasoning-<level>/raw_results.jsonl`: every answer, reasoning, raw API response, latency, token usage, reasoning effort, and error
- `runs/<timestamp>_model-<model>_reasoning-<level>/summary_by_model_task.csv`: accuracy and token totals per model, reasoning effort, and task
- `runs/<timestamp>_model-<model>_reasoning-<level>/summary_by_model.csv`: average accuracy and token totals per model and reasoning effort
- `runs/<timestamp>_model-<model>_reasoning-<level>/summary_by_task.csv`: average accuracy and token totals per task and reasoning effort

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
- Default run folders include the model name and reasoning effort. Explicit `--out` paths are used exactly as provided.
- Token counts are read from the API response `usage` field: prompt, completion, total, cached, and reasoning tokens where available. If a provider does not return usage, token columns will be `0` in summaries and `null` in raw results.
- Higher `--workers` values are faster but can hit provider rate limits. Start with `--workers 4` or `--workers 8` and increase only if the run is stable.
- The model is asked to return JSON with `reasoning` and `answer`; imperfect responses are still parsed with fallback extraction where possible.
