# Glossary

| Term | Definition |
| --- | --- |
| Workspace | One cloned learnBase repository, owned by one learner and containing multiple topics. |
| Workspace setup | One-time capture of the small set of local settings needed to use a cloned workspace; integrations and learning preferences are not prerequisites. |
| Topic onboarding | A learner-reviewed conversation that defines a topic's purpose, desired outcomes, prior background, constraints, sources, and optional progress evidence. Unknowns may remain unset. |
| Integration prerequisites | External tools/services required only when an adapter is used. Anki/nmem are supported by default; workspace setup neither probes them nor saves enable switches. |
| Topic | A navigable subject area with a stable ID, optional parent, aliases, and links to knowledge. |
| Topic configuration | Learner-approved structured learning intent linked to a topic ID; unknown fields remain unknown, and source hints are not registered evidence. |
| Knowledge unit | A concept, method, fact, procedure, or skill that can be linked to one or more topics and notes. |
| Source | An original PDF, webpage, book, course, or other material used as evidence. A source record does not own or alter the original. |
| Locator | A page, heading, timestamp, URL fragment, or other position that lets a reader return to the cited evidence. |
| Note | The canonical Markdown explanation of knowledge, with source links and explicit uncertainty. |
| Learning activity | A learner event, such as study, recall, question practice, review, reading reflection, or practical work; its activity date may remain unknown. |
| Attempt | A learner's response to a question or task; correctness and outcomes are stored only when explicitly learner-reported or separately verified. |
| Evidence | A learner-reviewed statement, observed artifact, or verified outcome linked to its activity and optional source/note locators. |
| Profile dimension | A learner-approved, topic-scoped observable behavior with explicit eligible activity/evidence types, count threshold, and recency window. |
| Profile projection | A rebuildable view over configured evidence, marked unknown, pending, conflicting, or confirmed; it is descriptive, not a mastery score. |
| Card draft | A proposed retrieval prompt linked to verified knowledge. It is not a published card or a mastery judgment. |
| Learning objective key | An explicit stable slug within a topic used to identify one card objective; semantic equivalence is reviewed by the learner, not inferred automatically by the CLI. |
| Card provenance merge | An approved union of note, evidence, source and locator links into one stable card ID, retaining the existing question/answer unless an explicit replacement is reviewed. |
| Anki preview | A read-only comparison against an existing Basic note type and deck scope; shows the proposed Q&A and provenance plus matches, conflicts, or skipped items without publication. |
| Adapter | An optional integration that connects learnBase to a host or external service without becoming a second authority. |
| Topic-to-deck mapping | A many-to-many relationship between learning topics and Anki decks; decks may be shared and one topic may use multiple decks. |
