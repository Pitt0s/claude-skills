<!--
SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
SPDX-FileContributor: Claude Code (claude-opus-5-5)

SPDX-License-Identifier: CC0-1.0
-->

<!--
SPDX-FileCreatedBy: Michael Zikeli
SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)
-->

# Contributing

Contributions are welcome. Please open an issue first for larger changes.

## Adding a plugin

1. Create `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json` manifest.
2. Put skills in `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.
3. Put hooks in `plugins/<plugin-name>/hooks/hooks.json`. Reference scripts
   with `${CLAUDE_PLUGIN_ROOT}`.
4. Add the plugin to `.claude-plugin/marketplace.json`.
5. Add a `README.md` to the plugin folder and a row to the table in the root `README.md`.
6. Add an entry to `CHANGELOG.md`.

Test a plugin locally with `claude --plugin-dir plugins/<plugin-name>`.

## Licensing and AI annotation

The repository follows the [REUSE specification](https://reuse.software).
Every file needs SPDX copyright and license information.

- Add headers with `reuse annotate`. Files that cannot hold a comment, or must
  start with YAML frontmatter (like `SKILL.md`), get a `.license` sidecar
  (`--force-dot-license`).
- New contributions are accepted under CC0-1.0.
- Mark AI-generated content as described in the
  [walberla-spdx-ai](plugins/walberla-spdx-ai/) plugin. In short: an AI-generated
  file gets `SPDX-FileCreatedBy` and `SPDX-FileCreatedUsing` tags in a separate
  comment block below the REUSE header. That plugin can do this for you.
- Run `reuse lint` before you open a pull request. CI runs it too.

## Tests

Plugins with tests have a `tests/run_tests.sh`. Run it from the plugin folder.
CI runs all of them.

## Contributors

Add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md) in your first pull request.
