<!--
SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
SPDX-FileContributor: Claude Code (claude-opus-5-5)

SPDX-License-Identifier: CC0-1.0
-->

<!--
SPDX-FileCreatedBy: Michael Zikeli
SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)
-->

# walberla-spdx-ai

A Claude Code plugin that marks AI-generated content with SPDX/REUSE license
information. It implements the waLBerla AI policy, but works for any repository
and any file type.

It has two parts:

- **Skill `spdx-ai-annotation`**: tells Claude when and how to annotate. Headers are
  written with `reuse annotate`, so every file type gets the right comment style.
  Binaries get a `.license` sidecar file.
- **Hook**: after every `Write`, `Edit` or `MultiEdit`, the checker runs
  `reuse lint-file` plus AI-specific checks. Errors go back to Claude, which fixes them.

## Requirements

- [REUSE tool](https://reuse.software) 6.x: `pipx install reuse`
- Python 3.8 or newer

Without `reuse`, the checker falls back to a reduced header check and warns.

<!-- REUSE-IgnoreStart -->

## Rules the skill follows

| Change | License | Marker |
|---|---|---|
| Refactoring (rename, bug fix, formatting, localized modernization, moving code) | unchanged | none |
| New file fully written by the agent | `CC0-1.0`, unless the user wants another license | AI file header |
| New logic inside a human-written file | `CC0-1.0` | AI snippet |
| New logic in a core path | - | not allowed, Claude asks |
| Human-written file annotated on request | project license | normal REUSE header |

The project license is detected in this order: `project_license` in
`.spdx-ai.json`, the `LICENSES/` folder, the root `LICENSE`/`COPYING` file.
If the result is ambiguous (GPL text does not say `-only` or `-or-later`),
Claude asks.

### AI file header

```
/*
 * SPDX-FileCopyrightText: 2026 Jane Doe <jane@example.org>
 * SPDX-FileContributor: Claude Code (claude-opus-5-5)
 *
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * SPDX-FileCreatedBy: Jane Doe
 * SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)
 */
```

The first block comes from `reuse annotate`. The second block holds the policy tags.
It is a separate comment on purpose: `reuse annotate` rewrites its own block and
drops unknown tags. The separate block survives. `SPDX-FileContributor` is a
standard tag that `reuse` keeps, so the checker can detect a lost policy block.

### AI snippet

```
/**
 * SPDX-SnippetBegin
 * SPDX-SnippetCopyrightText: 2026 Jane Doe <jane@example.org>
 * SPDX-License-Identifier: CC0-1.0
 * SPDX-SnippetCreatedBy: Jane Doe
 * SPDX-SnippetCreatedUsing: Claude Code (claude-opus-5-5)
 */
...
/* SPDX-SnippetEnd */
```

### Differences to the current policy text

- `CC-0` is not a valid SPDX identifier. This plugin uses `CC0-1.0`.
- REUSE requires a copyright notice on every file and recommends one per snippet.
  The policy templates have none, so `SPDX-FileCopyrightText` and
  `SPDX-SnippetCopyrightText` were added. By default they carry the human's name.
  If the user explicitly chooses no copyright holder, the value is `NONE`.
  The line is never omitted, so files without a holder stay searchable.

<!-- REUSE-IgnoreEnd -->

## Installation

### Option A: plugin (recommended for the group)

Inside Claude Code:

```
/plugin marketplace add Pitt0s/claude-skills
/plugin install walberla-spdx-ai@pitt0s
```

To enable it for everyone in a repository, add to its `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "pitt0s": { "source": { "source": "github", "repo": "Pitt0s/claude-skills" } }
  },
  "enabledPlugins": { "walberla-spdx-ai@pitt0s": true }
}
```

To try it without installing, clone the repository and run
`claude --plugin-dir <clone>/plugins/walberla-spdx-ai`.

### Option B: copy into the repository

1. Copy `skills/spdx-ai-annotation/` to `<repo>/.claude/skills/spdx-ai-annotation/`.
2. Merge `examples/settings.json` into `<repo>/.claude/settings.json`.

## Configuration: `.spdx-ai.json` in the repository root

| Key | Default | Meaning |
|---|---|---|
| `project_license` | detected | SPDX ID of the project license |
| `ai_license` | `CC0-1.0` | License for AI-generated content |
| `ai_copyright` | ask | `"human"` or `"NONE"` for AI content; unset means Claude asks |
| `core_paths` | `[]` | Directories where AI-generated code is not allowed |
| `exclude_paths` | `[]` | Directories the checker ignores |
| `annotate_args` | `[]` | Extra arguments for `reuse annotate`, e.g. `["--multi-line"]` |
| `agent_pattern` | Claude, Copilot, GPT, ... | Regex that identifies an AI agent in `SPDX-FileContributor` |

See `examples/spdx-ai.json`.

## Checker

```
check_spdx.py FILE...               # reuse lint-file + AI checks, exit 1 on errors
check_spdx.py --no-header-check ... # skip missing-header errors (legacy files)
check_spdx.py --project-license DIR # print detected licenses as JSON
```

The hook requires a header only for `Write` (new or fully rewritten files).
`Edit` on a legacy file without header passes, so refactoring is not blocked.

## CI and pre-commit

The plugin reuses the official REUSE integrations where possible:

- `examples/pre-commit-config.yaml`: the `reuse-lint-file` hook from `fsfe/reuse-tool`
  plus this plugin's AI checks.
- `examples/gitlab-ci.yml`: runs the checker on changed files in merge requests,
  inside the `fsfe/reuse` container image.
- GitHub: use [fsfe/reuse-action](https://github.com/fsfe/reuse-action) for full
  `reuse lint`.

## Tests

```
bash tests/run_tests.sh
```

## License

CC0-1.0
