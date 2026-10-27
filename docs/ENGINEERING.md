# Engineering Principles

These rules apply to every line of code in this repository — server and mobile.
The goal: a reviewer opening any file should find it clean, predictable and easy to change.

## 1. Repository layout

```
sado/
├── server/   # Python backend: speech, agent, memory
├── mobile/   # Flutter app
└── docs/     # Architecture, roadmap, decisions
```

## 2. Clean Architecture

Both apps follow the same four layers. **Dependencies point inward only.**

```
presentation  →  application  →  domain  ←  infrastructure
```

| Layer | Contains | May depend on |
|---|---|---|
| **domain** | Entities, value objects, repository and service interfaces (ports) | Nothing |
| **application** | Use cases that orchestrate the domain | domain |
| **infrastructure** | Adapters: Meta Model API, ASR/TTS models, database, file system | domain, application |
| **presentation** | HTTP routes (server), screens and state (mobile) | application, domain |

Rules:

- The domain layer never imports a framework, SDK or I/O library.
- Every external service sits behind an interface defined in the domain. Swapping a model or provider changes one adapter, nothing else.
- Objects are wired together in a single **composition root** — never inside business logic.
- Languages are **plug-ins**. A language pack bundles its speech-to-text, text-to-speech and text normaliser. Adding a language must not touch the agent.

### Server (Python 3.12, FastAPI)

```
server/src/sado/
├── domain/          # entities, ports
├── application/     # use cases
├── infrastructure/  # adapters (meta_api, asr, tts, storage, languages)
├── presentation/    # FastAPI routers and request/response schemas
└── main.py          # composition root
```

### Mobile (Flutter, feature-first)

```
mobile/lib/
├── core/                    # shared: errors, network, theme, DI
└── features/<feature>/
    ├── domain/              # entities, repository interfaces, use cases
    ├── data/                # data sources, DTOs, repository implementations
    └── presentation/        # state, pages, widgets
```

## 3. Clean code

- **Names explain intent.** `transcribe_audio`, not `process`. No abbreviations except well-known ones (`id`, `url`, `tts`).
- **Small units.** A function does one thing. If it needs "and" in its name, split it.
- **No magic values.** Constants and configuration live in one place.
- **Explicit types everywhere.** Python is fully type-hinted; Dart uses strict analysis.
- **Errors are values the caller can handle.** Domain-specific exceptions on the server, `Result`-style failures on mobile. Never swallow an error silently.
- **No dead code.** Unused code and commented-out blocks are deleted, not kept "just in case".
- **Secrets never enter the repository.** Configuration comes from environment variables; `.env.example` documents them.

## 4. Comments

Comments are rare and valuable. The code says **what**; a comment says **why**.

Write a comment when:

- the reason behind a decision is not obvious from the code;
- a workaround exists for an external limitation (link to the source);
- a public interface needs a one-line docstring describing its contract.

Do not write a comment when:

- it repeats the code (`# increment counter`);
- a better name would make it unnecessary;
- it describes history — that belongs in the commit message.

All code, comments and docs are written in English.

## 5. Quality gates

| Area | Server | Mobile |
|---|---|---|
| Formatting | `ruff format` | `dart format` |
| Linting | `ruff check` | `flutter analyze` with strict rules |
| Types | `mypy --strict` | Sound null safety, strict casts |
| Tests | `pytest` for domain and use cases | `flutter test` for domain and state |

Every commit must pass formatting, linting and tests. CI runs the same checks on every push.

## 6. Git

- Small, focused commits with [Conventional Commits](https://www.conventionalcommits.org/) messages: `feat(server): add MMS-TTS adapter`.
- One logical change per commit. Formatting-only changes go in their own commit.
- `main` must always build.
