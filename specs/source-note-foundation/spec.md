# Feature Specification: Source-to-Note Foundation

**Workspace**: `source-note-foundation`\
**Created**: 2026-11-09\
**Status**: Complete (local implementation and verification)\
**Input**: Create a reusable, offline-capable learning workspace that registers PDF/web sources and produces cited Markdown notes.

## Change Profile

| Field | Value |
|---|---|
| Change Profile | medium |
| Risk Signals | User-facing workflow and persistent source/note identity; local writes are reversible; no network or external writes |
| Override | none |
| Upgrade Trigger | Add network fetch, OCR, external synchronization, or publication |

## Feature Traits

| Trait | Hit | Basis |
|---|---|---|
| `multi-stage-workflow` | yes | Register source, read it, write note, validate citation |
| `external-side-effects` | no | No remote service writes or original-file modification |
| `artifact-handoff` | yes | Source IDs and locators flow into note frontmatter and SQLite |
| `user-visible-output` | yes | CLI creates user notes and reports validation results |
| `prior-closure-failure` | no | New template foundation |
| `bugfix-loop-breaker` | no | Not a bug-fix feature |

## User Scenarios

### Story 1: Initialize a learning workspace (P1)

As a learner, I want to initialize a cloned template and add topics so that materials from different subjects have stable destinations.

Acceptance: `init` creates the standard folders and SQLite registry; topic IDs are stable slugs; optional parent links are checked.

### Story 2: Register a source and create a cited note (P1)

As a learner, I want to register a PDF or webpage and create a Markdown note with page/section locations so that claims can be checked against the original.

Acceptance: source IDs are stable on repeated registration; external PDFs are recorded read-only; notes link to known source IDs; validation detects citation drift.

## Requirements

- **FR-001**: Initialize the workspace folders and versioned SQLite registry without third-party dependencies.
- **FR-002**: Register topics with stable IDs and optional parent topics.
- **FR-003**: Register local PDFs and web URLs and link each source to one or more topics.
- **FR-004**: Record local file size and SHA-256; do not copy, move, or modify an external PDF.
- **FR-005**: Reuse a source ID for an unchanged source at the same location; report a changed local revision for review instead of silently replacing it.
- **FR-006**: Generate Markdown notes with stable note IDs, topic links, source IDs, and locators.
- **FR-007**: Validate that a note remains under `02-notes/` and its source IDs/locators agree with the local registry.
- **FR-008**: Provide a host-neutral Agent Skill for reading source material and creating cited notes.
- **NFR-001**: The core source registry and note workflow work offline; source extraction is delegated to optional host capabilities.

## Out of Scope

- Bundled PDF parsing, OCR, web crawling, or model API.
- Learning attempt/review events, profile claims, spaced repetition, or Anki publishing.
- Importing personal records or exam-specific rules from the source project.

## Completion

Implementation tasks and evidence are recorded in [tasks.md](tasks.md) and [verify-evidence.md](verify-evidence.md). M2 is tracked separately as the active feature.
