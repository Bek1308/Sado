"""Failure paths a real user or a demo can hit, each pinned so it stays handled."""

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from sado.application.converse import REMEMBER, Converse
from sado.application.memories import Memories
from sado.application.reminders import Reminders
from sado.application.speak_text import SpeakText
from sado.application.transcribe_speech import TranscribeSpeech
from sado.domain.audio import Audio
from sado.domain.conversation import (
    Answer,
    Message,
    ModelTurn,
    Speaker,
    ToolCall,
    ToolRequest,
    ToolSpec,
    ToolStep,
)
from sado.domain.errors import (
    EmptyTextError,
    ReasoningUnavailableError,
    SpeechRecognitionUnavailableError,
    SpeechSynthesisUnavailableError,
    UnreadableRecordingError,
)
from sado.domain.language import Language
from sado.domain.mood import Mood
from sado.domain.recording import Recording, Transcript
from sado.domain.speech import LanguagePack
from sado.domain.voice import Voice
from sado.infrastructure.asr.omnilingual import OmnilingualRecognizer
from sado.infrastructure.memory.sqlite_reminders import SqliteReminderStore
from sado.infrastructure.memory.sqlite_store import SqliteMemoryStore
from sado.main import create_app
from tests.fakes import UppercaseNormalizer, fake_language_pack, fake_voice_catalog

_DUSHANBE = timezone(timedelta(hours=5))
_QUESTION = [Message(Speaker.USER, "Salom")]


class _Model:
    def __init__(self, *turns: ModelTurn) -> None:
        self._turns = list(turns)
        self.instructions: list[str] = []

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Message],
        tools: Sequence[ToolSpec],
        steps: Sequence[ToolStep],
    ) -> ModelTurn:
        self.instructions.append(instructions)
        return self._turns.pop(0)


def _reminders() -> Reminders:
    return Reminders(SqliteReminderStore(":memory:"))


# Reminders


def test_a_reminder_is_not_due_early_for_a_user_ahead_of_utc() -> None:
    reminders = _reminders()
    now = datetime.now(_DUSHANBE)
    reminders.remind("Call mother", (now + timedelta(hours=3)).isoformat())

    assert reminders.due(now) == []


def test_a_due_reminder_is_mentioned_once() -> None:
    reminders = _reminders()
    reminders.remind("Call mother", "2000-01-01T09:00:00+00:00")
    model = _Model(Answer("Salom!"), Answer("Yana salom!"))
    converse = Converse(model, None, reminders)

    converse.execute(_QUESTION, Language.UZBEK)
    converse.execute(_QUESTION, Language.UZBEK)

    assert "Call mother" in model.instructions[0]
    assert "Call mother" not in model.instructions[1]


def test_old_stores_gain_delivery_tracking(tmp_path: Path) -> None:
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as old:
        old.execute(
            "CREATE TABLE reminders (id TEXT PRIMARY KEY, text TEXT, due_at TEXT, created_at TEXT)"
        )

    reminders = Reminders(SqliteReminderStore(path))
    reminders.remind("Call mother", "2000-01-01T09:00:00+00:00")

    assert [reminder.text for reminder in reminders.due(datetime.now(UTC))] == ["Call mother"]


# Empty answers


def test_a_silent_answer_after_a_tool_becomes_a_short_confirmation() -> None:
    memories = Memories(SqliteMemoryStore(":memory:"))
    model = _Model(
        ToolRequest(calls=(ToolCall("c1", REMEMBER.name, {"fact": "Ismi Aziz"}),)),
        Answer("   "),
    )

    reply = Converse(model, memories).execute(_QUESTION, Language.UZBEK)

    assert reply.text == "Bo'ldi."


def test_a_silent_answer_without_tools_is_reported_not_shown() -> None:
    with pytest.raises(ReasoningUnavailableError):
        Converse(_Model(Answer(""))).execute(_QUESTION, Language.UZBEK)


# Speech recognition


def _recognizer(response: httpx.Response) -> OmnilingualRecognizer:
    transport = httpx.MockTransport(lambda _: response)
    return OmnilingualRecognizer(httpx.Client(base_url="http://asr.test", transport=transport), "x")


def test_an_unreadable_recording_is_the_recordings_fault() -> None:
    recognizer = _recognizer(httpx.Response(422, json={"detail": "Audio is longer than 40 s"}))

    with pytest.raises(UnreadableRecordingError, match="longer than 40 s"):
        recognizer.transcribe(Recording(b"audio", "audio/mp4"))


def test_a_garbled_worker_reply_means_the_service_is_unavailable() -> None:
    recognizer = _recognizer(httpx.Response(200, text="<html>tunnel error</html>"))

    with pytest.raises(SpeechRecognitionUnavailableError):
        recognizer.transcribe(Recording(b"audio", "audio/mp4"))


@dataclass
class _CountingRecognizer:
    text: str
    calls: list[str] = field(default_factory=list)

    def transcribe(self, recording: Recording) -> Transcript:
        self.calls.append(self.text)
        return Transcript(self.text)


def test_silence_is_transcribed_once_not_in_every_language() -> None:
    recognizer = _CountingRecognizer("")
    packs = {
        language: LanguagePack(
            language, UppercaseNormalizer(), fake_language_pack(language)[1], recognizer
        )
        for language in Language
    }

    transcript, _ = TranscribeSpeech(packs).execute_auto(Recording(b"hush", "audio/mp4"))

    assert transcript.text == ""
    assert len(recognizer.calls) == 1


# Speech synthesis


class _BrokenSynthesizer:
    def synthesize(self, text: str, voice: Voice, mood: Mood) -> Audio:
        raise RuntimeError("CUDA out of memory")


def test_a_failing_voice_engine_means_sado_cannot_speak() -> None:
    pack = LanguagePack(
        Language.UZBEK, UppercaseNormalizer(), _BrokenSynthesizer(), _CountingRecognizer("")
    )

    with pytest.raises(SpeechSynthesisUnavailableError):
        SpeakText({Language.UZBEK: pack}, fake_voice_catalog()).execute("Salom", Language.UZBEK)


def test_a_reply_of_only_cues_has_nothing_to_say() -> None:
    pack, _ = fake_language_pack(Language.UZBEK)

    with pytest.raises(EmptyTextError):
        SpeakText({Language.UZBEK: pack}, fake_voice_catalog()).execute("[laugh]", Language.UZBEK)


# Conversation history


def test_long_sado_turns_stay_in_the_history_but_long_user_turns_do_not() -> None:
    pack, _ = fake_language_pack(Language.UZBEK)
    client = TestClient(
        create_app(
            language_packs={Language.UZBEK: pack},
            voice_catalog=fake_voice_catalog(),
            reasoning_model=_Model(Answer("Ha.")),
        )
    )
    long_text = "Uzun tushuntirish. " * 200

    with_long_explanation = client.post(
        "/replies",
        json={
            "language": "uz",
            "messages": [
                {"speaker": "sado", "text": long_text},
                {"speaker": "user", "text": "Tushundim"},
            ],
        },
    )
    with_long_question = client.post(
        "/replies",
        json={"language": "uz", "messages": [{"speaker": "user", "text": long_text}]},
    )

    assert with_long_explanation.status_code == 200
    assert with_long_question.status_code == 422
