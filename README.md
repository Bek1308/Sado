# Sado

**Sado** ("voice" in Tajik and Uzbek) is a multilingual, voice-first AI assistant for speakers of low-resource languages, built on Meta's Muse models.

Hundreds of millions of people speak languages that mainstream AI assistants barely understand. Sado lets them simply talk to an assistant in their own language. It launches with **Tajik and Uzbek** and is designed so new languages can be added without changing the core.

Built for the **Meta Global AI Developer Hackathon** (Oct 26 – Nov 4, 2026), Indie track.

## What it does

- Talk to the assistant by voice in your own language.
- Photograph a letter or official document and get it explained in plain language.
- Set reminders and draft replies through tool calls.
- Hear the answer spoken back in your language.

## Languages

| Language | Status |
|---|---|
| Tajik | First release |
| Uzbek | First release |
| Russian, English | Supported as fallback languages |
| More low-resource languages | Planned through a pluggable language layer |

## Stack

- **Mobile app:** Flutter
- **Brain:** Muse Spark via Meta Model API
- **Speech:** Muse Voice Transcribe and per-language text-to-speech

## Hackathon note

All code in this repository was written during the hackathon, starting Oct 27, 2026.
