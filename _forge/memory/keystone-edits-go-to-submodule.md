# Edits under _forge/keystone/ go to the ai_keystone repo

[`../keystone/`](../keystone/) is a **git submodule** (repo `ai_keystone`). Any edit under
`_forge/keystone/**` (README, roles, guardrails, profiles, pipelines, ARCHETYPES, ROADMAP)
**belongs to the `ai_keystone` repo**: commit + push there, then bump the submodule pin in
this repo (`git add _forge/keystone`). This repo stores only the pinned commit.

So a session that changes both layers produces **two commits in two repos**:
- `_forge/keystone/**` → the `ai_keystone` repo;
- everything else (`_forge/agents/`, `_forge/{skills,tools,memory}/`, root `skills/`,
  `knowledge/`, `_forge/TASKS.md`, `AGENTS.md`, `agents/`, `src/`, …) → this (alphavar) repo.

This is the PROMOTE/PROPAGATE end of the keystone learn loop. Part of
[[keystone-ai-assist-model]]. Commits are the owner's to make ([[owner-owns-commits]]).
