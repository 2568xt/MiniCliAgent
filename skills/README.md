# Demo Skills

This directory contains demo skills selected for two filters:

1. They map to high-frequency skill categories in the current public ecosystem.
2. They fit MiniCLIAgent's built-in tool surface today: `bash`, `read_file`, `write_file`, `edit_file`, `task_*`, `worktree_*`, `team_*`, and background tools.

As of 2026-04-27, I used `skills.sh` as a rough popularity signal. The numbers below are marketplace-facing weekly installs, not a universal measure of all agent usage, but they are good enough for a demo shortlist.

| Local skill | Why it is here | Public reference |
| --- | --- | --- |
| `plan-grill` | "Challenge my plan" is one of the most-used conversational skill patterns. | `mattpocock/skills/grill-me` on skills.sh, `37.8K` weekly installs |
| `systematic-debugging` | Debugging playbooks are one of the highest-use engineering skill categories. | `wshobson/agents/debugging-strategies` on skills.sh, `6.9K` weekly installs |
| `code-review` | Code review remains a top recurring agent workflow. | `google-gemini/gemini-cli/code-reviewer` on skills.sh, `5.9K` weekly installs |
| `readme-refresh` | README and repo-doc upkeep is a common low-risk but high-value agent task. | `shpigford/skills/readme` on skills.sh, `170` weekly installs |
| `release-notes` | Release summaries and changelog drafting are practical git-native automations. | `jmerta/codex-skills/release-notes` on skills.sh, `28` weekly installs |

These local versions are intentionally rewritten for MiniCLIAgent instead of copied from those sources. They assume no browser, no external SaaS connector, and no MCP runtime by default.

Deliberately excluded from this demo set:

- Browser-heavy skills such as Playwright or visual QA because this repo's runtime does not expose a browser tool by default.
- SaaS-integrated skills such as Linear, Slack, or Figma because those depend on external APIs/connectors not bundled here.
- MCP-authoring skills because they are useful, but less "immediately demoable" than review, debugging, docs, and release workflows.
