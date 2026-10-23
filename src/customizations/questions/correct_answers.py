"""Correct answers for the 12 main tasks, keyed by question ID.

Canonical source — all scoring and analysis code imports from here.
Letters match presentation order (what participants see):
  A = Only statement 1 is correct.
  B = Only statement 2 is correct.
  C = Both statements are correct.
  D = Neither of the two statements is correct.
"""

ANSWER_OPTIONS = [
    "Only statement 1 is correct.",              # A
    "Only statement 2 is correct.",              # B
    "Both statements are correct.",              # C
    "Neither of the two statements is correct.", # D
]

LETTERS = ["A", "B", "C", "D"]
LETTER_TO_TEXT = dict(zip(LETTERS, ANSWER_OPTIONS))
TEXT_TO_LETTER = {v: k for k, v in LETTER_TO_TEXT.items()}

# ponytail: the one dict that rules them all
CORRECT_ANSWERS = {
    "ypc_02":              "D",
    "ypc_03":              "B",
    "ypc_05":              "A",
    "ypc_06":              "A",
    "car_racing_01":       "D",
    "car_racing_02":       "C",
    "car_racing_03":       "B",
    "car_racing_05":       "A",
    "graduation_party_01": "B",
    "graduation_party_05": "A",
    "graduation_party_06": "D",
    "graduation_party_07": "B",
}

# Backward compat: ordered list of full answer text, used by app.py scoring
right_choices = [LETTER_TO_TEXT[CORRECT_ANSWERS[q]] for q in CORRECT_ANSWERS]
