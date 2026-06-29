import argparse
import json
from pathlib import Path

import yaml


def iter_wrong_rows(raw_results_path, task_id):
    with open(raw_results_path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

            if row.get("task_id") != task_id:
                continue
            if row.get("is_correct") is not False:
                continue

            yield row


def task_from_config(tasks_config, task_id):
    try:
        with open(tasks_config, "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return None

    for task in config.get("tasks", []):
        if task.get("id") == task_id:
            return task

    return None


def default_tasks_configs(raw_results_path):
    raw_results_path = Path(raw_results_path)
    candidates = []
    manifest_path = raw_results_path.parent / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            config_path = manifest.get("config")
            if config_path and Path(config_path).exists():
                candidates.append(Path(config_path))
        except (json.JSONDecodeError, OSError):
            pass

    repo_default = Path("evaluation") / "tasks.example.yml"
    if repo_default.exists():
        candidates.append(repo_default)

    script_default = Path(__file__).resolve().parent / "tasks.example.yml"
    if script_default.exists():
        candidates.append(script_default)

    candidates.extend(sorted(Path(__file__).resolve().parent.glob("*.yml")))
    candidates.extend(sorted(Path(__file__).resolve().parent.glob("*.yaml")))

    deduped = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            deduped.append(candidate)
            seen.add(resolved)

    return deduped


def load_task(tasks_config, task_id):
    if not tasks_config:
        return None

    if isinstance(tasks_config, (str, Path)):
        tasks_config = [Path(tasks_config)]

    for candidate in tasks_config:
        task = task_from_config(candidate, task_id)
        if task:
            return task

    return None


def format_task(task, task_id, correct_answer):
    if not task:
        return (
            f"Task ID: {task_id}\n"
            f"Correct answer: {correct_answer or 'unknown'}\n"
        )

    option_lines = "\n".join(
        f"{key}. {value}" for key, value in (task.get("options") or {}).items()
    )
    return f"""Task ID: {task_id}

Context:
{str(task.get("context", "")).strip()}

Question:
{str(task.get("question", "")).strip()}

Answer choices:
{option_lines}

Correct answer: {correct_answer or task.get("correct") or "unknown"}"""


def format_responses(rows, plain=False):
    responses = [
        (row.get("response_text") or "").strip()
        for row in rows
        if (row.get("response_text") or "").strip()
    ]

    if plain:
        return "\n\n".join(responses)

    chunks = []
    for index, response in enumerate(responses, start=1):
        chunks.append(f"--- response {index} ---\n{response}")
    return "\n\n".join(chunks)


def main():
    parser = argparse.ArgumentParser(
        description="Extract model responses for a specific task where the answer was wrong."
    )
    parser.add_argument("raw_results", help="Path to raw_results.jsonl.")
    parser.add_argument("--task-id", required=True, help="Task ID to filter, for example future_days_01.")
    parser.add_argument(
        "--tasks-config",
        default=None,
        help="Path to tasks YAML. Defaults to the run manifest config, then nearby YAML files.",
    )
    parser.add_argument(
        "--responses-only",
        action="store_true",
        help="Output only wrong responses, without task context and correct answer.",
    )
    parser.add_argument("--out", default=None, help="Optional text file to write responses to.")
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Print only responses separated by blank lines, without response headers.",
    )
    args = parser.parse_args()

    rows = list(iter_wrong_rows(args.raw_results, args.task_id))
    correct_answer = next((row.get("correct_answer") for row in rows if row.get("correct_answer")), None)
    responses = format_responses(rows, plain=args.plain)

    if args.responses_only:
        output = responses
    else:
        tasks_config = Path(args.tasks_config) if args.tasks_config else default_tasks_configs(args.raw_results)
        task = load_task(tasks_config, args.task_id)
        output = (
            "Please analyze why the following model responses answered this task incorrectly.\n\n"
            f"{format_task(task, args.task_id, correct_answer)}\n\n"
            "Wrong model responses:\n"
            f"{responses}"
        )

    if args.out:
        output_path = Path(args.out)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
