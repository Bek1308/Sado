# Submission — Meta Global AI Developer Hackathon 2026 · Indie track

Copy each part into the matching field of the submission form.

## Project name

Sado

## Tagline

One voice. Every language. A voice-first AI companion that hears Tajik, Uzbek, Russian and English, and gets things done on your phone and computer.

## The problem

Mainstream AI assistants speak about 25 languages. Tajik and Uzbek, spoken by more than 40 million people, are not among them, and Meta's hosted speech API does not cover them either. For millions of people, including migrant workers who receive papers in Russian they cannot read, "talk to your phone" still does not work.

## What it does

Sado is a voice-first companion you simply talk to.

- **Hears and speaks four languages** — Tajik, Uzbek, Russian and English — and works out which one you used.
- **Remembers and reminds** — facts you share, reminders, shopping lists, all visible and deletable in the app.
- **Explains any paper** — photograph a Russian utility notice or share a contract PDF; Sado explains it in your language.
- **Acts on your phone** — calls and texts (only after your spoken "yes"), plays music, sets alarms and timers, calendar events, volume, battery, maps, apps.
- **Acts on your computer** — call it by saying "Sado"; it reads the screen and explains it, reads what a coding agent in the terminal just answered and types it the next task, finds and opens files, controls media, and runs commands after your yes.
- **One Sado across devices** — sign in with Google: the owner's phone drives the computer and the computer reaches the phone; everyone else gets their own private Sado.
- **A living 3D sphere** — drawn live on the GPU, it ripples with your voice and with Sado's.

## How we built it (Meta models)

- **Muse Spark 1.3** (Meta Model API) is the brain: conversation, tool calling for 40+ tools, reading photos and documents, and web search through the Responses API.
- **Omnilingual ASR** (Meta FAIR, open source) listens in all four languages on a local GPU.
- **Muse Spark Open** on Baseten listens when no GPU is available, so the server runs anywhere.
- **MMS-TTS** (Meta, open source) is the fallback voice; OmniVoice provides designed voices and moods.
- Server: Python FastAPI with clean architecture, 300 tests, strict typing. App: Flutter for Android and Windows, Riverpod, a GLSL fragment shader for the sphere. Firebase for Google sign-in; Vosk for the offline wake word.

## Challenges

- No hosted speech model covers Tajik or Uzbek, so we paired Muse Spark with open Meta speech models and wrote number, date and money normalisation for each language.
- Making an agent that acts safe: every action that reaches another person or changes the computer is a single-use, expiring request that only the user's yes can run; the model can never confirm it.
- Giving judges a working demo without exposing the owner's computer or memories: per-account spaces and an owner-only computer link.

## What's next

- More languages from Omnilingual's 1,600 through pluggable language packs.
- An always-on wake word on the phone.
- A hosted GPU backend so anyone can install the app and talk.

## Links

- Code: https://github.com/Bek1308/Sado
- Demo video: https://youtu.be/kC3cya5tfrU
