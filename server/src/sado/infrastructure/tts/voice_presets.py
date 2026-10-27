"""Sado's character voices, described in OmniVoice's voice-design vocabulary.

OmniVoice understands gender, age (child, teenager, young adult, middle-aged, elderly),
pitch (very low to very high) and a whisper style.
"""

from dataclasses import dataclass

from sado.domain.voice import Voice


@dataclass(frozen=True, slots=True)
class VoicePreset:
    voice: Voice
    omnivoice_description: str


VOICE_PRESETS = (
    VoicePreset(Voice("sado", "Sado"), "male, moderate pitch"),
    VoicePreset(Voice("bobo", "Bobo — wise elder"), "male, elderly, low pitch"),
    VoicePreset(Voice("aka", "Aka — calm baritone"), "male, middle-aged, low pitch"),
    VoicePreset(Voice("opa", "Opa — warm and bright"), "female, young adult, moderate pitch"),
    VoicePreset(Voice("momo", "Momo — gentle grandma"), "female, elderly, moderate pitch"),
    VoicePreset(Voice("shivir", "Shivir — night whisper"), "male, moderate pitch, whisper"),
)
