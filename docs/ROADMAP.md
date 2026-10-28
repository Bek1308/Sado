# Roadmap

Build window: **27 Oct – 4 Nov 2026**. Submission deadline: **4 Nov, 9:00 PM ET**.

Each phase ends with something that runs end to end. If time runs short, later phases shrink — earlier ones are never left half-done.

| # | Phase | Dates | Done when | Status |
|---|---|---|---|---|
| 0 | Foundations | 27 Oct | Server and mobile skeletons build, lint and test in CI | ✅ 27 Oct |
| 1 | Speak | 28 Oct | The app speaks a typed sentence in Tajik, Uzbek, Russian and English | ✅ 27 Oct |
| 2 | Hear | 28–29 Oct | The app transcribes speech in all four languages | ✅ 28 Oct |
| 3 | Think | 29–30 Oct | Voice in → Muse Spark reasons as Sado → voice out | ✅ 28 Oct |
| 4 | Remember | 31 Oct | Sado saves, searches and recalls facts; the user can view and delete them | ✅ 28 Oct |
| 5 | See & Act | 1 Nov | Sado explains a photographed document and performs confirmed actions | ✅ 28 Oct |
| 6 | Character & Modes | 2 Nov | Sado's voice, face and personality; Home, Personal, Work and On-the-go modes | ✅ 29 Oct |
| 7 | Ship | 3 Nov | Deployed backend, hardened errors, updated README | ⏳ |
| 8 | Demo | 4 Nov | Three-minute video, submission, post on X | ⏳ |

---

## Phase 0 — Foundations
- Monorepo layout: `server/`, `mobile/`, `docs/`.
- Server: FastAPI app with Clean Architecture folders, settings from environment, health endpoint.
- Mobile: Flutter app with feature-first structure, theme, routing, dependency injection, HTTP client.
- Tooling: ruff, mypy, pytest; flutter analyze, flutter test.
- CI: GitHub Actions runs all checks on every push.

## Phase 1 — Speak
- Domain: `LanguagePack` and `SpeechSynthesizer` ports.
- Text normaliser per language: numbers, dates, currency and abbreviations become words.
- Adapter: Meta MMS-TTS for Tajik, Uzbek, Russian and English.
- Use case and endpoint: text → audio.
- Mobile: Sado home screen and audio playback.

## Phase 2 — Hear
- Domain: `SpeechRecognizer` port and a router that picks the recogniser per language.
- Adapter: Meta Omnilingual ASR for Tajik, Uzbek and Russian.
- Adapter: Muse Voice Transcribe for English and other supported languages.
- Use case and endpoint: audio → text with detected language.
- Mobile: push-to-talk recording and live transcript.

## Phase 3 — Think
- Domain: `Conversation`, `Message`, `Tool` and `ReasoningModel` port.
- Adapter: Meta Model API client for Muse Spark (tool calling, image input).
- Sado's persona prompt and agent loop: plan → call tools → answer.
- Use case and endpoint: one voice turn, audio in → audio out.
- Mobile: conversation screen.

## Phase 4 — Remember
- Domain: `Memory` entity and `MemoryStore` port.
- Adapter: SQLite store with full-text search.
- Agent tools: save, search and summarise memories.
- Mobile: memory screen to view, edit and delete.

## Phase 5 — See & Act
- Camera capture → Muse Spark vision → plain-language explanation in the user's language.
- Agent tools: reminders, message drafts, lists.
- Confirm-before-act: every side effect needs the user's yes.
- Mobile: camera flow and confirmation sheet.

## Phase 6 — Character & Modes
- Sado's designed voice and visual identity.
- Modes as configuration: each mode sets persona tone, enabled tools and greeting.
- Mobile: mode switcher and animated Sado face that reacts while listening and speaking.

## Phase 7 — Ship
- Backend deployed so judges can try it.
- Graceful failures: offline, slow network, unsupported language.
- README build log and screenshots updated.

## Phase 8 — Demo
- Script with three scenes: Home, On the go, Work.
- Record, edit, subtitle and narrate the three-minute video.
- Submit on Cerebral Valley and post the demo on X.
