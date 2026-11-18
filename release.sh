#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./release.sh [-major | -minor | -hotfix]"
  echo ""
  echo "  -major   Bump major version  (x.0.0)"
  echo "  -minor   Bump minor version  (0.x.0)"
  echo "  -hotfix  Bump patch version  (0.0.x)"
  exit 1
}

JS_PKG="javascript/package.json"
PY_PKG="python/pyproject.toml"
BUMP=""

for arg in "$@"; do
  case "$arg" in
    -major)  BUMP="major" ;;
    -minor)  BUMP="minor" ;;
    -hotfix) BUMP="patch" ;;
    *) echo "Unknown flag: $arg"; usage ;;
  esac
done

[ -z "$BUMP" ] && usage

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree is dirty. Commit or stash changes first."
  exit 1
fi

# Both packages are kept in lockstep — read from JS package.json
CURRENT=$(node -p "require('./${JS_PKG}').version")
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "Bumping $CURRENT → $NEW_VERSION ($BUMP)"

# Bump javascript/package.json
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('${JS_PKG}', 'utf8'));
pkg.version = '$NEW_VERSION';
fs.writeFileSync('${JS_PKG}', JSON.stringify(pkg, null, 2) + '\n');
"

# Bump javascript/src/index.js
node -e "
const fs = require('fs');
let content = fs.readFileSync('javascript/src/index.js', 'utf8');
content = content.replace(/return '\d+\.\d+\.\d+';/, \"return '$NEW_VERSION';\");
fs.writeFileSync('javascript/src/index.js', content);
"

# Bump python/pyproject.toml
PY_CURRENT=$(grep '^version' "$PY_PKG" | head -1 | sed 's/version = "\(.*\)"/\1/')
sed -i.bak "s/^version = \"${PY_CURRENT}\"/version = \"${NEW_VERSION}\"/" "$PY_PKG" && rm "${PY_PKG}.bak"

# Bump python/asoba/__init__.py
python3 -c "
import re
with open('python/asoba/__init__.py', 'r') as f:
    c = f.read()
c = re.sub(r'__version__ = \"\d+\.\d+\.\d+\"', f'__version__ = \"$NEW_VERSION\"', c)
with open('python/asoba/__init__.py', 'w') as f:
    f.write(c)
"

git add "$JS_PKG" "$PY_PKG" "javascript/src/index.js" "python/asoba/__init__.py"
git commit -m "chore: bump version to ${NEW_VERSION}"
git push

gh release create "v${NEW_VERSION}" \
  --title "v${NEW_VERSION}" \
  --generate-notes \
  --repo AsobaCloud/sdk

echo ""
echo "✓ Released v${NEW_VERSION} — GitHub Actions will publish @asobacloud/sdk to npm and asoba to PyPI automatically."
