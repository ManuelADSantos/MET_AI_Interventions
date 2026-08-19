from openai import OpenAI
from config_loader import load_config

config = load_config()
oai_key = config['openai_api_key']
gpt_model = config['gpt_model']
reasoning_effort = str(config.get('reasoning_effort') or '').strip().lower()

api_base_url = config.get('base_url')

client_kwargs = {'api_key': oai_key}
if api_base_url:
    client_kwargs['base_url'] = api_base_url
gpt_client = OpenAI(**client_kwargs)
reasoning_enabled = reasoning_effort and reasoning_effort not in ('none', 'off')
use_responses_api = reasoning_enabled and (not api_base_url or 'api.openai.com' in api_base_url)
chat_request_options = {'reasoning_effort': reasoning_effort} if reasoning_enabled and not use_responses_api else {}
responses_request_options = {'reasoning': {'effort': reasoning_effort, 'summary': 'auto'}} if use_responses_api else {}

# ponytail: consolidated from format_messages + format_responses_input
def _format_input(messages, responses_api=False):
    def _msg(m):
        if 'image' not in m:
            return {'role': str(m['role']), 'content': str(m['content'])}
        txt_t = 'input_text' if responses_api else 'text'
        url = str(m['image'])
        img = ({'type': 'input_image', 'image_url': url, 'detail': 'low'} if responses_api
               else {'type': 'image_url', 'image_url': {'url': url, 'detail': 'low'}})
        return {'role': str(m['role']), 'content': [{'type': txt_t, 'text': str(m['content'])}, img]}
    return [_msg(m) for m in messages]

def response_reasoning(response_data):
    return '\n'.join(
        summary.get('text', '')
        for item in response_data.get('output', [])
        if item.get('type') == 'reasoning'
        for summary in item.get('summary', [])
    ).strip()

def response_text(response_data):
    return ''.join(
        part.get('text', '')
        for item in response_data.get('output', [])
        if item.get('type') == 'message'
        for part in item.get('content', [])
        if part.get('type') == 'output_text'
    )

def as_chat_response(response = None, content = None, reasoning = None):
    response_data = response.model_dump() if response else {}
    content = content if content is not None else getattr(response, 'output_text', '') or response_text(response_data)
    reasoning = reasoning if reasoning is not None else response_reasoning(response_data)
    return {
        'id': response_data.get('id'),
        'object': 'chat.completion',
        'created': response_data.get('created_at'),
        'model': response_data.get('model') or str(gpt_model),
        'choices': [
            {
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': content,
                    **({'reasoning': reasoning} if reasoning else {})
                },
                'finish_reason': response_data.get('status') or 'stop'
            }
        ],
        'usage': response_data.get('usage')
    }

def stream_completion(messages, temperature=None):
    # ponytail: temperature override for the dual-column alternatives mode. Chat Completions only —
    # reasoning models reject it on the Responses API, which app.py refuses to start with.
    temp_kw = {'temperature': temperature} if temperature is not None else {}
    try:
        if use_responses_api:
            stream = gpt_client.responses.create(
                model = str(gpt_model),
                input = _format_input(messages, responses_api=True),
                stream = True,
                **responses_request_options
            )

            content = ''
            reasoning = ''
            final_response = None

            for event in stream:
                event_data = event.model_dump()
                event_type = event_data.get('type')

                if event_type in ('response.reasoning_summary_text.delta', 'response.reasoning_text.delta'):
                    reasoning += event_data.get('delta') or ''
                    yield {
                        'type': 'reasoning',
                        'delta': event_data.get('delta') or '',
                        'reasoning': reasoning
                    }

                if event_type == 'response.output_text.delta':
                    content += event_data.get('delta') or ''
                    yield {
                        'type': 'delta',
                        'delta': event_data.get('delta') or '',
                        'content': content
                    }

                if event_type == 'response.completed':
                    final_response = event.response

            yield {
                'type': 'done',
                'response': as_chat_response(final_response, content, reasoning or None)
            }
            return

        stream = gpt_client.chat.completions.create(
            model = str(gpt_model),
            messages = _format_input(messages),
            stream = True,
            **temp_kw,
            **chat_request_options
        )

        content = ''
        reasoning = ''
        response_meta = {}
        finish_reason = None

        for chunk in stream:
            chunk_data = chunk.model_dump()
            response_meta = {
                'id': chunk_data.get('id'),
                'created': chunk_data.get('created'),
                'model': chunk_data.get('model'),
            }

            choice = chunk.choices[0] if chunk.choices else None
            delta = choice.delta.content if choice and choice.delta else None
            delta_data = chunk_data['choices'][0].get('delta') or {} if chunk_data.get('choices') else {}
            # Reasoning models expose thinking as reasoning_content (DeepSeek/Qwen) or reasoning (OpenRouter)
            reasoning_delta = delta_data.get('reasoning_content') or delta_data.get('reasoning')

            if choice and choice.finish_reason:
                finish_reason = choice.finish_reason

            if reasoning_delta:
                reasoning += reasoning_delta
                yield {
                    'type': 'reasoning',
                    'delta': reasoning_delta,
                    'reasoning': reasoning
                }

            if delta:
                content += delta
                yield {
                    'type': 'delta',
                    'delta': delta,
                    'content': content
                }

        yield {
            'type': 'done',
            'response': {
                'id': response_meta.get('id'),
                'object': 'chat.completion',
                'created': response_meta.get('created'),
                'model': response_meta.get('model') or str(gpt_model),
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': content,
                            **({'reasoning': reasoning} if reasoning else {})
                        },
                        'finish_reason': finish_reason or 'stop'
                    }
                ],
                'usage': None
            }
        }
    except Exception as e:
        raise RuntimeError('Error while streaming GPT request:', str(e))
