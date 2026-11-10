# ADR 0001: Markdown Knowledge and SQLite Learning Records

- Status: accepted
- Date: 2026-11-09

## Context

The workspace needs editable notes, traceable sources, structured learning events, and useful reports. Markdown is easy to review, diff, export, and use with common agents. Structured event histories need stable identity, constraints, deduplication, and rebuildable queries.

## Decision

Markdown is authoritative for formal knowledge content. SQLite is authoritative for structured identity, provenance links, learning events, evidence, and profile state. Reports are derived; external memory services and flashcard systems are adapters, not alternate sources of truth.

## Consequences

- Notes remain portable and human-editable.
- Learning state requires a supported transactional writer and a versioned schema.
- Markdown and SQLite links must be validated; a successful database write does not imply a note or report is current.
- Integrations must retain local IDs and provide reconciliation receipts.
