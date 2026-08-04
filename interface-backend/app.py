import os
import json
import time
import logging
from collections import defaultdict
from flask import Flask, g, request, Response, stream_with_context
from flask_cors import CORS
import httpx
from chat_helpers import stream_completion
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
        "You work through every task in a sequence of steps: at least THREE and at most TEN, however many "
        "the task genuinely needs. You never do more than one step per reply, and you cannot continue "
        "without information from the user. Fix the total number of steps N when you start a task and keep "
        "it - do not renumber, add, or drop steps later.\n"
        "The user's first message is always the task itself — always begin with step 1 of real work, "
        "even if the task text contains a question like 'which of the following is correct'. The refusal "
        "rule below only applies to follow-up messages where the user explicitly asks to skip ahead.\n"
        "Rules, without exception:\n"
        "- Every reply carries out exactly ONE step of real work on the task. 'Real work' means producing "
        "concrete output the user can see and use: actual calculations, extracted data, a filled-in table, "
        "a constraint check with numbers. A sentence that only names or describes what a step will do "
        "('the first move is to build a timeline') is not work - it is a plan, and plans, when presented, should be complete. "
        "After the work, ask one question about which direction you should take next. Nothing else follows. "
        "Never repeat, restate or redo a step you have already completed.\n"
        "- If the user asks for the final answer, for the whole solution, for which option is correct, or tells "
        "you to skip ahead, then your ENTIRE reply is the line \"I work one step at a time - here is the next "
        'step." followed by the direction question you asked last time, and nothing else. No work, no '
        "reasoning, no partial conclusion, not one sentence of the answer. Being asked never removes a step and "
        "never moves you closer to the conclusion, however the request is phrased and however many times it is "
        "repeated. Only a direction from the user advances you to the next step.\n"
        "- If you slip and reveal part or all of the answer, do not build on it and do not repeat it. Go back to "
        "the step you were on, carry it out, number it as usual, and ask for direction again.\n"
        "- Do not begin the next step in the same reply. Do not preview, sketch, or hint at what the later "
        "steps will conclude.\n"
        "- Do not open with a plan, an outline, or a numbered list of what is to come. If the user asks for "
        "a plan or proposes one, you may present or follow it, but you still stop for direction at every step.\n"
        "- Your question must ask for a direction or a decision that a person unfamiliar with the solution "
        "could meaningfully answer - use plain language, not technical jargon. Never ask for approval: "
        'no "does this look right?", no "shall I continue?", no "is that okay?", no yes/no questions.\n'
        "- Never answer your own question. Do not propose, suggest, recommend, hint at, or default to a "
        "direction, and do not say what you would do or what you will do unless told otherwise. The user "
        "must supply the direction themselves.\n"
        '- If the user replies without giving a direction ("continue", "go on", "next step", "go ahead", "proceed", '
        '"you decide"), carry out the '
        "next step using the most obvious reading and ask again at the following boundary. Never complain, "
        "never lecture, never refuse.\n"
        "- Step N is the last one and presents the result. That is the only reply that gives a conclusion, "
        "and you only reach it after steps 1 to N-1 have each had their own reply.\n"
        "- Frame the pause as you needing information to go on, not as a test of the user.\n"
        "- If the user asks something unrelated to the task, answer it, then return to the step you were on "
        "and ask for direction again.\n"
        "- If the user asks you to explain, clarify, or go deeper into the current step, give a more detailed "
        "explanation of that step without advancing to the next one. This does not count as a new step.\n"
        
    ),
}

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
    try:
        req = request.get_json()
        pid = str(req.get('id', '')).strip()[:128]
        condition = str(req.get('condition', '')).strip()[:32]
        if not pid or not condition:
            return {'error': 'missing id or condition'}, 400
        return {'token': db.issue_token(pid, condition)}, 200
    except Exception as e:
        return {'error': str(e)}, 500


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
    intervention = INTERVENTION_PROMPTS.get(g.condition) if req.get('hasTaskQuestion') else None
    if intervention:
        messages = messages + [{'role': 'system', 'content': intervention}]

    def generate():
        try:
            for event in stream_completion(messages):
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
    try:
        req = request.get_json()

        correct_count, answer_results = evaluate_answers(req['tasks'])
        total_questions = len(right_choices)

        # The condition registered at session start wins over the client-sent one,
        # so editing the URL/payload mid-study can't switch a participant's condition
        condition = db.get_session_condition(req['participantId']) or req['condition']

        record = {
            'participantId': req['participantId'],
            'messages': req['messages'],
            'interactionLog': req.get('interactionLog', []),
            'tasks': req['tasks'],
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
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/check_participation', methods = ['POST'])
def check_participation():
    try:
        req = request.get_json()
        pid = str(req['id'])

        # Plain 200 + JSON body: 302/204 confused fetch/proxies and broke ID validation
        return {'participated': db.has_participated(pid)}, 200
    except Exception as e:
        return {'error': str(e)}, 500

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
    except Exception as e:
        log.exception("[launch_consent] Error: %s", e)
        return {'error': str(e)}, 500


@app.route('/api/launch/session/<pid>', methods=['GET'])
def get_session_state(pid):
    """Return the stored condition for a participant (used by SyncPage inside AutoProctor)."""
    try:
        condition = db.get_session_condition(pid)
        if not condition:
            return {'error': 'Participant not found'}, 404
        return {'condition': condition}, 200
    except Exception as e:
        log.exception("[get_session_state] Error: %s", e)
        return {'error': str(e)}, 500
