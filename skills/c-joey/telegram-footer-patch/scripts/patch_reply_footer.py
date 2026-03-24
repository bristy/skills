#!/usr/bin/env python3
"""Patch OpenClaw dist JS bundles to append a Telegram private-chat footer.

Safety notes:
- This script modifies files under the OpenClaw installation directory.
- Always run with --dry-run first to see which files would be touched.
- The script creates timestamped backups (*.bak.telegram-footer.*) before writing.
- If anything fails, it restores from backup automatically.

This version tries to be resilient across OpenClaw bundle layouts:
- targets explicit likely bundles first
- optionally auto-discovers by content needle
- uses a self-contained footer formatter (no formatTokens dependency)
- supports both {text} and {html} payload shapes

Important boundary:
- patch/verify success only proves candidate bundle patching + syntax validity
- final acceptance still requires a real Telegram private-chat reply showing the footer
- do not treat static verification alone as proof of cross-version compatibility
"""

import argparse
import datetime as dt
import os
import pathlib
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

MARKER_START = "/* OPENCLAW_TELEGRAM_STATUS_FOOTER_START */"
MARKER_END = "/* OPENCLAW_TELEGRAM_STATUS_FOOTER_END */"

SNIPPET_TEMPLATE = r'''
__MARKER_START__
const __ocSessionLooksTelegramDirect =
  typeof sessionKey === "string" && sessionKey.includes(":telegram:direct:");
const __ocReplyProvider =
  sessionCtx?.Surface || sessionCtx?.Provider || activeSessionEntry?.lastChannel || activeSessionEntry?.channel || "";
const __ocReplyChatType =
  sessionCtx?.ChatType || activeSessionEntry?.chatType || "";
const __ocShouldAppendStatusFooter =
  (__ocSessionLooksTelegramDirect || __ocReplyProvider === "telegram") &&
  __ocReplyChatType !== "group" &&
  __ocReplyChatType !== "channel";

const __ocEscapeHtml = (str) => String(str)
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/\"/g, "&quot;")
  .replace(/'/g, "&#39;");

const __ocFormatTokens = (value) => {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "?";
  if (value >= 1000000) return `${(value / 1000000).toFixed(value >= 10000000 ? 0 : 1).replace(/\.0$/, "")}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 100000 ? 0 : 1).replace(/\.0$/, "")}k`;
  return String(Math.round(value));
};

const __ocBuildTokenUsage = (used, limit) => {
  const usedLabel = __ocFormatTokens(used);
  const limitLabel = __ocFormatTokens(limit);
  return limitLabel === "?" ? usedLabel : `${usedLabel}/${limitLabel}`;
};

const __ocAppendFooter = (payloads, footerText, footerHtml) => {
  let index = -1;
  for (let i = payloads.length - 1; i >= 0; i -= 1) {
    if (payloads[i]?.html || payloads[i]?.text) {
      index = i;
      break;
    }
  }

  if (index === -1) return [...payloads, { text: footerText }];

  const existing = payloads[index];

  if (existing?.html) {
    const existingHtml = existing.html ?? "";
    const sep = existingHtml.endsWith("<br>") ? "" : "<br>";
    const next = { ...existing, html: `${existingHtml}${sep}${footerHtml}` };
    const updated = payloads.slice();
    updated[index] = next;
    return updated;
  }

  if (existing?.text) {
    const existingText = existing.text ?? "";
    const separator = existingText.endsWith("\n") ? "" : "\n";
    const next = { ...existing, text: `${existingText}${separator}${footerText}` };
    const updated = payloads.slice();
    updated[index] = next;
    return updated;
  }

  return [...payloads, { text: footerText }];
};

if (__ocShouldAppendStatusFooter) {
  const __ocTotalTokens = resolveFreshSessionTotalTokens(activeSessionEntry);
  const __ocThinkingLevel = activeSessionEntry?.thinkingLevel || "default";
  const __ocContextLimit = contextTokensUsed ?? activeSessionEntry?.contextTokens ?? null;

  const __ocStatusFooter = [
    `🧠 ${providerUsed && modelUsed ? `${providerUsed}/${modelUsed}` : modelUsed || "unknown"}`,
    `💭 Think: ${__ocThinkingLevel}`,
    `📊 ${__ocBuildTokenUsage(__ocTotalTokens, __ocContextLimit)}`
  ].join(" ");

  const __ocFooterText = `\n──────────\n${__ocStatusFooter}`;
  const __ocFooterHtml = `──────────<br>${__ocEscapeHtml(__ocStatusFooter)}`;

  finalPayloads = __ocAppendFooter(finalPayloads, __ocFooterText, __ocFooterHtml);
}
__MARKER_END__
'''.strip("\n")

SNIPPET = (
    SNIPPET_TEMPLATE.replace("__MARKER_START__", MARKER_START)
    .replace("__MARKER_END__", MARKER_END)
)

PATTERN = re.compile(
    r"(if\s*\(\s*responseUsageLine\s*\)\s*finalPayloads\s*=\s*appendUsageLine\(\s*finalPayloads\s*,\s*responseUsageLine\s*\);)",
    flags=re.M,
)
MARKER_BLOCK_RE = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), flags=re.S)
NEEDLE_SUBSTR = "appendUsageLine(finalPayloads, responseUsageLine)"
TARGET_GLOBS = [
    "agent-runner.runtime-*.js",
    "reply-*.js",
    "compact-*.js",
    "pi-embedded-*.js",
    "plugin-sdk/thread-bindings-*.js",
    "model-selection-*.js",
    "auth-profiles-*.js",
]
LEGACY_BLOCK_RE = re.compile(
    r"\n?\s*const shouldAppendStatusFooter = activeSessionEntry\?\.chatType !== \"group\" && activeSessionEntry\?\.chatType !== \"channel\" && \(activeSessionEntry\?\.lastChannel === \"telegram\" \|\| activeSessionEntry\?\.channel === \"telegram\"\);\s*"
    r"if \(shouldAppendStatusFooter\) \{\s*"
    r"const totalTokens = resolveFreshSessionTotalTokens\(activeSessionEntry\);\s*"
    r"const statusFooter = \[\s*"
    r"`🧠 Model: \$\{providerUsed && modelUsed \? `\$\{providerUsed\}/\$\{modelUsed\}` : modelUsed \|\| \"unknown\"\}`\s*,\s*"
    r"`📊 Context: \$\{formatTokens\(typeof totalTokens === \"number\" && Number\.isFinite\(totalTokens\) && totalTokens > 0 \? totalTokens : null, contextTokensUsed \?\? activeSessionEntry\?\.contextTokens \?\? null\)\}`\s*"
    r"\]\.join\(\"  \"\);\s*"
    r"finalPayloads = appendUsageLine\(finalPayloads, statusFooter\);\s*"
    r"\}\s*",
    flags=re.S,
)


def verify_node_syntax(path: pathlib.Path):
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "node --check failed").strip()
        raise RuntimeError(details)


def _is_backup_path(path: pathlib.Path) -> bool:
    return ".bak.telegram-footer." in path.name


def _read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _looks_like_target_by_content(path: pathlib.Path) -> bool:
    text = _read_text(path)
    return NEEDLE_SUBSTR in text and bool(PATTERN.search(text))


def iter_target_files(dist: pathlib.Path, auto_discover: bool = False) -> list[pathlib.Path]:
    files: set[pathlib.Path] = set()
    for pattern in TARGET_GLOBS:
        for fp in dist.glob(pattern):
            if fp.is_file() and not _is_backup_path(fp):
                files.add(fp)

    if auto_discover:
        for fp in dist.rglob("*.js"):
            if not fp.is_file() or _is_backup_path(fp):
                continue
            try:
                if _looks_like_target_by_content(fp):
                    files.add(fp)
            except OSError:
                continue

    return sorted(files)


def analyze_file(path: pathlib.Path) -> dict:
    content = _read_text(path)
    has_marker = MARKER_START in content
    has_pattern = PATTERN.search(content) is not None
    has_legacy = LEGACY_BLOCK_RE.search(content) is not None
    is_candidate = has_marker or has_pattern or has_legacy
    return {
        "path": path,
        "content": content,
        "has_marker": has_marker,
        "has_pattern": has_pattern,
        "has_legacy": has_legacy,
        "is_candidate": is_candidate,
    }


def patch_file(path: pathlib.Path, dry_run: bool):
    info = analyze_file(path)
    content = info["content"]
    has_marker = info["has_marker"]
    has_legacy = info["has_legacy"]
    is_candidate = info["is_candidate"]
    if not is_candidate:
        print(f"[skip] non-target dist bundle: {path}")
        return {"status": "skip", "candidate": False, "changed": False}

    updated = content
    legacy_removed = 0
    if has_legacy:
        updated, legacy_removed = LEGACY_BLOCK_RE.subn("\n", updated)

    if MARKER_START in updated:
        updated, count = MARKER_BLOCK_RE.subn(lambda _m: SNIPPET, updated, count=1)
        if count == 0:
            print(f"[err] marker block found but could not be replaced: {path}", file=sys.stderr)
            return {"status": "error", "candidate": True, "changed": False}
        action = "update patch"
    else:
        match = PATTERN.search(updated)
        if not match:
            print(
                f"[err] insertion needle not found in candidate dist bundle: {path} (upstream dist likely changed; rework patch)",
                file=sys.stderr,
            )
            return {"status": "error", "candidate": True, "changed": False}
        replacement = match.group(1) + "\n\n" + SNIPPET
        updated = updated[: match.start()] + replacement + updated[match.end() :]
        action = "patch"

    changed = updated != content
    if not changed:
        print(f"[skip] already up to date: {path}")
        return {"status": "ok", "candidate": True, "changed": False}

    if dry_run:
        extra = f" (legacy cleaned: {legacy_removed})" if legacy_removed else ""
        print(f"[dry-run] would {action}: {path}{extra}")
        return {"status": "ok", "candidate": True, "changed": True}

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.telegram-footer.{ts}")
    shutil.copy2(path, backup)
    try:
        path.write_text(updated, encoding="utf-8")
        verify_node_syntax(path)
    except Exception as exc:
        shutil.copy2(backup, path)
        print(f"[err] patch failed, restored backup: {path}", file=sys.stderr)
        print(f"[err] reason: {exc}", file=sys.stderr)
        return {"status": "error", "candidate": True, "changed": False}

    extra = f" (legacy cleaned: {legacy_removed})" if legacy_removed else ""
    print(f"[ok] {action}ed: {path}{extra}")
    print(f"[ok] backup      : {backup}")
    print(f"[ok] syntax check: node --check passed")
    return {"status": "ok", "candidate": True, "changed": True}


def preflight(dist: pathlib.Path, dry_run: bool) -> int:
    print("[warn] This tool patches OpenClaw installation files (dist JS bundles).")
    print("[warn] Recommended: run --dry-run first and review the candidate files.")
    node_path = shutil.which("node")
    if not node_path:
        print("[err] node not found in PATH (required for syntax validation via node --check)", file=sys.stderr)
        return 2
    if not dist.exists() or not dist.is_dir():
        print(f"[err] dist directory not found: {dist}", file=sys.stderr)
        return 2
    if not dry_run:
        if not os.access(dist, os.W_OK):
            print(f"[err] no write permission for dist directory: {dist} (try sudo or adjust permissions)", file=sys.stderr)
            return 2
    else:
        if not os.access(dist, os.R_OK):
            print(f"[err] no read permission for dist directory: {dist}", file=sys.stderr)
            return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch OpenClaw dist files to append Telegram status footer.")
    parser.add_argument("--dist", default="/usr/lib/node_modules/openclaw/dist", help="OpenClaw dist directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write")
    parser.add_argument("--auto-discover", action="store_true", help="Also scan dist/**/*.js for the injection needle")
    parser.add_argument("--list-targets", action="store_true", help="Print resolved target file list, then exit")
    parser.add_argument("--verify", action="store_true", help="Exit non-zero if any real candidate file lacks the marker")
    args = parser.parse_args()

    dist = pathlib.Path(args.dist)
    rc = preflight(dist, dry_run=args.dry_run)
    if rc != 0:
        return rc

    files = iter_target_files(dist, auto_discover=args.auto_discover)
    if not files:
        print("[err] no target dist files found", file=sys.stderr)
        return 2

    if args.list_targets:
        for fp in files:
            info = analyze_file(fp)
            print(
                f"{fp}  candidate={str(info['is_candidate']).lower()}  marker={str(info['has_marker']).lower()}  needle={str(info['has_pattern']).lower()}  legacy={str(info['has_legacy']).lower()}"
            )
        return 0

    if args.verify:
        missing: list[pathlib.Path] = []
        candidate_count = 0
        for fp in files:
            info = analyze_file(fp)
            if not info["is_candidate"]:
                continue
            candidate_count += 1
            if not info["has_marker"]:
                missing.append(fp)
        if missing:
            for fp in missing:
                print(f"[err] marker missing in candidate: {fp}", file=sys.stderr)
            return 1
        print(f"[ok] marker present in {candidate_count} candidate target(s)")
        return 0

    changed = 0
    errors = 0
    for fp in files:
        result = patch_file(fp, dry_run=args.dry_run)
        if result.get("status") == "error":
            errors += 1
        if result.get("changed"):
            changed += 1

    if errors:
        print(f"[done] errors: {errors}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[done] changed files: {changed}" if changed else "[done] no files changed")
        return 0

    print(f"[done] changed files: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
