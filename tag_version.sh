#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: ./tag_version.sh <version> [--dry-run]"
  exit 1
fi

VERSION="$1"
DRY_RUN="${2:-}"

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must follow semantic versioning, for example 0.2.0"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYPROJECT="$ROOT_DIR/pyproject.toml"
CHANGELOG="$ROOT_DIR/CHANGELOG.md"
TODAY="$(date +%F)"

echo "Preparing release $VERSION"
echo "Project root: $ROOT_DIR"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "[dry-run] Would update version in pyproject.toml"
  echo "[dry-run] Would prepend changelog entry to CHANGELOG.md"
  echo "[dry-run] Would create git tag v$VERSION"
  exit 0
fi

python3 - <<PY
from pathlib import Path
import re

pyproject = Path("$PYPROJECT")
content = pyproject.read_text()
updated = re.sub(r'^version = "[^"]+"$', 'version = "$VERSION"', content, count=1, flags=re.M)
if updated == content:
    raise SystemExit("Could not update version in pyproject.toml")
pyproject.write_text(updated)
PY

python3 - <<PY
from pathlib import Path

changelog = Path("$CHANGELOG")
content = changelog.read_text()
entry = f"## [$VERSION] - $TODAY\\n\\n- Release $VERSION\\n\\n"
if entry in content:
    raise SystemExit("Changelog entry already exists")
parts = content.split("\\n", 3)
if len(parts) < 3:
    raise SystemExit("Unexpected changelog format")
updated = parts[0] + "\\n\\n" + entry + "\\n".join(parts[2:])
changelog.write_text(updated)
PY

git add pyproject.toml CHANGELOG.md
git commit -m "chore: release $VERSION"
git tag "v$VERSION"

echo "Release $VERSION prepared."
echo "Next steps:"
echo "  1. Review the commit"
echo "  2. Push the branch and tag"
echo "  3. Create the GitHub release if needed"
