import os
import json
import time
from collections import defaultdict
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from chat_helpers import get_completion, stream_completion
from correct_answers import right_choices
from config_loader import load_config
import db

config = load_config()
prolific_code = config.get('completion_code', 'COMPLETE')
prolific_url = config.get('completion_url', '')

db.init()

app = Flask(__name__)

CORS(app, origins=os.environ.get('ALLOWED_ORIGIN', '*'))

# ponytail: per-worker in-memory rate limit, Redis/DB if cross-worker sharing needed
_rate = defaultdict(list)
_RATE_LIMIT = 30
_RATE_WINDOW = 300  # 5 minutes

@app.before_request
def _rate_limit_chat():
    if not request.path.startswith('/chat'):
        return
    # Behind Railway's proxy remote_addr is a rotating proxy IP; the real client
    # is the LAST X-Forwarded-For entry (appended by the trusted edge, not spoofable)
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[-1].strip() if xff else request.remote_addr
    now = time.time()
    hits = _rate[ip] = [t for t in _rate[ip] if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_LIMIT:
        return {'error': 'rate limit exceeded'}, 429
    hits.append(now)


@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/chat', methods = ['POST'])
def send_message():
    try:
        req = request.get_json()
        messages = req['messages']

        result = get_completion(messages)
        return {'response': result}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/chat/stream', methods = ['POST'])
def stream_message():
    req = request.get_json()
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

        record = {
            'participantId': req['participantId'],
            'messages': req['messages'],
            'tasks': req['tasks'],
            'condition': req['condition'],
            'studyId': req.get('studyId', ''),
            'sessionId': req.get('sessionId', ''),
            'correctAnswers': correct_count,
            'totalQuestions': total_questions,
            'answerResults': answer_results
        }

        db.save_participant(req['participantId'], req['condition'], record)

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

        if db.has_participated(pid):
            return {'participated': True}, 302

        return {'participated': False}, 204
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/export')
def export_data():
    # Set export_token in study.config.yml (or EXPORT_TOKEN env var) to enable this endpoint
    token = os.environ.get('EXPORT_TOKEN') or config.get('export_token')
    if not token or request.args.get('token') != token:
        return {'error': 'unauthorized'}, 403
    return {'participants': db.fetch_all()}, 200
