#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Michael Zikeli <63597338+Pitt0s@users.noreply.github.com>
# SPDX-FileContributor: Claude Code (claude-opus-5-5)
#
# SPDX-License-Identifier: CC0-1.0

# SPDX-FileCreatedBy: Michael Zikeli
# SPDX-FileCreatedUsing: Claude Code (claude-opus-5-5)

"""
Check SPDX/REUSE compliance and AI-annotation markers.

Wraps `reuse lint-file` (https://reuse.software) and adds the checks that reuse
does not do: AI markers, snippet pairing, core paths, placeholders.

Usage:
  check_spdx.py FILE [FILE ...]   lint mode (CI, pre-commit, manual use)
  check_spdx.py --hook            Claude Code PostToolUse hook (JSON on stdin)
  check_spdx.py --project-license [DIR]
                                  print the detected project license as JSON

Options:
  --no-header-check   ignore missing copyright/license info (legacy files)
  --config PATH       explicit path to .spdx-ai.json

Exit codes:
  lint mode: 0 = ok, 1 = errors found
  hook mode: 0 = ok, 2 = errors found (stderr is shown to Claude)

Only the Python standard library is needed. If the `reuse` tool is not
installed, a reduced built-in header check is used and a warning is printed.
"""

import json
import os
import re
import shutil
import subprocess
import sys

# REUSE-IgnoreStart (tag names below are code, not license info)

DEPRECATED_IDS = {"CC-0": "CC0-1.0", "CC0": "CC0-1.0"}
DEFAULT_AGENT_PATTERN = r"(?i)\b(claude|copilot|chatgpt|gpt-?\d|gemini|codex|cursor|llm|agent)\b"
PLACEHOLDER = re.compile(
    r"\[(Year|Author|Human|LLM|Agent)[^\]]*\]|<(Human|Agent|Author|Year)[^>@]*>")
TAG = re.compile(r"SPDX-([A-Za-z-]+)\s*:?\s*(.*?)\s*(\*/|-->|\*\)|-\})?\s*$")
MISSING_INFO = ("no copyright notice", "no license identifier")

LICENSE_FILES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "LICENCE", "LICENCE.txt",
                 "COPYING", "COPYING.txt", "COPYING.md")


# --------------------------------------------------------------------------- config

def find_root(start):
    d = os.path.abspath(start if os.path.isdir(start) else os.path.dirname(start))
    while True:
        if os.path.exists(os.path.join(d, ".git")) or os.path.isfile(os.path.join(d, ".spdx-ai.json")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def load_config(start, explicit=None):
    cfg = {"core_paths": [], "exclude_paths": [], "project_license": None,
           "ai_license": "CC0-1.0", "agent_pattern": DEFAULT_AGENT_PATTERN}
    root = find_root(start)
    path = explicit or (os.path.join(root, ".spdx-ai.json") if root else None)
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            cfg.update(json.load(fh))
        root = root or os.path.dirname(os.path.abspath(path))
    return cfg, root


def rel_to_root(path, root):
    if root is None:
        return path.replace(os.sep, "/")
    return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")


def in_paths(rel, prefixes):
    for p in prefixes:
        p = p.strip("/")
        if p and (rel == p or rel.startswith(p + "/")):
            return True
    return False


# --------------------------------------------------------------- project license

def _guess_from_text(text):
    t = " ".join(text.split())
    if "GNU LESSER GENERAL PUBLIC LICENSE" in t:
        v = "3.0" if "Version 3" in t else "2.1"
        return ["LGPL-%s-or-later" % v, "LGPL-%s-only" % v]
    if "GNU AFFERO GENERAL PUBLIC LICENSE" in t:
        return ["AGPL-3.0-or-later", "AGPL-3.0-only"]
    if "GNU GENERAL PUBLIC LICENSE" in t:
        v = "3.0" if "Version 3" in t else "2.0"
        return ["GPL-%s-or-later" % v, "GPL-%s-only" % v]
    if "Apache License" in t and "Version 2.0" in t:
        return ["Apache-2.0"]
    if "Mozilla Public License Version 2.0" in t:
        return ["MPL-2.0"]
    if "Permission is hereby granted, free of charge" in t:
        return ["MIT"]
    if "Redistribution and use in source and binary forms" in t:
        return ["BSD-3-Clause"] if "Neither the name" in t else ["BSD-2-Clause"]
    if "free and unencumbered software released into the public domain" in t:
        return ["Unlicense"]
    return []


def detect_project_license(root, cfg):
    """Return a dict describing the project license and how it was found."""
    res = {"license": None, "ambiguous": False, "candidates": [], "source": None,
           "ai_license": cfg.get("ai_license", "CC0-1.0"), "licenses_dir": [], "missing_in_LICENSES": []}
    lic_dir = os.path.join(root, "LICENSES") if root else None
    if lic_dir and os.path.isdir(lic_dir):
        res["licenses_dir"] = sorted(os.path.splitext(f)[0] for f in os.listdir(lic_dir))

    if cfg.get("project_license"):
        res.update(license=cfg["project_license"], source=".spdx-ai.json")
    else:
        own = [l for l in res["licenses_dir"] if l != res["ai_license"]]
        if len(own) == 1:
            res.update(license=own[0], source="LICENSES/")
        elif len(own) > 1:
            res.update(ambiguous=True, candidates=own, source="LICENSES/")
        else:
            for name in LICENSE_FILES:
                p = os.path.join(root or ".", name)
                if os.path.isfile(p):
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        cands = _guess_from_text(fh.read())
                    res["source"] = name
                    res["candidates"] = cands
                    if len(cands) == 1:
                        res["license"] = cands[0]
                    elif cands:
                        res["ambiguous"] = True
                    break
    wanted = [x for x in (res["license"], res["ai_license"]) if x]
    res["missing_in_LICENSES"] = [x for x in wanted if x not in res["licenses_dir"]]
    return res


# ------------------------------------------------------------- structural checks

def read_text(path):
    """Return lines of a text file, or None for binary/unreadable files."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace").splitlines()


# Built by concatenation so this file does not end its own ignore region.
IGNORE_START = "REUSE-" + "IgnoreStart"
IGNORE_END = "REUSE-" + "IgnoreEnd"


def ignored_lines(lines):
    """Line numbers inside REUSE ignore regions (start/end markers)."""
    skip, inside = set(), False
    for i, line in enumerate(lines, start=1):
        if IGNORE_START in line:
            inside = True
        if inside:
            skip.add(i)
        if IGNORE_END in line:
            inside = False
    return skip


def parse_tags(lines):
    out = []
    skip = ignored_lines(lines)
    for i, line in enumerate(lines, start=1):
        if i in skip or "SPDX-" not in line:
            continue
        m = re.search(r"SPDX-[A-Za-z][A-Za-z-]*", line)
        if m is None:
            continue
        t = TAG.match(line[m.start():])
        if t:
            out.append((i, t.group(1), t.group(2)))
    return out


def structural_check(path, lines, cfg, rel):
    errors, warnings = [], []
    tags = parse_tags(lines)
    agent_re = re.compile(cfg.get("agent_pattern") or DEFAULT_AGENT_PATTERN)

    skip = ignored_lines(lines)
    for i, line in enumerate(lines, start=1):
        if i not in skip and "SPDX-" in line and PLACEHOLDER.search(line):
            errors.append("line %d: unfilled placeholder in SPDX tag" % i)

    for n, k, v in tags:
        if k == "License-Identifier":
            for bad, good in DEPRECATED_IDS.items():
                if re.search(r"(^|[\s(])%s($|[\s)])" % re.escape(bad), v):
                    errors.append("line %d: '%s' is not a valid SPDX identifier, use '%s'" % (n, bad, good))

    # file-level AI markers (outside snippets)
    in_snip = False
    file_tags = {}
    for n, k, v in tags:
        if k == "SnippetBegin":
            in_snip = True
        elif k == "SnippetEnd":
            in_snip = False
        elif not in_snip:
            file_tags.setdefault(k, []).append((n, v))
    has_by = "FileCreatedBy" in file_tags
    has_using = "FileCreatedUsing" in file_tags
    if has_by != has_using:
        errors.append("file-level AI marker incomplete: need both SPDX-FileCreatedBy and SPDX-FileCreatedUsing")
    agent_contrib = [n for n, v in file_tags.get("FileContributor", []) if agent_re.search(v)]
    if agent_contrib and not has_using:
        errors.append("line %d: an AI agent is listed as SPDX-FileContributor, but the "
                      "SPDX-FileCreatedBy/SPDX-FileCreatedUsing block is missing (maybe removed by "
                      "`reuse annotate`); restore it" % agent_contrib[0])

    # snippets
    open_at, meta, ai_snips = None, {}, 0
    def close(line):
        is_ai = "SnippetCreatedUsing" in meta or "SnippetCreatedBy" in meta
        if not is_ai:
            return 0
        for k in ("SnippetCreatedBy", "SnippetCreatedUsing", "License-Identifier", "SnippetCopyrightText"):
            if not meta.get(k):
                errors.append("line %d: AI snippet without SPDX-%s" % (line, k))
        return 1
    for n, k, v in tags:
        if k == "SnippetBegin":
            if open_at is not None:
                errors.append("line %d: nested SPDX-SnippetBegin (previous one opened at line %d)" % (n, open_at))
                ai_snips += close(open_at)
            open_at, meta = n, {}
        elif k == "SnippetEnd":
            if open_at is None:
                errors.append("line %d: SPDX-SnippetEnd without SPDX-SnippetBegin" % n)
            else:
                ai_snips += close(open_at)
            open_at = None
        elif open_at is not None:
            meta.setdefault(k, v)
    if open_at is not None:
        ai_snips += close(open_at)
        errors.append("line %d: SPDX-SnippetBegin without SPDX-SnippetEnd" % open_at)

    if has_using and ai_snips:
        warnings.append("file is already marked as AI-generated; AI snippet markers are redundant")

    if in_paths(rel, cfg.get("core_paths", [])) and (has_using or ai_snips or agent_contrib):
        errors.append("file is in a core path (%s); the AI policy excludes AI-generated code in the core"
                      % ", ".join(cfg["core_paths"]))
    return errors, warnings


def fallback_header_check(lines):
    tags = {k for _, k, _ in parse_tags(lines or [])}
    errs = []
    if "FileCopyrightText" not in tags:
        errs.append("no copyright notice")
    if "License-Identifier" not in tags:
        errs.append("no license identifier")
    return errs


# ------------------------------------------------------------------------- reuse

def run_reuse(paths, root):
    """Return {path: [messages]} from `reuse lint-file`, or None if reuse is missing."""
    exe = shutil.which("reuse")
    if exe is None:
        return None
    absr = {os.path.abspath(p): p for p in paths}
    try:
        cmd = [exe] + (["--root", root] if root else []) + ["lint-file", "--lines"] + list(absr)
        proc = subprocess.run(cmd, cwd=root or None,
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {p: ["could not run reuse: %s" % exc] for p in paths}
    out = {}
    for line in (proc.stdout + proc.stderr).splitlines():
        if ": " not in line:
            continue
        fpath, msg = line.rsplit(": ", 1) if line.count(": ") > 1 else line.split(": ", 1)
        cand = os.path.abspath(os.path.join(root or ".", fpath)) if not os.path.isabs(fpath) else fpath
        key = absr.get(cand, fpath)
        out.setdefault(key, []).append(msg.strip())
    return out


# -------------------------------------------------------------------------- main

def check_files(paths, cfg_path, require_header):
    results = {}
    by_root = {}
    for p in paths:
        if p.endswith(".license") and os.path.isfile(p[:-len(".license")]):
            p = p[:-len(".license")]
        if not os.path.isfile(p):
            continue
        cfg, root = load_config(p, cfg_path)
        rel = rel_to_root(p, root)
        if in_paths(rel, cfg.get("exclude_paths", [])):
            continue
        by_root.setdefault(root, []).append(p)
        lines = read_text(p)
        sidecar = p + ".license"
        if os.path.isfile(sidecar):
            lines = read_text(sidecar)
        errors, warnings = structural_check(p, lines or [], cfg, rel)
        results[p] = {"errors": errors, "warnings": warnings, "lines": lines}

    for root, files in by_root.items():
        reuse_out = run_reuse(files, root)
        for p in files:
            r = results[p]
            if reuse_out is None:
                r["warnings"].append("reuse is not installed (pipx install reuse); using a reduced header check")
                msgs = fallback_header_check(r["lines"])
            else:
                msgs = reuse_out.get(p, [])
            for m in msgs:
                if not require_header and m in MISSING_INFO:
                    continue
                if m.startswith("missing license"):
                    if any("'%s'" % bad in m for bad in DEPRECATED_IDS):
                        continue  # already reported as invalid identifier
                    m += " (add it with `reuse download <SPDX-ID>`)"
                r["errors"].append("reuse: " + m)
    return results


def report(results, stream):
    failed = False
    for p, r in results.items():
        for e in r["errors"]:
            print("%s: error: %s" % (p, e), file=stream)
            failed = True
        for w in r["warnings"]:
            print("%s: warning: %s" % (p, w), file=stream)
    return failed


def main(argv):
    cfg_path, require_header, hook, files = None, True, False, []
    it = iter(argv)
    for a in it:
        if a == "--hook":
            hook = True
        elif a == "--no-header-check":
            require_header = False
        elif a == "--config":
            cfg_path = next(it, None)
        elif a == "--project-license":
            start = next(it, ".")
            cfg, root = load_config(start, cfg_path)
            print(json.dumps(detect_project_license(root or os.path.abspath(start), cfg), indent=2))
            return 0
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            files.append(a)

    if hook:
        try:
            data = json.load(sys.stdin)
        except ValueError:
            return 0
        tin = data.get("tool_input", {}) or {}
        path = tin.get("file_path") or tin.get("notebook_path")
        if not path or not os.path.isfile(path):
            return 0
        # Write = new or fully rewritten file -> header required.
        # Edit on legacy files without header -> only marker checks.
        results = check_files([path], cfg_path, require_header=(data.get("tool_name") == "Write"))
        for r in results.values():
            r["warnings"] = [w for w in r["warnings"] if "reuse is not installed" in w]
        if report(results, sys.stderr):
            print("Fix this according to the spdx-ai-annotation skill before continuing.", file=sys.stderr)
            return 2
        return 0

    if not files:
        print(__doc__, file=sys.stderr)
        return 1
    return 1 if report(check_files(files, cfg_path, require_header), sys.stdout) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# REUSE-IgnoreEnd
