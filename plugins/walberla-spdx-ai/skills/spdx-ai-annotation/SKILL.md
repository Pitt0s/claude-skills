---
name: spdx-ai-annotation
description: Mark AI-generated code and files with SPDX/REUSE license headers and snippet markers, following the waLBerla AI policy. Use whenever you create a new file, add new logic to an existing file, or when the user asks to annotate, lint or fix SPDX, REUSE or AI markers. Works for all file types.
---

# SPDX/REUSE annotation of AI-generated content

You are an AI agent. Any creative content you write in this repository must be
marked as AI-generated. This skill tells you how. Follow it every time you write
files. Do not wait to be asked.

Headers are written and checked with the REUSE tool (`reuse`, https://reuse.software).
Do not write file headers by hand. `reuse` knows the correct comment style for
each file type and uses a `.license` sidecar file for binaries.

## 0. Prerequisites (once per session)

1. Check that `reuse --version` works. If not, ask the user to install it
   (`pipx install reuse`). Do not continue annotating without it.
2. Read `.spdx-ai.json` in the repository root if it exists. Keys:
   `project_license`, `ai_license` (default `CC0-1.0`), `ai_copyright`
   (`"human"` or `"NONE"`, see step 5), `core_paths`, `exclude_paths`,
   `annotate_args` (extra arguments for `reuse annotate`).
3. Collect metadata:
   - Human: `git config user.name` and `git config user.email`. If empty, ask. Never invent a name.
   - Agent: `Claude Code (<model id>)`, for example `Claude Code (claude-opus-5-5)`.
     Take the model id from your system prompt.
4. Detect the licenses:
   ```
   python3 <this skill's directory>/scripts/check_spdx.py --project-license <repo root>
   ```
   - `license` is the project license. It comes from `.spdx-ai.json`, the `LICENSES/`
     folder or the root `LICENSE`/`COPYING` file, in that order.
   - If `ambiguous` is true (for example GPL text cannot tell `-only` from `-or-later`),
     ask the user which one applies. Suggest saving it as `project_license` in `.spdx-ai.json`.
   - If `missing_in_LICENSES` is not empty, `reuse lint` will fail. Tell the user and,
     after a yes, run `reuse download <SPDX-ID>` for each missing license.
5. Decide the copyright holder for AI content:
   - If `ai_copyright` is set in `.spdx-ai.json`, use it.
   - Otherwise ask the user once per session: copyright line with their name
     (default), or no copyright holder (`NONE`).
   - Use `NONE` only after the user explicitly chose it. It is written as
     `SPDX-FileCopyrightText: NONE`, so such files stay searchable.
   - Never omit the copyright line. REUSE requires one on every file.

## 1. Decide what kind of change you are making

| Your change | License | What to do |
|---|---|---|
| **Refactoring**: renaming, bug fixes, formatting, localized modernization, moving or splitting existing code | unchanged | **No marker.** Refactoring is not creative work. Keep the existing header. If you move code into a new file, copy the original file's copyright and license lines into the new file. |
| **New file**, fully written by you | `ai_license` (CC0-1.0) unless the user wants another license | AI file header (section 2a) |
| **New logic** added to an existing human-written file | `ai_license` | AI snippet (section 2b). Keep the file header untouched. |
| Any change in a file that already has an AI file header | as in the header | No extra marker |
| Annotating an existing human-written file on request | project license | `reuse annotate` with the human's data, no AI markers |
| New logic in a **core path** (`core_paths`) | - | **STOP.** The policy excludes AI-generated code in the core. Explain this and ask the user. Refactoring in the core is fine. |
| User wants a mixed file to become fully AI-licensed | - | Only the human authors can decide this. All authors must agree. Ask for explicit confirmation first. |

Rules that always apply:
- When in doubt whether something is refactoring or new logic, ask the user.
- Never add a human-authored header with a guessed author or year.
- Never remove or change SPDX lines written by humans.
- Licensing decisions belong to the human. You only execute them.
- Documentation or code that only *shows* SPDX tags as examples (not real license
  info) must be wrapped in `REUSE-IgnoreStart` / `REUSE-IgnoreEnd` comments, so
  `reuse` and the checker do not read them as tags.

<!-- REUSE-IgnoreStart -->

## 2. How to annotate

### 2a. AI file header (new file written by you)

Step 1: write the header with `reuse`:

```
reuse annotate \
  --copyright "<Human Name> <human@mail>" \
  --license "<ai_license>" \
  --contributor "<Agent Name>" \
  <annotate_args> --fallback-dot-license <file>
```

If the user chose `NONE`, use `--copyright NONE --exclude-year` instead.
This writes exactly `SPDX-FileCopyrightText: NONE`.

Step 2: add the policy block **as a separate comment directly below** the header,
in the same comment style that `reuse` used. Keep a blank line between the blocks.
`reuse annotate` rewrites its own header block, and a separate block survives that.

C/C++ example (after both steps):

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

Python, shell, CMake, YAML and similar use `#` comments instead. Shebang and
encoding lines stay at the very top. `reuse` handles that.

Files that must start with YAML frontmatter (`SKILL.md`, Jekyll or Hugo pages)
and files that must start with a fixed line other than a shebang: use
`--force-dot-license`, so the file itself stays untouched.

If `reuse` created a `.license` sidecar (binary or unknown file type), append the
two policy lines to the sidecar file without comment characters.

### 2b. AI snippet (new logic inside a human-written file)

`reuse annotate` cannot write snippets. Write them yourself, in the comment syntax
of that file. Use this order of tags:

```
/**
 * SPDX-SnippetBegin
 * SPDX-SnippetCopyrightText: <Year> <Human Name> <human@mail>
 * SPDX-License-Identifier: CC0-1.0
 * SPDX-SnippetCreatedBy: <Human Name>
 * SPDX-SnippetCreatedUsing: <Agent Name>
 */

... generated code ...

/* SPDX-SnippetEnd */
```

`#`-comment example:

```
# SPDX-SnippetBegin
# SPDX-SnippetCopyrightText: 2026 Jane Doe <jane@example.org>
# SPDX-License-Identifier: CC0-1.0
# SPDX-SnippetCreatedBy: Jane Doe
# SPDX-SnippetCreatedUsing: Claude Code (claude-opus-5-5)

def generated_helper():
    ...

# SPDX-SnippetEnd
```

If the user chose `NONE`, write `SPDX-SnippetCopyrightText: NONE`.

Snippet rules:
- One snippet per contiguous generated block. Keep it tight.
- Never nest snippets. If you extend code inside or right next to an existing AI
  snippet, extend that snippet instead of opening a new one.
- Every `SPDX-SnippetBegin` needs exactly one `SPDX-SnippetEnd`.
- If the file format has no comments at all (for example JSON), you cannot mark a
  snippet. Ask the user: move the generated part to its own file, or mark the whole
  file with a `.license` sidecar.

<!-- REUSE-IgnoreEnd -->

## 3. Verify

Run the checker on every file you created or changed:

```
python3 <this skill's directory>/scripts/check_spdx.py <files>
```

It runs `reuse lint-file` and adds the AI-specific checks: snippet pairing,
complete markers, placeholders, deprecated IDs like `CC-0`, and core paths.
Fix every error before you report the task as done. If the plugin hook is
installed, this check also runs after each Write or Edit.

For a full repository check, `reuse lint` is the reference. Expect many errors
in legacy repositories that are not yet REUSE-compliant. Do not fix those
unless asked.

## 4. Report

In your final message, list:
- files with a new AI header or AI snippet,
- license files you downloaded,
- every case where you stopped and asked instead of annotating.
