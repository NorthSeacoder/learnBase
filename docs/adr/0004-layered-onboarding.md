# ADR 0004: Layered Workspace, Topic, and Integration Onboarding

- Status: accepted
- Date: 2026-11-09

## Context

A learner may clone learnBase to study one of many possible domains. Asking for subject goals, study routines, or Anki configuration during repository initialization either makes every learner answer irrelevant questions or makes optional integrations appear mandatory. A README questionnaire would also duplicate the conversational workflow and become stale.

## Decision

Use three separate entry points:

1. **Workspace setup** runs once after cloning and captures only local runtime settings. Defaults should cover nonessential fields; it must not require a learner biography, study goals, Anki, nmem, or network access.
2. **Topic onboarding** runs when the learner starts a new subject. A host-neutral Agent Skill interviews the learner about desired outcomes, prior background, constraints, likely sources, and observable progress evidence. The learner may skip unknown fields and reviews the proposed topic configuration before it is stored.
3. **Integration prerequisites** are needed only when an adapter is used. Anki/nmem are supported by default without enable switches or setup probing (updated by `default-integration-support` on 2026-11-10). For Anki, read the actual existing decks, support shared decks and many-to-many topic mappings, and preview any remote deck creation or card write before explicit authorization.

The CLI owns validation and persistence of bounded structured fields. Skills own the conversational interview and domain-neutral modeling. The README provides the short path and current implementation status; it links to the Skill/spec instead of reproducing the questionnaire.

## Consequences

- A workspace can be used immediately without Anki or nmem.
- Topic-specific configuration is not confused with global learner identity.
- Adapter configuration can be added or changed without rerunning workspace setup.
- A generated topic plan is a proposal until reviewed by the learner.
- Workspace setup and topic onboarding are implemented locally. Anki/nmem support is available by default; external prerequisites and any authorization for writes remain separate from local initialization.
