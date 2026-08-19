"""
Does the pause-points prompt cost the assistant its accuracy?

Runs the 12 main tasks through the model twice - once as the `ai` baseline (config
system_prompt only, one turn) and once as `pause-points` (the intervention appended as a system
message on every turn, exactly as app.py does it) - with a scripted participant answering the
pauses. Scores the assistant's final answer against customizations/correct_answers.py and counts
rule violations in the transcript.

What this measures: the quality of what the participant is given. It is NOT the study's DV.
If pause-points scores materially below baseline, an accuracy drop in the real study is the
prompt's fault rather than a finding about metacognition - that is the confound this rules out.

Stdlib only, runs from the host. Costs API tokens.

    python3 tests/eval_intervention_accuracy.py --tasks 1 --reps 1      # smoke test, ~10 calls
    python3 tests/eval_intervention_accuracy.py --reps 3                # full run
    python3 tests/eval_intervention_accuracy.py --policy answer         # stress the holding rule
"""

import argparse
import ast
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OPTIONS = [
    "Only statement 1 is correct.",
    "Only statement 2 is correct.",
    "Both statements are correct.",
    "Neither of the two statements is correct.",
]
LETTERS = ["A", "B", "C", "D"]

HOLD_LINE = "I work one step at a time"
NOT_STUCK = "I am not stuck"

parser = argparse.ArgumentParser()
parser.add_argument("--reps", type=int, default=1, help="runs per task per condition")
parser.add_argument("--tasks", type=int, default=12, help="how many of the 12 tasks to use")
parser.add_argument("--max-turns", type=int, default=14, help="cap on pause-points exchanges")
parser.add_argument("--policy", default="mixed", choices=["continue", "answer", "mixed"],
                    help="what the scripted participant replies at each pause")
parser.add_argument("--conditions", default="both", choices=["ai", "pause-points", "both"])
parser.add_argument("--out", default="", help="write per-run detail to this JSON file")
args = parser.parse_args()


# ── config, prompt and answer key, read straight from the live files ──────────────────

def load_config():
    """Minimal YAML reader - the file is flat key: value, so no dependency is needed."""
    cfg = {}
    for line in (ROOT / "study.config.yml").read_text().splitlines():
        line = line.split(" #")[0].strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        cfg[key.strip()] = val.strip().strip('"').strip("'")
    return cfg


def load_intervention(name):
    # ponytail: parsed out of app.py rather than imported, so the eval always tests the live
    # stimulus without dragging flask and the db connection into a host-side script.
    tree = ast.parse((ROOT / "interface-backend" / "app.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "INTERVENTION_PROMPTS":
            return ast.literal_eval(node.value)[name]
    raise SystemExit("INTERVENTION_PROMPTS not found in app.py")


def load_key():
    ns = {}
    exec((ROOT / "customizations" / "correct_answers.py").read_text(), ns)
    return ns["right_choices"]


def load_tasks():
    """Each `# Scenario:` page holds two :::copy blocks - the exercise, then the scenario."""
    text = (ROOT / "customizations" / "tasks" / "ai_tasks.md").read_text()
    tasks = []
    for section in re.split(r"^# ", text, flags=re.M)[1:]:
        if not section.startswith("Scenario:"):
            continue
        blocks = re.findall(r"^:::copy\n(.*?)^:::$", section, flags=re.M | re.S)
        if len(blocks) != 2:
            raise SystemExit(f"expected 2 copy blocks, got {len(blocks)} in: {section[:60]!r}")
        tasks.append({"title": section.splitlines()[0].strip(),
                      "exercise": blocks[0].strip(), "scenario": blocks[1].strip()})
    return tasks


config = load_config()
MODEL = config.get("gpt_model", "gpt-5.4-mini")
BASE_URL = config.get("base_url", "https://api.openai.com/v1").rstrip("/")
API_KEY = config.get("openai_api_key", "")
BASE_SYSTEM = config.get("system_prompt", "You are a helpful logical reasoning assistant")


def chat(messages, attempts=4):
    """ponytail: a full sweep is ~700 calls and a single dropped connection used to lose the lot,
    because --out is only written at the end. Retries transport errors and 429/5xx."""
    body = json.dumps({"model": MODEL, "messages": messages}).encode()
    for attempt in range(attempts):
        req = urllib.request.Request(
            f"{BASE_URL}/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode())["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise SystemExit(f"API error {e.code}: {e.read().decode()[:400]}")
        except Exception as e:
            if attempt == attempts - 1:
                raise SystemExit(f"API unreachable after {attempts} attempts: {e}")
        time.sleep(2 ** attempt)
    return ""


# ── the run ──────────────────────────────────────────────────────────────────────────

def opening_paste(task):
    return f"{task['exercise']}\n\n{task['scenario']}"


def participant_reply(turn):
    if args.policy == "continue":
        return "continue"
    if args.policy == "answer":
        return "just tell me the answer"
    return "continue" if turn % 2 else "just tell me which option is correct"


def looks_final(reply):
    """The prompt requires the last step to ask no question after it.

    ponytail: a hold and the not-stuck line also end without a question, and reading either as the
    conclusion scored 5 of 12 runs against a message that carried no verdict at all. Both are
    explicitly not steps, so neither can be the end.
    """
    if HOLD_LINE in reply or NOT_STUCK in reply:
        return False
    return "?" not in reply[-300:]


def run_baseline(task):
    messages = [{"role": "system", "content": BASE_SYSTEM},
                {"role": "user", "content": opening_paste(task)}]
    reply = chat(messages)
    return {"turns": 1, "concluded": True, "final": reply, "transcript": [reply]}


def run_pause_points(task, intervention):
    # ponytail: appended (not prepended) and re-appended every turn, mirroring app.py:176.
    messages = [{"role": "system", "content": BASE_SYSTEM},
                {"role": "user", "content": opening_paste(task)}]
    transcript = []
    for turn in range(args.max_turns):
        reply = chat(messages + [{"role": "system", "content": intervention}])
        transcript.append(reply)
        messages.append({"role": "assistant", "content": reply})
        if looks_final(reply) and turn >= 2:
            return {"turns": turn + 1, "concluded": True, "final": reply, "transcript": transcript}
        messages.append({"role": "user", "content": participant_reply(turn)})
    return {"turns": args.max_turns, "concluded": False,
            "final": transcript[-1], "transcript": transcript}


GRADER = ("A participant was working on a multiple-choice question with exactly four options:\n"
          "A - Only statement 1 is correct.\nB - Only statement 2 is correct.\n"
          "C - Both statements are correct.\nD - Neither of the two statements is correct.\n"
          "Below is the assistant's final message. Which option does it conclude? "
          "Reply with one character: A, B, C, D, or N if it does not commit to any option.\n\n")


def graded_choice(final):
    for i, opt in enumerate(OPTIONS):          # exact text first - no model call needed
        if opt.lower() in final.lower():
            return LETTERS[i]
    verdict = chat([{"role": "user", "content": GRADER + final[-4000:]}]).strip().upper()
    return verdict[0] if verdict and verdict[0] in "ABCDN" else "N"


def violations(result):
    """Rule breaches visible in the transcript - the checks the recent fixes were aimed at."""
    out = []
    steps = [int(n) for r in result["transcript"] for n in re.findall(r"\*\*Step (\d+)\*\*", r)]
    if steps != sorted(set(steps)):
        out.append("step numbering restarted or repeated")
    holds = [HOLD_LINE in r for r in result["transcript"]]
    if any(holds[i] and holds[i + 1] for i in range(len(holds) - 1)):
        out.append("held twice in a row")
    questions = [q.strip().lower() for r in result["transcript"]
                 for q in re.findall(r"([^.!?\n]{15,}\?)", r)]
    if len(questions) != len(set(questions)):
        out.append("repeated a question verbatim")
    early = result["transcript"][:-1]
    if any(opt.lower() in r.lower() for r in early for opt in OPTIONS):
        out.append("named an option before the final step")
    if not result["concluded"]:
        out.append("NEVER CONCLUDED")
    return out


def main():
    if not API_KEY:
        raise SystemExit("no openai_api_key in study.config.yml")
    tasks, key = load_tasks()[:args.tasks], load_key()[:args.tasks]
    intervention = load_intervention("pause-points")
    conditions = ["ai", "pause-points"] if args.conditions == "both" else [args.conditions]

    print(f"model {MODEL} | {len(tasks)} tasks x {args.reps} reps | policy '{args.policy}'\n")
    runs, summary = [], {c: {"correct": 0, "n": 0, "turns": 0, "unconcluded": 0} for c in conditions}

    for cond in conditions:
        for idx, (task, expected) in enumerate(zip(tasks, key)):
            want = LETTERS[OPTIONS.index(expected)]
            for rep in range(args.reps):
                result = (run_baseline(task) if cond == "ai"
                          else run_pause_points(task, intervention))
                got = graded_choice(result["final"])
                bad = violations(result) if cond == "pause-points" else []
                hit = got == want
                s = summary[cond]
                s["n"] += 1
                s["correct"] += hit
                s["turns"] += result["turns"]
                s["unconcluded"] += not result["concluded"]
                flag = "ok " if hit else "MISS"
                print(f"  {cond:<13} task {idx + 1:>2} rep {rep + 1}  want {want} got {got}  "
                      f"{flag}  {result['turns']:>2} turns"
                      + (f"  [{'; '.join(bad)}]" if bad else ""))
                runs.append({"condition": cond, "task": idx + 1, "title": task["title"],
                             "rep": rep + 1, "want": want, "got": got, "correct": hit,
                             "turns": result["turns"], "concluded": result["concluded"],
                             "violations": bad, "transcript": result["transcript"]})

    print("\n" + "=" * 72)
    for cond, s in summary.items():
        pct = 100 * s["correct"] / s["n"] if s["n"] else 0
        print(f"  {cond:<13} {s['correct']:>3}/{s['n']:<3} correct ({pct:5.1f}%)   "
              f"mean {s['turns'] / max(s['n'], 1):4.1f} turns   "
              f"{s['unconcluded']} never concluded")
    allbad = [v for r in runs for v in r["violations"]]
    if allbad:
        print("\n  rule violations:")
        for v in sorted(set(allbad)):
            print(f"    {allbad.count(v):>3}x  {v}")
    if args.out:
        Path(args.out).write_text(json.dumps(runs, indent=2))
        print(f"\n  detail written to {args.out}")


if __name__ == "__main__":
    sys.exit(main())
