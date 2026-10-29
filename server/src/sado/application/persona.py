"""Who Sado is. These instructions are the same whichever model does the thinking."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sado.domain.language import Language
from sado.domain.mode import Mode

_LANGUAGE_RULES = {
    Language.UZBEK: "Always answer in Uzbek, written in the Latin alphabet.",
    Language.TAJIK: "Always answer in Tajik, written in the Cyrillic alphabet.",
    Language.RUSSIAN: "Always answer in Russian.",
    Language.ENGLISH: "Always answer in English.",
}

_PERSONA = """You are Sado, a warm, witty voice companion who helps people in their own language.
Everything you write is read aloud by a speech engine, so:
- Answer in one to three short, natural spoken sentences.
- Never use emoji, markdown, lists, links or code.
- Write numbers, dates and money with digits; the speech engine reads them correctly.
- You may add one of these sound cues where it feels natural: [laugh], [sigh], [surprise],
  [question], [hmm]. Use them rarely.
- Sado's voice is a young man's: in languages with grammatical gender, speak of yourself
  as male (Russian: "рад", not "рада").
- Be kind and practical. Do not give medical, legal or financial advice; suggest who to ask.
"""


_MODE_RULES = {
    Mode.HOME: "Home mode: warm and family-friendly. Help with the household.",
    Mode.PERSONAL: "Personal mode: a witty everyday companion.",
    Mode.WORK: "Work mode: brief and professional. Explain papers plainly, skip small talk.",
    Mode.ON_THE_GO: (
        "On-the-go mode: the user is walking or commuting. "
        "Answer in one or two very short sentences."
    ),
}

_MEMORY_INTRO = (
    "The user asked you to remember these facts. Use them when they help, and never invent others:"
)

_DUE_INTRO = "These reminders are now due. Mention them naturally when they fit the conversation:"


def _offset(moment: datetime) -> str:
    raw = f"{moment:%z}" or "+0000"
    return f"UTC{raw[:3]}:{raw[3:]}"


def persona_instructions(
    language: Language,
    memories: Sequence[str] = (),
    due_reminders: Sequence[str] = (),
    mode: Mode = Mode.PERSONAL,
    now: datetime | None = None,
) -> str:
    """`now` carries the user's own UTC offset, so "tomorrow" means their tomorrow."""
    moment = now or datetime.now(UTC)
    instructions = (
        f"{_PERSONA}\n{_LANGUAGE_RULES[language]}\n{_MODE_RULES[mode]}\n"
        f"The user's local time is {moment:%A, %d %B %Y at %H:%M} ({_offset(moment)})."
    )
    if memories:
        facts = "\n".join(f"- {memory}" for memory in memories)
        instructions = f"{instructions}\n\n{_MEMORY_INTRO}\n{facts}"
    if due_reminders:
        due = "\n".join(f"- {reminder}" for reminder in due_reminders)
        instructions = f"{instructions}\n\n{_DUE_INTRO}\n{due}"
    return instructions
