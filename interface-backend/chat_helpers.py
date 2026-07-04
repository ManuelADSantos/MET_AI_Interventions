from openai import OpenAI
from config_loader import load_config

config = load_config()
oai_key = config['openai_api_key']
gpt_model = config['gpt_model']

api_base_url = config.get('base_url')

client_kwargs = {'api_key': oai_key}
if api_base_url:
    client_kwargs['base_url'] = api_base_url
gpt_client = OpenAI(**client_kwargs)

def format_messages(messages):
    return [
        {
            'role': str(m['role']),
            'content': [
                { 'type': 'text', 'text': str(m['content']) },
                { 'type': 'image_url', 'image_url': { 'url': str(m['image']), 'detail': 'low' }}
            ]
        }
        if 'image' in m else
        {
            'role': str(m['role']),
            'content': str(m['content'])
        }
        for m in messages
    ]

def get_completion(messages):
    try:
        completion = gpt_client.chat.completions.create(
            model = str(gpt_model),
            messages = format_messages(messages)
        )

        return completion.model_dump()
    except Exception as e:
        raise RuntimeError('Error while fulfilling GPT request:', str(e))

def stream_completion(messages):
    try:
        stream = gpt_client.chat.completions.create(
            model = str(gpt_model),
            messages = format_messages(messages),
            stream = True
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
                'system_fingerprint': chunk_data.get('system_fingerprint')
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
                'system_fingerprint': response_meta.get('system_fingerprint'),
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
