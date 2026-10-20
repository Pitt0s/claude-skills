<!--
SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
SPDX-FileContributor: Claude Code (claude-opus-5-5)

SPDX-License-Identifier: CC0-1.0
-->

<!--
SPDX-FileCreatedBy: Michael Zikeli
SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)
-->

# Changelog

All notable changes are listed here. Versions follow [Semantic Versioning](https://semver.org).

## walberla-spdx-ai

### 0.3.0 - 2026-10-20

- Copyright holder for AI content is asked for: the human's name by default,
  or `SPDX-FileCopyrightText: NONE` after an explicit choice.
- New config key `ai_copyright`.
- Files that must start with YAML frontmatter get a `.license` sidecar.
- The checker honors `REUSE-IgnoreStart` / `REUSE-IgnoreEnd` regions, so documentation
  can show SPDX examples.
- Fixed a checker crash on lines that contain `SPDX-` but no tag name.

### 0.2.0 - 2026-10-20

- Headers are written with `reuse annotate` and checked with `reuse lint-file`.
- Works for all file types. Binaries get a `.license` sidecar.
- AI license is `CC0-1.0` instead of the invalid `CC-0`.
- Project license is detected from `.spdx-ai.json`, `LICENSES/` or `LICENSE`/`COPYING`.
- Refactoring needs no AI marker.
- Copyright lines added to AI headers and snippets, as REUSE requires.

### 0.1.0 - 2026-10-20

- First version: skill, PostToolUse hook and checker for the waLBerla AI policy.
