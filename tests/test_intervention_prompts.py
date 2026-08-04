"""
Shape checks on INTERVENTION_PROMPTS. These are the stimulus text of the study, so a typo is a
silent manipulation failure rather than a crash — a missing "\\n" once glued two rules into one line.
Run inside the backend container:
    docker compose exec backend sh -c 'cd /app && PYTHONPATH=/app python /tests/test_intervention_prompts.py'
"""

import sys

sys.path.insert(0, '/app')

from app import INTERVENTION_PROMPTS  # noqa: E402

REFUSAL = 'I work one step at a time - here is the next step.'

for condition, prompt in INTERVENTION_PROMPTS.items():
    lines = [line for line in prompt.split('\n') if line.strip()]
    assert lines, f'{condition}: empty prompt'
    # Every line after the preamble is a rule, so a line that neither starts a rule nor is indented
    # continuation means two rules were concatenated by a missing newline.
    rules_start = next(i for i, line in enumerate(lines) if line.startswith('Rules'))
    for line in lines[rules_start + 1:]:
        assert line.startswith('- ') or line.startswith('  '), \
            f'{condition}: line is neither a rule nor indented continuation (missing newline?): {line[:80]!r}'
    assert prompt.endswith('\n'), f'{condition}: prompt should end with a newline'

alternatives = INTERVENTION_PROMPTS['alternatives']
for option in ('A - Only statement 1', 'B - Only statement 2', 'C - Both statements', 'D - Neither of the two'):
    assert option in alternatives, f'alternatives: missing option {option!r}'
assert 'never from you' in alternatives, 'alternatives: lost the do-not-invent-the-statements rule'

pause = INTERVENTION_PROMPTS['pause-points']
assert pause.count(REFUSAL) == 1, f'pause-points: canned refusal appears {pause.count(REFUSAL)} times, want exactly 1'
assert 'ENTIRE reply' in pause, 'pause-points: lost the refusal-only rule that stops answer-on-demand'
assert 'THREE' in pause and 'TEN' in pause, 'pause-points: step budget changed'

print(f'intervention prompts: all assertions passed ({", ".join(sorted(INTERVENTION_PROMPTS))})')
