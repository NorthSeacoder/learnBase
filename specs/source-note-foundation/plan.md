# Implementation Plan: Source-to-Note Foundation

**Workspace**: `source-note-foundation` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Use a dependency-free Python CLI over a local SQLite registry, with Markdown notes as the authoritative knowledge body. Agent Skills handle interpretation and source extraction; the CLI enforces stable local IDs and citation links.

## Architecture

```text
PDF / webpage -> source registration (SQLite) -> host reader + learnbase-study skill
                                                       -> Markdown note (02-notes/)
SQLite source/topic/note links <----------------------- note validation
```

The source registry stores topic, source, and note identities plus their links. External PDF references are read-only. Web fetching and PDF parsing are explicitly outside the core so the workspace can work offline and use whichever host tools are available.

## Decisions

- [ADR 0001](../../docs/adr/0001-markdown-and-sqlite.md): Markdown owns knowledge; SQLite owns structured records.
- [ADR 0002](../../docs/adr/0002-single-learner-multi-topic.md): one learner, multiple topics, cross-topic links.
- [ADR 0003](../../docs/adr/0003-offline-core-and-adapters.md): offline core, optional adapters.

## Validation

- Exercise CLI initialization, topic creation, PDF/web registration, note creation, and note validation in temporary workspaces.
- Verify external source files remain in place and unchanged.
- Verify duplicate registration reuses the source ID and changed citation IDs are rejected.
- Run the complete `unittest` suite and `git diff --check` in the target repository.
