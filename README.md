<!--
SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
SPDX-FileContributor: Claude Code (claude-opus-5-5)

SPDX-License-Identifier: CC0-1.0
-->

<!--
SPDX-FileCreatedBy: Michael Zikeli
SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)
-->

# claude-skills

Claude Code plugins and skills by Michael Zikeli.
The repository is a Claude Code plugin marketplace.

## Plugins

| Plugin | Description |
|---|---|
| [walberla-spdx-ai](plugins/walberla-spdx-ai/) | Marks AI-generated code with SPDX/REUSE license headers and snippet markers, following the waLBerla AI policy. Works for all file types. |

## Installation

Inside Claude Code:

```
/plugin marketplace add Pitt0s/claude-skills
/plugin install walberla-spdx-ai@pitt0s
```

To try a plugin without installing it, clone this repository and start Claude Code
with the plugin folder:

```
claude --plugin-dir /path/to/claude-skills/plugins/walberla-spdx-ai
```

Each plugin's README lists its requirements and configuration.

## Repository layout

```
.claude-plugin/marketplace.json   marketplace manifest
plugins/<name>/                   one folder per plugin
LICENSES/                         license texts (REUSE)
REUSE.toml                        licensing of test fixtures
```

## Licensing

This repository follows the [REUSE specification](https://reuse.software).
Every file carries SPDX license information. Check it with `reuse lint`.

All content was created with AI assistance and is released under
[CC0-1.0](LICENSES/CC0-1.0.txt). AI-generated files are marked with
`SPDX-FileCreatedBy` and `SPDX-FileCreatedUsing` tags.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CONTRIBUTORS.md](CONTRIBUTORS.md).
