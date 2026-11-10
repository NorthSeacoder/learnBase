# Tasks: Source-to-Note Foundation

- [x] T001 Create the template workspace contract and offline initialization flow. **Slice**: usable empty workspace. **Blocked by**: none. **Verify**: fresh-workspace CLI test.
- [x] T002 Add stable topics and PDF/web source registration with topic links and read-only external-file behavior. **Slice**: source is identifiable and safely registered. **Blocked by**: T001. **Verify**: CLI and external-file tests.
- [x] T003 Generate source-linked Markdown notes with locators and validate registry consistency. **Slice**: source can be converted into a traceable formal note. **Blocked by**: T002. **Verify**: note creation and drift-rejection tests.
- [x] T004 Add the shared Agent Skill and Codex/WorkBuddy discovery instructions. **Slice**: agent can run the source-to-note workflow. **Blocked by**: T003. **Verify**: skill path, WorkBuddy symlink, and docs inspection.
- [x] T005 Record verification evidence and local completion. **Slice**: roadmap can recommend the next feature. **Blocked by**: T001-T004. **Verify**: evidence ledger and acceptance record.

All tasks are complete for the local working tree. Commit, push, and GitHub template-repository activation are follow-through work and are not claimed as complete.
