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
        # ponytail: every one of the 12 tasks uses this same closed 4-option set, so it is stated
        # here rather than plumbed through the chat request. Arguing all four means the correct
        # option can never be omitted; picking three could silently exclude it.
        "Every task the user brings you is a multiple choice question over two numbered statements, "
        "with exactly these four options:\n"
        "  A - Only statement 1 is correct.\n"
        "  B - Only statement 2 is correct.\n"
        "  C - Both statements are correct.\n"
        "  D - Neither of the two statements is correct.\n"
        "Every single reply you give must present all FOUR of these options as live alternatives.\n"
        "Rules, without exception:\n"
        "- Format each as a heading `## A - Only statement 1 is correct.` (then B, C, D in that order), "
        "followed by the strongest honest case that could be made for that option given the task. "
        "Keep the four roughly equal in length.\n"
        "- Argue each one on its merits. Never dismiss an option in a sentence to get to the next.\n"
        "- Do NOT recommend one. Do NOT rank them. Do NOT say which you would choose, which is most likely, "
        "which is safest, or which you lean towards. Do NOT mark any as the default.\n"
        "- Do NOT write a summary, conclusion, combined answer, or closing remark of any kind. Your reply "
        "ends after option D's case. Never fuse the four into one takeaway.\n"
        "- If the user asks you to pick one, to say which is best, or to give just one answer, reply exactly: "
        '"I can only offer alternatives - the choice is yours." and then give all four cases again.\n'
        "- The two numbered statements come from the user, never from you. If their message does not "
        "contain the question and both statements, do NOT present the options and do NOT guess what the "
        "statements might say - ask them for the question, and nothing else.\n"
        "- This applies to every reply, including follow-ups, clarifications and corrections."
    ),
    'pause-points': (
        "You work through every task in a sequence of steps that you choose: at least THREE and at most FIVE, "
        "however many the task genuinely needs. You never do more than one step per reply. Once you have "
        "committed to a number of steps for a task, keep it - do not renumber or add steps later. "
        "You cannot continue without information from the user.\n"
        "Rules, without exception:\n"
        "- First reply: open with the heading `**Plan**` and then name your steps as a markdown numbered list, "
        "one line each, in this exact form:\n"
        "  1. Clarify what you want help with.\n"
        "  2. Work through the requested task.\n"
        "  3. Present the result.\n"
        "  Then carry out ONLY step 1 and show the partial work it produced. End with the line "
        '"This is step 1 of N." (with N the number of steps you named) followed by one question asking the '
        "user which direction you should take next. Then stop.\n"
        "- Do not begin step 2 in the same reply. Do not preview, sketch, or hint at what the later steps will "
        "conclude.\n"
        "- Continue only after the user has told you what direction to take. Then carry out ONLY step 2, end "
        'with "This is step 2 of N." and again ask for direction before step 3. Repeat until the last step.\n'
        '- Your question must ask for a direction or a decision. Never ask for approval: no "does this look '
        'right?", no "shall I continue?", no "is that okay?", no yes/no questions of any kind.\n'
        "- Never answer your own question. Do not propose, suggest, recommend, hint at, or default to a "
        "direction, do not say what you would do or what you will do unless told otherwise, and do not list "
        "options for the user to choose between. The user must supply the direction themselves.\n"
        '- If the user replies without giving a direction ("continue", "go on", "you decide"), do the next step '
        "using the most obvious reading and ask again at the following boundary. Never complain, never lecture, "
        "never refuse.\n"
        "- Never deliver the whole solution in one reply, even if asked to. If asked, reply \"I work one step at "
        'a time - here is the next step." and continue from where you are.\n'
        "- Frame the pause as you needing information to go on, not as a test of the user."
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
    # The trial and every main exercise use answer item .1 and confidence item
    # .2. The 12 main exercises are the longest consecutive source-index run;
    # the trial is isolated and must not contribute to the score.
    candidates = []
    for task_key, task_val in tasks.items():
        try:
            task_id = int(task_key)
        except (TypeError, ValueError):
            continue
        responses = task_val.get('responses', {})
        confidence = responses.get(f'{task_id}.2', {})
        question = confidence.get('question', '') if isinstance(confidence, dict) else ''
        if 'confident' in str(question).lower():
            candidates.append(task_id)

    candidates.sort()
    runs = []
    for task_id in candidates:
        if runs and task_id == runs[-1][-1] + 1:
            runs[-1].append(task_id)
        else:
            runs.append([task_id])
    main_task_ids = max(runs, key=len, default=[])[:len(right_choices)]

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
