"""
Tiny checks for reasoning summary conversion.
Run inside the backend container:
    docker compose exec backend python /tests/test_chat_reasoning.py
"""

import chat_helpers


class FakeResponse:
    output_text = "Final answer"

    def model_dump(self):
        return {
            "id": "resp_1",
            "model": "test-model",
            "created_at": 123,
            "status": "completed",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [
                        {"type": "summary_text", "text": "Checked the premises."}
                    ],
                },
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "Final answer"}
                    ],
                },
            ],
        }


response = chat_helpers.as_chat_response(FakeResponse())
message = response["choices"][0]["message"]
assert message["content"] == "Final answer"
assert message["reasoning"] == "Checked the premises."

response = chat_helpers.as_chat_response(None, "A", "R")
assert response["choices"][0]["message"] == {
    "role": "assistant",
    "content": "A",
    "reasoning": "R",
}

print("chat reasoning conversion tests passed")
