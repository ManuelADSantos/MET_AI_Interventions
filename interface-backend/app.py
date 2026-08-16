import os
import json
import time
import logging
from collections import defaultdict
from flask import Flask, g, request, Response, stream_with_context
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import httpx
from chat_helpers import stream_completion, use_responses_api
from correct_answers import right_choices
from config_loader import load_config
import db

log = logging.getLogger(__name__)

config = load_config()
prolific_code = config.get('completion_code', 'COMPLETE')
prolific_url = config.get('completion_url', '')

db.init()

app = Flask(__name__)

CORS(app, origins=os.environ.get('ALLOWED_ORIGIN', '*'))

# ponytail: per-worker in-memory rate limit, Redis/DB if cross-worker sharing needed
_rate = defaultdict(list)
_RATE_WINDOW = 300  # 5 minutes
_RATE_LIMITS = {'/chat': 30, '/token': 10, '/save': 10}  # per IP per window

# ponytail: one handler replaces the try/except Exception -> 500 that every route below repeated.
# HTTPExceptions (404/405, the 429 above) are re-raised so they keep their own status.
@app.errorhandler(Exception)
def _unhandled(e):
    if isinstance(e, HTTPException):
        return e
    log.exception("[%s] %s", request.path, e)
    return {'error': str(e)}, 500


@app.before_request
def _rate_limit():
    for prefix, limit in _RATE_LIMITS.items():
        if request.path.startswith(prefix):
            break
    else:
        return
    # Behind Railway's proxy remote_addr and the last X-Forwarded-For entry are rotating
    # edge IPs; X-Real-Ip is the stable client address set by the edge itself
    ip = request.headers.get('X-Real-Ip') or request.remote_addr
    now = time.time()
    hits = _rate[(ip, prefix)] = [t for t in _rate[(ip, prefix)] if now - t < _RATE_WINDOW]
    if len(hits) >= limit:
        return {'error': 'rate limit exceeded'}, 429
    hits.append(now)


# Blocks context-stuffing abuse; roomy enough for a full-study transcript plus an image or two
_MAX_CHAT_CHARS = 200_000

# ponytail: the intervention stimulus lives server-side and is keyed off the token's stored
# condition, so a participant cannot inspect or strip it from the bundle. Conditions absent
# from this dict (ai, no-ai, reflection) get the plain assistant — reflection's manipulation
# is the post-task screen, not the chat.
INTERVENTION_PROMPTS = {
    'alternatives': (
        # ponytail: the four-option set is fixed for all 12 tasks. The intervention presents alternatives
        # instead of a single answer, but allows normal discussion as long as it stays neutral.
        "The user is working on multiple-choice questions with two numbered statements and exactly "
        "four options:\n"
        "  A - Only statement 1 is correct.\n"
        "  B - Only statement 2 is correct.\n"
        "  C - Both statements are correct.\n"
        "  D - Neither of the two statements is correct.\n"
        "You must NEVER reveal, hint at, or lean towards which option you believe is correct. This "
        "is your core constraint — it applies to every reply, whether you are discussing, breaking "
        "down the task, or presenting the options.\n"
        "Rules, without exception:\n"
        "- When the user asks for the answer, asks which option is correct, or submits the full task "
        "with both statements, present all FOUR options as `## A - Only statement 1 is correct.` "
        "(then B, C, D in that order), each followed by the strongest honest case for that option. "
        "Keep the four roughly equal in length and tone. Do NOT write a summary, conclusion, or "
        "closing remark after option D.\n"
        "- When the user asks to discuss a specific part of the task, break down data, or reason "
        "through an aspect, help with that — but stay neutral. Present facts and analysis without "
        "concluding which option the analysis supports. Let the user draw their own conclusion.\n"
        "- Do NOT recommend one. Do NOT rank them. Do NOT say which you would choose, which is most "
        "likely, which is safest, or which you lean towards. Do NOT mark any as the default.\n"
        "- If the user asks you to pick one, to say which is best, or to give just one answer, reply "
        'exactly: "I can only offer alternatives - the choice is yours." and then present all four.\n'
        "- The two numbered statements come from the user, never from you. If their message does not "
        "contain the question and both statements, do NOT present the options and do NOT guess what the "
        "statements might say — ask them for the question, and nothing else.\n"
        "- If the user asks something unrelated to the current task, answer it.\n"
    ),
    'pause-points': (
        # ponytail: bullet ORDER is load-bearing. The permissive "everything is a direction" rule and the
        # "your own words quoted back" rule must both come BEFORE the holding rule. Put the hold first and
        # the model reads the strong-sounding rule as the general case, then refuses a user who merely
        # answered the question it had just asked - the recorded failure was the canned line three times
        # with no step behind it. No total is fixed up front either: the model cannot know how many steps
        # a task takes before doing it, and a pre-committed N buys padding or cramming.
        # The holding rule is deliberately scoped to "while parts are still unworked", and it may never
        # fire twice running. Unscoped, it livelocks the end of every task: once only the conclusion is
        # left, every question the model can ask is about the conclusion, so the user's answer always
        # reads as a demand for the finished answer and the hold fires for ever. The hold exists to stop
        # work being skipped, not to stop the task finishing.
        "You work through every task in a sequence of steps: one step per reply, and after each step you "
        "stop and ask the user which direction to take next. A task takes at least THREE steps and at most "
        "TEN - as many as the work genuinely needs. Never announce a total and never lay the steps out in "
        "advance; you cannot know how many there are until the work is done.\n"
        "A reply that carries out a step has exactly two parts, in this order:\n"
        "  1. the heading `**Step k**`, then one step of real work;\n"
        "  2. one question asking the user which direction to take next.\n"
        "Nothing follows that question.\n"
        "Number each step one higher than the last step you finished on the task in hand: after Step 1 "
        "comes Step 2, then Step 3. Never reuse a number and never drop back to Step 1 while the same task "
        "is still open. A reply that is not a step leaves the count exactly where it was. Only when the user "
        "brings a different task does the count start again at Step 1 - and a new question about a scenario "
        "you have already worked on is a different task, however much of the scenario is pasted again with "
        "it.\n"
        "The user's first message on a task is the task itself, never a request to skip ahead: open with "
        "Step 1 of real work even when that message says 'which of the following statements is or are "
        "correct' or asks you outright for the answer.\n"
        "Rules, without exception:\n"
        "- Every step produces real work: concrete output the user can see and use - an actual calculation, "
        "data pulled out of the scenario and organised, a filled-in table, a named constraint checked "
        "against named values. A sentence that only says what a step will do ('the first move is to build a "
        "timeline') is not work. Divide the task along its own structure, so each step settles one part of "
        "it: one case, one claim, one constraint, one piece of the data. If the task is small, divide more "
        "finely to reach three steps - never pad.\n"
        "- Work already on the page is finished work. Never produce it again in another shape: no "
        "re-tabulating the same data, no re-listing it in a tidier or more compact form, no recap of what "
        "the earlier steps established. Every step puts something on the page that was not there before. If "
        "an earlier step was wrong, say in one line what changed and carry on from where you were.\n"
        "- Your question asks the user to choose between pieces of work still to be done: which part to "
        "take next, which order to go in, how to go at the part that is left. While any part of the task is "
        "still unworked, never offer a conclusion, a verdict, or an answer as one of the choices - "
        '"shall I check whether the first statement is true?" is a verdict dressed as a choice, while '
        '"which of the two statements should I test first?" is work. '
        "Do not word the question so that it mirrors the answer options the task offers; the user is "
        "choosing what you work on, not what the answer is. Above all, never offer a choice you would then "
        "refuse to carry out: if picking it would earn the user a refusal, it does not belong in your "
        "question. "
        "Use plain language, not technical jargon. Never ask for approval: "
        'no "does this look right?", no "shall I continue?", no "is that okay?", no yes/no questions. '
        "When one piece of work is all that is left, ask how to go at it - never a question that has only "
        "one possible answer.\n"
        "- Never answer your own question. Do not propose, recommend, rank, hint at, or default to one of "
        "the choices, and do not say what you would do or what you will do unless the user has already told "
        "you. The direction has to come from them.\n"
        "- Treat whatever the user sends next as a direction and carry out the next step, unless it "
        "explicitly demands the finished answer. "
        '"Continue", "go on", "next step", "go ahead", "proceed", "you decide", a one-word reply, a part of '
        "the task named back to you, or one of the choices you just offered - every one of those is a "
        "direction. When the reply is ambiguous, take the most obvious reading and do the work. Never "
        "complain, never lecture, never refuse.\n"
        "- Words you put in the user's mouth can never be a request to skip ahead. If they pick, quote, or "
        "paraphrase one of the choices from your own question, that is a direction however it is worded - "
        "carry out that piece of work, even if you phrased the choice badly yourself.\n"
        "- While parts of the task are still unworked, a demand for the finished answer buys no work. If the "
        "user explicitly asks for the whole solution, for which option is correct, or tells you to jump to "
        "the end, your ENTIRE reply is the line "
        '"I work one step at a time, so the full answer comes at the end rather than in one go." '
        "followed by one question asking which piece of work to take next - no work, no reasoning, no "
        "partial conclusion, not one sentence of the answer. Being asked never removes a step and never "
        "moves you closer to the conclusion, however the request is worded. That reply is not a step: it "
        "carries no heading and leaves the count where it was, and its question must differ from the one "
        "you asked last time. Never do this twice running: if your previous reply was one of these, your "
        "next reply carries out work, whatever the user has said.\n"
        "- Say only what you have derived on the page. Do not preview, sketch, or hint at what the later "
        "steps will conclude, and do not begin the next step in the same reply. If you do let part of the "
        "answer out, do not repeat it and do not build on it: go back to the step you were on, carry it "
        "out, and ask for direction again.\n"
        "- Not every reply is a step. If the user asks you to explain, clarify, or go deeper on the step "
        "you have just done, do that in full and stay on that step. A small question - a definition, one "
        "fact from the scenario, something off the topic - gets a plain answer. If the task as given is "
        "missing something you need in order to do the work, ask the user for exactly that. None of these "
        "carry a step heading and none of them advance the numbering; afterwards, put your pending "
        "direction question back to the user.\n"
        "- Never open with a plan, an outline, or a list of what is to come. If the user asks for a plan, "
        "that reply's step is the plan: name the pieces of work in the order you would do them, complete, "
        "with no findings and no conclusions in it - then stop for direction as usual.\n"
        "- If the user offers their own answer, guess, or reasoning, treat it as context only. Do not "
        "confirm it, deny it, correct it, grade it, or say how close it is. Carry on with the next step.\n"
        "- Once every part of the task has been worked out on the page, and at least two earlier steps have "
        "each had a reply of their own, nothing is left but the result and the holding rule above stops "
        "applying. From that point a request for the answer, the verdict, the wrap-up or the conclusion is "
        "your cue: take the last step, give the result in full and plainly, and ask no question after it. At "
        "that boundary you may also offer the wrap-up as one of the choices in your question, because there "
        "it is the honest one - and if the user picks it, you carry it out.\n"
        "- Frame the pause as you needing a direction in order to go on, never as a test of the user. If "
        "the user signals that they think you are broken, stuck, or refusing to help, say exactly: "
        '"I am not stuck - I work through a problem a step at a time, and I stop after each one because '
        'where I go next depends on what you want to look at." '
        "Use that line at most once in a conversation, never volunteer it, and never say why you work this "
        "way.\n"
    ),
}

# ponytail: dual-column alternatives — two parallel model calls, each with its own stance or
# temperature. Keyed by column id ('a'/'b'). Falls back to the single-prompt INTERVENTION_PROMPTS
# entry when no column is sent (old frontend).
alternatives_mode = config.get('alternatives_mode', 'opposing')
if alternatives_mode not in ('opposing', 'temperature'):
    raise RuntimeError(f"alternatives_mode must be 'opposing' or 'temperature', got {alternatives_mode!r}")
# OpenAI reasoning models reject `temperature` on the Responses API, so every dual-column request
# would 400 and the condition would collect nothing. Fail at startup instead: temperature mode
# needs `reasoning_effort: none` (or a non-OpenAI base_url) so the Chat Completions path is used.
if alternatives_mode == 'temperature' and use_responses_api:
    raise RuntimeError(
        "alternatives_mode: temperature requires reasoning_effort: none — "
        "reasoning models reject the temperature parameter on the Responses API"
    )

COLUMN_PROMPTS = {
    'a': (
        "When analyzing the task, give weight to evidence that supports the statements being correct. "
        "Present your analysis naturally without revealing that you are taking a particular stance."
    ),
    'b': (
        "When analyzing the task, give weight to evidence that challenges or questions the statements. "
        "Present your analysis naturally without revealing that you are taking a particular stance."
    ),
}

COLUMN_TEMPS = {'a': 0.3, 'b': 1.0}


def _chat_denied(req):
    """Bearer-token auth + size cap for the chat endpoints. Returns an error response or None."""
    auth = request.headers.get('Authorization', '')
    g.condition = db.consume_chat(auth[7:]) if auth.startswith('Bearer ') else None
    if not g.condition:
        return {'error': 'invalid or exhausted session token'}, 401
    messages = req.get('messages') or []
    size = sum(len(str(m.get('content', ''))) + len(str(m.get('image', ''))) for m in messages)
    if len(messages) > 200 or size > _MAX_CHAT_CHARS:
        return {'error': 'request too large'}, 413
    return None


@app.route('/token', methods=['POST'])
def issue_token():
    req = request.get_json()
    pid = str(req.get('id', '')).strip()[:128]
    condition = str(req.get('condition', '')).strip()[:32]
    if not pid or not condition:
        return {'error': 'missing id or condition'}, 400
    return {'token': db.issue_token(pid, condition)}, 200


@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/chat/stream', methods = ['POST'])
def stream_message():
    req = request.get_json()
    denied = _chat_denied(req)
    if denied:
        return denied
    messages = req['messages']

    # ponytail: append (not prepend) — recency keeps the manipulation live in long chats.
    # Every intervention is gated by the question check in ChatView: prompts that do not carry the
    # task's actual question (greetings, meta questions, the scenario pasted on its own) get the
    # plain assistant. Add an ungated intervention here and you need a condition list again.
    column = req.get('column')
    temperature = None

    if column and g.condition == 'alternatives' and req.get('hasTaskQuestion'):
        # ponytail: dual-column mode — stance or temperature, never both
        if alternatives_mode == 'temperature':
            intervention, temperature = None, COLUMN_TEMPS.get(column)
        else:
            intervention = COLUMN_PROMPTS.get(column)
    else:
        intervention = INTERVENTION_PROMPTS.get(g.condition) if req.get('hasTaskQuestion') else None

    if intervention:
        messages = messages + [{'role': 'system', 'content': intervention}]

    def generate():
        try:
            for event in stream_completion(messages, temperature=temperature):
                yield json.dumps(event) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'error': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

def evaluate_answers(tasks):
    # The 12 main exercises are the pages titled "Scenario: ..." (the trial is "Trial: ..." and must
    # not contribute to the score); their answer is item .1. TaskPage sends the title with every page.
    # ponytail: the old version had to infer them as the longest consecutive run of sourceIndexes,
    # which collapsed to one task as soon as reflection pages sat between the exercises. Falls back to
    # the confidence-question heuristic for records saved before the title was sent.
    main_task_ids = []
    for task_key, task_val in tasks.items():
        try:
            task_id = int(task_key)
        except (TypeError, ValueError):
            continue
        title = str(task_val.get('title') or '')
        if title:
            if title.startswith('Scenario:'):
                main_task_ids.append(task_id)
            continue
        confidence = (task_val.get('responses') or {}).get(f'{task_id}.2', {})
        question = confidence.get('question', '') if isinstance(confidence, dict) else ''
        if 'confident' in str(question).lower():
            main_task_ids.append(task_id)

    main_task_ids.sort()
    # A legacy record includes the trial; drop it by keeping the last len(right_choices) ids
    main_task_ids = main_task_ids[-len(right_choices):]

    results = {}
    for task_id, expected_answer in zip(main_task_ids, right_choices):
        task_val = tasks.get(str(task_id), tasks.get(task_id, {}))
        responses = task_val.get('responses', {})
        resp_key = f'{task_id}.1'
        resp_val = responses.get(resp_key, {})
        answer = resp_val.get('answer') if isinstance(resp_val, dict) else resp_val
        results[resp_key] = str(answer).strip() == expected_answer

    correct = sum(results.values())
    return correct, results

@app.route('/save', methods = ['POST'])
def save_data():
    req = request.get_json()

    # ponytail: evaluate_answers must never block the save — a crash here left participants
    # staring at an infinite spinner with no completion code and no retry button
    try:
        correct_count, answer_results = evaluate_answers(req.get('tasks') or {})
    except Exception as e:
        log.error('[save] evaluate_answers failed for %s: %s', req.get('participantId'), e)
        correct_count, answer_results = 0, {}
    total_questions = len(right_choices)

    # The condition registered at session start wins over the client-sent one,
    # so editing the URL/payload mid-study can't switch a participant's condition
    condition = db.get_session_condition(req['participantId']) or req['condition']

    record = {
        'participantId': req['participantId'],
        'messages': req.get('messages', []),
        'interactionLog': req.get('interactionLog', []),
        'tasks': req.get('tasks', {}),
        'condition': condition,
        'studyId': req.get('studyId', ''),
        'sessionId': req.get('sessionId', ''),
        'correctAnswers': correct_count,
        'totalQuestions': total_questions,
        'answerResults': answer_results
    }

    db.save_participant(req['participantId'], condition, record)

    return {
        'message': 'OK',
        'prolificCode': prolific_code,
        'prolificUrl': prolific_url,
        'correctAnswers': correct_count,
        'totalQuestions': total_questions
    }, 201

@app.route('/check_participation', methods = ['POST'])
def check_participation():
    req = request.get_json()
    pid = str(req['id'])

    # Plain 200 + JSON body: 302/204 confused fetch/proxies and broke ID validation
    return {'participated': db.has_participated(pid)}, 200

@app.route('/export')
def export_data():
    # Set export_token in study.config.yml (or EXPORT_TOKEN env var) to enable this endpoint
    token = os.environ.get('EXPORT_TOKEN') or config.get('export_token')
    if not token or request.args.get('token') != token:
        return {'error': 'unauthorized'}, 403
    return {'participants': db.fetch_all()}, 200


# ── AutoProctor launch ───────────────────────────────────────────────

@app.route('/api/launch/consent', methods=['POST'])
def launch_consent():
    """Register participant session and return a unique AutoProctor URL."""
    try:
        req = request.get_json()
        pid = str(req.get('prolificPid', '')).strip()
        condition = str(req.get('condition', '')).strip()

        if not pid or not condition:
            return {'error': 'Missing prolificPid or condition'}, 400

        if db.has_participated(pid):
            return {'error': 'Participation with given ID already registered.'}, 409

        api_key = os.getenv('AUTOPROCTOR_API_KEY')
        test_label = os.getenv('AUTOPROCTOR_TEST_LABEL')
        if not api_key or not test_label:
            log.error("[launch_consent] AUTOPROCTOR_API_KEY or AUTOPROCTOR_TEST_LABEL not set")
            return {'error': 'Proctoring service is not configured on the server'}, 500

        db.create_session(pid, condition)

        pseudo_email = f"{pid}@prolific.study"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"https://www.autoproctor.co/api/v2/tests/{test_label}/generate-unique-urls/",
                headers={"Content-Type": "application/json", "X-API-Key": api_key},
                json={"emails": [pseudo_email], "loginNotRequired": True},
            )

        if resp.status_code != 200:
            log.error("[launch_consent] AutoProctor error %s: %s", resp.status_code, resp.text)
            return {'error': 'Failed to generate proctoring link'}, 502

        urls = resp.json().get('urls', [])
        if not urls:
            return {'error': 'No URL returned from proctoring service'}, 502

        return {'autoproctor_url': urls[0]}, 200

    except httpx.RequestError as e:
        log.error("[launch_consent] AutoProctor unreachable: %s", e)
        return {'error': 'Proctoring service unreachable'}, 503


@app.route('/api/launch/session/<pid>', methods=['GET'])
def get_session_state(pid):
    """Return the stored condition for a participant (used by SyncPage inside AutoProctor)."""
    condition = db.get_session_condition(pid)
    if not condition:
        return {'error': 'Participant not found'}, 404
    return {'condition': condition}, 200
