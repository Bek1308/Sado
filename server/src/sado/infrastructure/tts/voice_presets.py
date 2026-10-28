"""Sado's character voices.

Each voice is designed once from words (gender, age, pitch, whisper) and every later sentence
is cloned from that first recording, so the voice never drifts between sentences.
Speaking speed is left to the model: forcing it makes OmniVoice sound synthetic.
"""

from dataclasses import dataclass

from sado.domain.voice import Voice


@dataclass(frozen=True, slots=True)
class VoiceStyle:
    omnivoice_description: str


@dataclass(frozen=True, slots=True)
class VoicePreset:
    voice: Voice
    style: VoiceStyle


VOICE_PRESETS = (
    VoicePreset(
        Voice("sado", "Sado", "Friendly and clear"),
        VoiceStyle("male, young adult, moderate pitch"),
    ),
    VoicePreset(
        Voice("bobo", "Bobo", "Wise elder"),
        VoiceStyle("male, elderly, low pitch"),
    ),
    VoicePreset(
        Voice("aka", "Aka", "Calm baritone"),
        VoiceStyle("male, middle-aged, low pitch"),
    ),
    VoicePreset(
        Voice("opa", "Opa", "Warm and bright"),
        VoiceStyle("female, young adult, moderate pitch"),
    ),
    VoicePreset(
        Voice("momo", "Momo", "Gentle grandma"),
        VoiceStyle("female, elderly, moderate pitch"),
    ),
    VoicePreset(
        Voice("shivir", "Shivir", "Night whisper"),
        VoiceStyle("male, young adult, moderate pitch, whisper"),
    ),
)
