---
name: learnbase-onboarding
description: Interview a learner when starting a topic in a learnBase workspace, then save only a reviewed and explicitly approved topic proposal.
---

# learnBase Topic Onboarding

Use this skill when a learner wants to start a new topic in an initialized learnBase workspace. The skill owns the conversation and proposal review; the CLI owns validation and persistence.

## Interview

Ask concise questions in a low-friction order about:

1. The outcome the learner wants from this topic.
2. Relevant prior background, if they know it.
3. Available time, constraints, or preferences that affect the plan.
4. Likely sources or materials they may use.
5. Observable signals they may use later to notice progress.

Let the learner skip any question or say they do not know. Do not infer a level, mastery, confidence, mistake, duration, or learning history. Progress signals describe possible future observations; they are not evidence that the learner has already mastered something. Source hints are leads only; register actual sources separately and preserve their IDs and locators when creating notes.

## Proposal Contract

Create one JSON object with `proposal_version` set to `1` and these fields:

```json
{
  "proposal_version": 1,
  "topic_id": "lowercase-stable-slug",
  "name": "Learner-facing topic name",
  "parent_id": null,
  "learning_goal": null,
  "prior_background": null,
  "constraints": null,
  "source_hints": null,
  "progress_signals": null
}
```

`topic_id` is stable and uses lowercase ASCII letters, digits, and hyphens. `name` is required. Optional scalar fields use `null` when skipped or unknown. Optional list fields use `null` when skipped or unknown and `[]` when the learner explicitly has none to add. Each list may contain at most 20 non-empty strings. Do not add fields outside this contract.

## Review and Save

Show the learner the complete proposal, including its topic ID and parent, before writing anything. Apply requested edits and show the revised proposal. Ask for explicit approval of the final proposal. A general request to continue the conversation is not approval to save.

Only after explicit approval, pass the reviewed JSON to:

```sh
python3 tools/learnbase.py topic onboard --proposal - --approved
```

Provide the JSON object on stdin. If the host cannot pass stdin, write a temporary JSON file outside the workspace only after approval, use `--proposal <temporary-file> --approved`, then remove the temporary file. Never write an unapproved proposal into the workspace. If the CLI rejects it, report the error and do not claim it was saved. Confirm the created topic ID only after a successful CLI result.

The CLI stores the topic and its configuration together in SQLite. This flow does not update a learner profile, register sources, connect an integration, or publish anything externally.
