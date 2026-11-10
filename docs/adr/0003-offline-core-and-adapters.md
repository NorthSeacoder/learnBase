# ADR 0003: Offline Core with Optional Adapters

- Status: accepted
- Date: 2026-11-09

## Context

Source reading, memory retrieval, and card publication may use different tools across Codex, WorkBuddy, and future hosts. Making one provider mandatory would reduce portability and make local study depend on external availability.

## Decision

The core CLI and repository workflows work offline. PDF extraction, web retrieval, nmem, and Anki are optional adapters. Agent workflows use a host-neutral Agent Skill contract, with thin host-specific discovery or invocation instructions where required.

## Consequences

- Source registration and Markdown note creation work without credentials or a network.
- Adapters must fail without discarding local state and must expose their side effects before external writes.
- Host compatibility is validated per host; a shared skill file alone does not prove host execution works.
