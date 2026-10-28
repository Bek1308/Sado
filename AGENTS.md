# AGENTS.md

Guide for coding agents working on Sado. Read `docs/ENGINEERING.md` first; it is the source of truth for architecture and style.

## Code map

- `server/src/sado/` — FastAPI backend, Clean Architecture
  - `domain/` entities and ports, no framework imports
  - `application/` use cases (`Converse`, `Memories`, `Reminders`, `ExplainDocument`, ...)
  - `infrastructure/` adapters: Muse Spark (`reasoning/`), Omnilingual ASR (`asr/`), OmniVoice and MMS-TTS (`tts/`), SQLite (`memory/`), language packs (`languages/`)
  - `presentation/` routers and request/response schemas
  - `main.py` the only composition root
- `server/workers/` the Omnilingual ASR worker; runs on Linux or WSL only
- `mobile/lib/` Flutter app, feature-first: `features/<feature>/{domain,data,presentation}`, shared code in `core/`
- `docs/` roadmap and engineering rules

## Checks that must pass

```
cd server && uv run ruff format --check src tests && uv run ruff check src tests && uv run mypy src && uv run pytest -q
cd mobile && dart format --set-exit-if-changed lib test && dart analyze && flutter test
```

Use `dart analyze`, not `flutter analyze`: the latter fails on the Cyrillic folder path. Build Android from the ASCII junction `C:\dev\Sado`.

## Rules

- Every new behaviour comes with tests, written against fakes rather than real models or network.
- Comments explain why, never what.
- Secrets live in `server/.env` (git-ignored); document new settings in `server/.env.example`.
- Never commit generated data (`server/data/`), run logs (`server/.run/`) or build output.
- Never use the project owner's own voice recordings for cloning or testing.
- User-facing text in the app is English; Sado answers in the user's language.
