"""Sado's character voices.

OmniVoice designs a voice from gender, age (child, teenager, young adult, middle-aged, elderly),
pitch (very low to very high) and a whisper style. Speaking speed gives each character its own
temperament: the elder takes his time, the young sister speaks briskly.
"""

from dataclasses import dataclass

from sado.domain.voice import Voice


@dataclass(frozen=True, slots=True)
class VoiceStyle:
    omnivoice_description: str
    speed: float = 1.0


@dataclass(frozen=True, slots=True)
class VoicePreset:
    voice: Voice
    style: VoiceStyle


VOICE_PRESETS = (
    VoicePreset(Voice("sado", "Sado"), VoiceStyle("male, moderate pitch")),
    VoicePreset(
        Voice("bobo", "Bobo — wise elder"), VoiceStyle("male, elderly, low pitch", speed=0.88)
    ),
    VoicePreset(
        Voice("aka", "Aka — calm baritone"),
        VoiceStyle("male, middle-aged, low pitch", speed=0.95),
    ),
    VoicePreset(
        Voice("opa", "Opa — warm and bright"),
        VoiceStyle("female, young adult, moderate pitch", speed=1.08),
    ),
    VoicePreset(
        Voice("momo", "Momo — gentle grandma"),
        VoiceStyle("female, elderly, moderate pitch", speed=0.9),
    ),
    VoicePreset(
        Voice("shivir", "Shivir — night whisper"),
        VoiceStyle("male, moderate pitch, whisper", speed=0.92),
    ),
)
