"""Who Sado is. These instructions are the same whichever model does the thinking."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sado.domain.language import Language

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
- Be kind and practical. Do not give medical, legal or financial advice; suggest who to ask.
"""


_MEMORY_INTRO = (
    "The user asked you to remember these facts. Use them when they help, and never invent others:"
)

_DUE_INTRO = "These reminders are now due. Mention them naturally when they fit the conversation:"


def persona_instructions(
    language: Language,
    memories: Sequence[str] = (),
    due_reminders: Sequence[str] = (),
    now: datetime | None = None,
) -> str:
    moment = now or datetime.now(UTC)
    instructions = (
        f"{_PERSONA}\n{_LANGUAGE_RULES[language]}\n"
        f"The current time is {moment:%A, %d %B %Y at %H:%M} UTC."
    )
    if memories:
        facts = "\n".join(f"- {memory}" for memory in memories)
        instructions = f"{instructions}\n\n{_MEMORY_INTRO}\n{facts}"
    if due_reminders:
        due = "\n".join(f"- {reminder}" for reminder in due_reminders)
        instructions = f"{instructions}\n\n{_DUE_INTRO}\n{due}"
    return instructions
