from enum import StrEnum


class Mood(StrEnum):
    """The emotional colour of a whole utterance, independent of who is speaking."""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    CALM = "calm"
    SAD = "sad"
    EXCITED = "excited"
    SERIOUS = "serious"
