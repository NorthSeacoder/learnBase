# ADR 0002: One Learner Across Multiple Topics

- Status: accepted
- Date: 2026-11-09

## Context

The template should support learning a broad theme without creating a repository per subject, while still allowing independent topics and cross-topic concepts.

## Decision

One workspace represents one learner and can contain many topics. Topics form a tree for navigation. Knowledge units and sources may link to multiple topics; topic membership is not the sole identity of a concept.

## Consequences

- The initial schema avoids multi-user authorization and collaboration complexity.
- Stable topic IDs, aliases, and redirects are required for safe renames and merges.
- A profile claim must declare its topic scope and evidence coverage.
