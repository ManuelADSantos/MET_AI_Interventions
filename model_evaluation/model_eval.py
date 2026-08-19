import argparse
import csv
import json
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml
from openai import OpenAI
from tqdm import tqdm


ANSWER_RE = re.compile(r"\b([A-Z])\b", re.IGNORECASE)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slugify(value):
    text = str(value or "default").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "default"


def run_label(models, response_mode="json", extractor_config=None):
    extractor_label = ""
    if response_mode == "natural" and extractor_config:
        extractor_label = f"_extractor-{slugify(extractor_config['name'])}"

    if len(models) == 1:
        model = models[0]
        reasoning_effort = model.get("reasoning_effort") or "default"
        return (
            f"{run_id()}_model-{slugify(model['name'])}_reasoning-{slugify(reasoning_effort)}"
            f"_mode-{slugify(response_mode)}{extractor_label}"
        )

    model_label = "__".join(slugify(model["name"]) for model in models)
    reasoning_values = sorted({str(model.get("reasoning_effort") or "default") for model in models})
    reasoning_label = slugify(reasoning_values[0]) if len(reasoning_values) == 1 else "mixed"
    return (
        f"{run_id()}_models-{model_label}_reasoning-{reasoning_label}"
        f"_mode-{slugify(response_mode)}{extractor_label}"
    )


def build_prompt(task, response_mode="json"):
    option_lines = "\n".join(f"{key}. {value}" for key, value in task.get("options", {}).items())

    prompt = f"""Evaluate this multiple-choice task.

Context / information:
{task.get("context", "").strip()}

Question:
{task.get("question", "").strip()}

Answer choices:
{option_lines}
"""

    if response_mode == "natural":
        return prompt

    return prompt + """
Return only JSON in this shape:
{{
  "reasoning": "Briefly solve the task before choosing the answer.",
  "answer": "A"
}}
"""


def build_extraction_prompt(task, response_text):
    option_lines = "\n".join(f"{key}. {value}" for key, value in task.get("options", {}).items())

    return f"""Extract the final multiple-choice answer from the model response.

Question:
{task.get("question", "").strip()}

Answer choices:
{option_lines}

Model response:
{response_text.strip()}

Return only JSON in this shape:
{{
  "answer": "A"
}}
"""


def parse_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None

    return None


def normalize_answer(value, options):
    if value is None:
        return None

    text = str(value).strip()
    upper_text = text.upper()
    valid_keys = {str(key).upper(): str(key).upper() for key in options.keys()}

    if upper_text in valid_keys:
        return valid_keys[upper_text]

    for key, option_text in options.items():
        if text.lower() == str(option_text).strip().lower():
            return str(key).upper()

    answer_match = re.search(r"(?:answer|choice|option)\s*[:\-]?\s*([A-Z])\b", text, re.IGNORECASE)
    if answer_match and answer_match.group(1).upper() in valid_keys:
        return answer_match.group(1).upper()

    first_letter = ANSWER_RE.search(text)
    if first_letter and first_letter.group(1).upper() in valid_keys:
        return first_letter.group(1).upper()

    return None


def get_client(provider):
    api_key_env = provider.get("api_key_env")
    api_key = provider.get("api_key") or (os.getenv(api_key_env) if api_key_env else None)

    if not api_key:
        if api_key_env and str(api_key_env).startswith("sk-"):
            raise RuntimeError(
                f"Provider '{provider.get('name', 'unknown')}' has an API key in api_key_env. "
                "Use api_key_env: OPENAI_API_KEY and set that environment variable, or use api_key directly."
            )

        raise RuntimeError(
            f"Missing API key for provider '{provider.get('name', 'unknown')}'. "
            f"Set {api_key_env} or add api_key in the config."
        )

    kwargs = {"api_key": api_key}
    if provider.get("base_url"):
        kwargs["base_url"] = provider["base_url"]

    return OpenAI(**kwargs)


def call_model(client, model_name, messages, max_completion_tokens, reasoning_effort=None):
    start = time.time()
    request = {
        "model": model_name,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
    }
    if reasoning_effort:
        request["reasoning_effort"] = reasoning_effort

    completion = client.chat.completions.create(**request)
    elapsed = time.time() - start
    data = completion.model_dump()
    content = data["choices"][0]["message"].get("content") or ""
    return content, data, elapsed


def get_usage(raw_response):
    usage = raw_response.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_tokens": prompt_details.get("cached_tokens"),
        "reasoning_tokens": completion_details.get("reasoning_tokens"),
    }


def evaluate_once(client, model_config, task, defaults, iteration, max_retries, extractor_client=None, extractor_config=None):
    options = task.get("options") or {}
    correct = normalize_answer(task.get("correct"), options)
    messages = [
        {"role": "system", "content": defaults["system_prompt"]},
        {"role": "user", "content": build_prompt(task, defaults["response_mode"])},
    ]
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            content, raw_response, elapsed = call_model(
                client=client,
                model_name=model_config["name"],
                messages=messages,
                max_completion_tokens=model_config.get(
                    "max_completion_tokens",
                    model_config.get("max_tokens", defaults["max_completion_tokens"]),
                ),
                reasoning_effort=model_config.get("reasoning_effort"),
            )
            parsed = parse_json_object(content)
            extraction_content = ""
            extraction_raw_response = None
            extraction_error = None

            if defaults["response_mode"] == "natural" and extractor_client and extractor_config:
                try:
                    extraction_content, extraction_raw_response, _ = call_model(
                        client=extractor_client,
                        model_name=extractor_config["name"],
                        messages=[
                            {
                                "role": "system",
                                "content": "You extract multiple-choice answers. Return only the requested JSON.",
                            },
                            {"role": "user", "content": build_extraction_prompt(task, content)},
                        ],
                        max_completion_tokens=extractor_config.get("max_completion_tokens", 200),
                        reasoning_effort=extractor_config.get("reasoning_effort"),
                    )
                    extraction_parsed = parse_json_object(extraction_content)
                    predicted = normalize_answer(
                        extraction_parsed.get("answer") if extraction_parsed else extraction_content,
                        options,
                    )
                except Exception as exc:
                    extraction_error = str(exc)
                    predicted = normalize_answer(content, options)
            else:
                predicted = normalize_answer(parsed.get("answer") if parsed else content, options)

            usage = get_usage(raw_response)

            return {
                "timestamp": now_iso(),
                "model": model_config["name"],
                "provider": model_config.get("provider", "default"),
                "reasoning_effort": model_config.get("reasoning_effort") or "default",
                "response_mode": defaults["response_mode"],
                "extractor_model": extractor_config.get("name") if extractor_config else "none",
                "task_id": task["id"],
                "iteration": iteration,
                "correct_answer": correct,
                "predicted_answer": predicted,
                "is_correct": predicted == correct if predicted and correct else False,
                "latency_seconds": round(elapsed, 3),
                **usage,
                "parsed": parsed,
                "response_text": content,
                "raw_response": raw_response,
                "extraction_response_text": extraction_content,
                "extraction_raw_response": extraction_raw_response,
                "extraction_error": extraction_error,
                "error": extraction_error,
            }
        except Exception as exc:
            last_error = str(exc)
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))

    return {
        "timestamp": now_iso(),
        "model": model_config["name"],
        "provider": model_config.get("provider", "default"),
        "reasoning_effort": model_config.get("reasoning_effort") or "default",
        "response_mode": defaults["response_mode"],
        "extractor_model": extractor_config.get("name") if extractor_config else "none",
        "task_id": task["id"],
        "iteration": iteration,
        "correct_answer": correct,
        "predicted_answer": None,
        "is_correct": False,
        "latency_seconds": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "cached_tokens": None,
        "reasoning_tokens": None,
        "parsed": None,
        "response_text": "",
        "raw_response": None,
        "extraction_response_text": "",
        "extraction_raw_response": None,
        "extraction_error": None,
        "error": last_error,
    }


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(results, group_fields):
    grouped = defaultdict(list)
    for row in results:
        grouped[tuple(row[field] for field in group_fields)].append(row)

    summary = []
    for key, rows in sorted(grouped.items()):
        total = len(rows)
        answered = sum(1 for row in rows if row["predicted_answer"])
        correct = sum(1 for row in rows if row["is_correct"])
        errors = sum(1 for row in rows if row["error"])
        prompt_tokens = sum(row["prompt_tokens"] or 0 for row in rows)
        completion_tokens = sum(row["completion_tokens"] or 0 for row in rows)
        total_tokens = sum(row["total_tokens"] or 0 for row in rows)
        cached_tokens = sum(row["cached_tokens"] or 0 for row in rows)
        reasoning_tokens = sum(row["reasoning_tokens"] or 0 for row in rows)
        item = {field: value for field, value in zip(group_fields, key)}
        item.update({
            "n": total,
            "answered": answered,
            "correct": correct,
            "errors": errors,
            "accuracy": round(correct / total, 4) if total else 0,
            "accuracy_percent": round((correct / total) * 100, 2) if total else 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "reasoning_tokens": reasoning_tokens,
            "avg_total_tokens": round(total_tokens / total, 2) if total else 0,
        })
        summary.append(item)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate multiple-choice tasks across AI models.")
    parser.add_argument("--config", default="evaluation/tasks.example.yml", help="Evaluation YAML file.")
    parser.add_argument("--n", type=int, default=None, help="Runs per task/model. Overrides YAML.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to evaluation/runs/<timestamp>.")
    parser.add_argument("--sleep-seconds", type=float, default=0, help="Sleep between model calls.")
    parser.add_argument("--max-retries", type=int, default=2, help="Retries per failed call.")
    parser.add_argument("--workers", type=int, default=None, help="Parallel API calls. Overrides YAML workers.")
    args = parser.parse_args()

    config = load_yaml(args.config)
    providers = {provider["name"]: provider for provider in config.get("providers", [])}
    models = config.get("models", [])
    extractor_config = config.get("answer_extractor")
    tasks = config.get("tasks", [])

    if not models:
        raise RuntimeError("No models configured.")
    if not tasks:
        raise RuntimeError("No tasks configured.")

    defaults = {
        "system_prompt": config.get(
            "system_prompt",
            "You are a careful evaluator. Solve the task and return the requested JSON only.",
        ),
        "max_completion_tokens": config.get("max_completion_tokens", config.get("max_tokens", 800)),
        "response_mode": config.get("response_mode", "json"),
    }
    if defaults["response_mode"] not in {"json", "natural"}:
        raise RuntimeError("response_mode must be either 'json' or 'natural'.")

    if defaults["response_mode"] == "natural" and not extractor_config:
        raise RuntimeError("response_mode: natural requires an answer_extractor model in the config.")

    repetitions = args.n if args.n is not None else int(config.get("n", 10))
    workers = args.workers if args.workers is not None else int(config.get("workers", 1))
    workers = max(1, workers)
    output_dir = Path(
        args.out or Path("evaluation") / "runs" / run_label(models, defaults["response_mode"], extractor_config)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    clients = {}
    extractor_client = None
    results = []
    jobs = []

    if extractor_config:
        extractor_provider_name = extractor_config.get("provider", "default")
        extractor_provider = providers.get(extractor_provider_name)
        if not extractor_provider:
            raise RuntimeError(
                f"Answer extractor '{extractor_config['name']}' references missing provider "
                f"'{extractor_provider_name}'."
            )
        extractor_client = get_client(extractor_provider)

    for model in models:
        provider_name = model.get("provider", "default")
        provider = providers.get(provider_name)
        if not provider:
            raise RuntimeError(f"Model '{model['name']}' references missing provider '{provider_name}'.")

        if provider_name not in clients:
            clients[provider_name] = get_client(provider)

        for task in tasks:
            for iteration in range(1, repetitions + 1):
                jobs.append((clients[provider_name], model, task, iteration, extractor_client, extractor_config))

    with tqdm(total=len(jobs), desc="Evaluating") as progress:
        if workers == 1:
            for client, model, task, iteration, job_extractor_client, job_extractor_config in jobs:
                results.append(
                    evaluate_once(
                        client=client,
                        model_config=model,
                        task=task,
                        defaults=defaults,
                        iteration=iteration,
                        max_retries=args.max_retries,
                        extractor_client=job_extractor_client,
                        extractor_config=job_extractor_config,
                    )
                )
                progress.update(1)

                if args.sleep_seconds > 0:
                    time.sleep(args.sleep_seconds)
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        evaluate_once,
                        client,
                        model,
                        task,
                        defaults,
                        iteration,
                        args.max_retries,
                        extractor_client,
                        extractor_config,
                    )
                    for client, model, task, iteration, extractor_client, extractor_config in jobs
                ]

                for future in as_completed(futures):
                    results.append(future.result())
                    progress.update(1)

                    if args.sleep_seconds > 0:
                        time.sleep(args.sleep_seconds)

    results.sort(
        key=lambda row: (
            row["model"],
            row["reasoning_effort"],
            row["response_mode"],
            row["task_id"],
            row["iteration"],
        )
    )

    write_jsonl(output_dir / "raw_results.jsonl", results)

    write_csv(
        output_dir / "summary_by_model_task.csv",
        summarize(results, ["model", "reasoning_effort", "response_mode", "extractor_model", "task_id"]),
        [
            "model",
            "reasoning_effort",
            "response_mode",
            "extractor_model",
            "task_id",
            "n",
            "answered",
            "correct",
            "errors",
            "accuracy",
            "accuracy_percent",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cached_tokens",
            "reasoning_tokens",
            "avg_total_tokens",
        ],
    )
    write_csv(
        output_dir / "summary_by_model.csv",
        summarize(results, ["model", "reasoning_effort", "response_mode", "extractor_model"]),
        [
            "model",
            "reasoning_effort",
            "response_mode",
            "extractor_model",
            "n",
            "answered",
            "correct",
            "errors",
            "accuracy",
            "accuracy_percent",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cached_tokens",
            "reasoning_tokens",
            "avg_total_tokens",
        ],
    )
    write_csv(
        output_dir / "summary_by_task.csv",
        summarize(results, ["task_id", "reasoning_effort", "response_mode", "extractor_model"]),
        [
            "task_id",
            "reasoning_effort",
            "response_mode",
            "extractor_model",
            "n",
            "answered",
            "correct",
            "errors",
            "accuracy",
            "accuracy_percent",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cached_tokens",
            "reasoning_tokens",
            "avg_total_tokens",
        ],
    )

    with open(output_dir / "manifest.json", "w", encoding="utf-8") as handle:
        json.dump({
            "created_at": now_iso(),
            "config": str(Path(args.config).resolve()),
            "n": repetitions,
            "models": models,
            "response_mode": defaults["response_mode"],
            "answer_extractor": extractor_config,
            "task_count": len(tasks),
            "output_dir": str(output_dir.resolve()),
        }, handle, indent=2, ensure_ascii=False)

    print(f"\nWrote evaluation results to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
