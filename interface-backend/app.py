import os
import json
import time
import logging
from collections import defaultdict
from flask import Flask, request, Response, stream_with_context
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

def _chat_denied(req):
    """Bearer-token auth + size cap for the chat endpoints. Returns an error response or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer ') or not db.consume_chat(auth[7:]):
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

    def generate():
        try:
            for event in stream_completion(messages):
                yield json.dumps(event) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'error', 'error': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

RELEVANT_KEYS = {f'{i}.1' for i in range(4, 24)}

def get_answer(resp_val):
    if isinstance(resp_val, dict):
        return resp_val.get('answer', resp_val)
    return resp_val

def evaluate_answers(tasks):
    correct = 0
    results = {}
    for task_key, task_val in tasks.items():
        responses = task_val.get('responses', {})
        for resp_key, resp_val in responses.items():
            if resp_key in RELEVANT_KEYS:
                answer = get_answer(resp_val)
                is_correct = answer in right_choices
                results[resp_key] = is_correct
                if is_correct:
                    correct += 1
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
