#!/usr/bin/env bash
# Scan for committed secrets in the repository.
# Uses git grep for common patterns. For deeper scanning, use trufflehog or gitleaks
# installed locally in .tools/ (not globally).

set -euo pipefail

echo "=== Secret Scan ==="
FOUND=0

# Check for common secret patterns
patterns=(
    "AKIA[0-9A-Z]{16}"          # AWS access key
    "sk-[a-zA-Z0-9]{32,}"       # OpenAI-style key
    "nvapi-[a-zA-Z0-9_-]{20,}"  # NVIDIA API key
    "ghp_[a-zA-Z0-9]{36}"       # GitHub personal token
    "password\s*=\s*['\"][^'\"]*['\"]"  # Hardcoded password
)

for pattern in "${patterns[@]}"; do
    if git grep -nI -E "$pattern" -- ':!*.example' ':!scan_secrets*' 2>/dev/null; then
        echo "WARN: Possible secret found matching: $pattern"
        FOUND=1
    fi
done

# Check .env is not committed
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "FAIL: .env is tracked by git!"
    FOUND=1
fi

if [ $FOUND -eq 0 ]; then
    echo "PASS: No secrets found"
else
    echo "FAIL: Potential secrets detected. Review and rotate if needed."
    exit 1
fi
