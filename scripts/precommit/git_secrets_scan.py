"""Basic heuristic secret scan used as a lightweight git-secrets replacement."""
from __future__ import annotations

import re
import sys
from pathlib import Path

SUSPECT_PATTERN_TEXT = re.compile(
    # Catch common .env / yaml styles: TOKEN=abc... or TOKEN: abc...
    r"(?i)(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|SENTRY_DSN)\s*[:=]\s*[A-Za-z0-9/_-]{16,}"
)

SUSPECT_PATTERN_CODE = re.compile(
    # Catch hardcoded string literals in code: token = "abc..."
    r"(?i)(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|SENTRY_DSN)\s*[:=]\s*['\"][A-Za-z0-9/_-]{16,}['\"]"
)

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".woff",
    ".ttf",
    ".example",
}

SKIP_PATH_FRAGMENTS = {
    ".codex/",
    "/docs/",
    "/tests/",
    "/legacy/",
    "git_secrets_scan.py",
}


def should_skip(path: Path) -> bool:
    posix = path.as_posix()
    if any(fragment in posix for fragment in SKIP_PATH_FRAGMENTS):
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return path.is_dir()


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        pattern = SUSPECT_PATTERN_TEXT
        if path.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx"}:
            pattern = SUSPECT_PATTERN_CODE
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for no, line in enumerate(handle, start=1):
                if pattern.search(line):
                    findings.append(f"{path}:{no}")
    except Exception:
        return findings
    return findings


def expand_candidates(root: Path) -> list[Path]:
    if root.is_dir():
        return [p for p in root.rglob("*") if p.is_file()]
    return [root]


def main(args: list[str]) -> int:
    findings: list[str] = []
    candidates = args or ["."]
    for target in candidates:
        for path in expand_candidates(Path(target)):
            if should_skip(path):
                continue
            findings.extend(scan_file(path))

    if findings:
        print("❌ Potential secrets detected (keyword assignments):")
        for item in findings:
            print(f" - {item}")
        print("Hint: rotate the credential or move it to secret storage.")
        return 1

    print("✅ git-secrets scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
