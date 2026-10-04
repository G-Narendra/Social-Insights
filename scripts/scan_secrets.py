"""
Secret scanner for git-tracked files in the repository.
Runs regex scans against sensitive credential patterns and ensures .env is untracked.
"""

from __future__ import annotations

import re
import subprocess
import sys

PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
    (r"nvapi-[a-zA-Z0-9_-]{20,}", "NVIDIA NIM API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Token"),
    (r"password\s*=\s*['\"][^'\"]*['\"]", "Hardcoded Password Assignment"),
]

EXCLUDE_EXTENSIONS = [".example", ".png", ".jpg", ".webp", ".lock"]
EXCLUDE_FILES = ["scan_secrets.py", "scan_secrets.sh", "package-lock.json"]


def main() -> int:
    print("=== Secret Scan ===")
    found = 0

    # 1. Verify .env is not tracked
    try:
        res = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print("FAIL: .env is tracked by git!")
            found += 1
    except Exception as e:
        print(f"Error checking .env: {e}")

    # 2. Get list of tracked files
    tracked_res = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_files = tracked_res.stdout.splitlines()

    for file_path in tracked_files:
        if any(file_path.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
            continue
        if any(file_path.endswith(f) for f in EXCLUDE_FILES):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for pat, desc in PATTERNS:
                        if re.search(pat, line):
                            print(f"WARN: Possible {desc} found in {file_path}:{line_num}")
                            found += 1
        except Exception:
            pass

    if found == 0:
        print("PASS: No hardcoded secrets or credentials detected across tracked files.")
        return 0
    else:
        print(f"FAIL: {found} potential secret(s) found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
