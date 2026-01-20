#!/bin/bash
#
# Release script for db-sync-tool
# Usage: ./scripts/release.sh <version>
# Example: ./scripts/release.sh 3.0.0
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

confirm() {
    read -p "$1 [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 3.0.0"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"
DATE=$(date +%Y-%m-%d)

echo ""
echo "=========================================="
echo " db-sync-tool Release Script"
echo " Version: $VERSION"
echo " Tag: $TAG"
echo " Date: $DATE"
echo "=========================================="
echo ""

# Step 1: Pre-flight checks
info "Running pre-flight checks..."

# Check clean git state
if [ -n "$(git status --porcelain)" ]; then
    warn "Working directory is not clean:"
    git status --short
    if ! confirm "Continue anyway?"; then
        exit 1
    fi
fi

# Check we're on main/master branch
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" != "main" && "$BRANCH" != "master" ]]; then
    warn "Not on main/master branch (current: $BRANCH)"
    if ! confirm "Continue anyway?"; then
        exit 1
    fi
fi

# Check tag doesn't exist
if git tag -l | grep -q "^$TAG$"; then
    error "Tag $TAG already exists. Delete it first or use a different version."
fi

# Check required tools
command -v python3 >/dev/null 2>&1 || error "python3 is required"
command -v gh >/dev/null 2>&1 || warn "gh CLI not found - GitHub release will be manual"

success "Pre-flight checks passed"

# Step 2: Show current version
CURRENT_VERSION=$(grep '__version__' db_sync_tool/info.py | sed 's/.*"\(.*\)"/\1/')
info "Current version: $CURRENT_VERSION"
info "New version: $VERSION"
echo ""

if ! confirm "Proceed with version bump?"; then
    exit 0
fi

# Step 3: Update version in files
info "Updating version in files..."

# Update db_sync_tool/info.py
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" db_sync_tool/info.py
rm -f db_sync_tool/info.py.bak
success "Updated db_sync_tool/info.py"

# Update composer.json
sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" composer.json
rm -f composer.json.bak
success "Updated composer.json"

# Step 4: Update CHANGELOG.md
info "Updating CHANGELOG.md..."

if grep -q "## \[Unreleased\]" CHANGELOG.md; then
    sed -i.bak "s/## \[Unreleased\]/## [$VERSION] - $DATE/" CHANGELOG.md
    rm -f CHANGELOG.md.bak
    success "Updated CHANGELOG.md: [Unreleased] -> [$VERSION] - $DATE"
else
    warn "No [Unreleased] section found in CHANGELOG.md - skipping"
fi

# Step 5: Show changes
echo ""
info "Files changed:"
git diff --stat
echo ""
git diff db_sync_tool/info.py composer.json CHANGELOG.md

if ! confirm "Commit these changes?"; then
    info "Reverting changes..."
    git checkout -- db_sync_tool/info.py composer.json CHANGELOG.md
    exit 0
fi

# Step 6: Commit version bump
info "Committing version bump..."
git add db_sync_tool/info.py composer.json CHANGELOG.md
git commit -m "release: v$VERSION"
success "Created commit"

# Step 7: Create git tag
info "Creating git tag $TAG..."
git tag -a "$TAG" -m "Release $VERSION"
success "Created tag $TAG"

# Step 8: Build distribution
info "Building distribution..."
rm -rf build/ dist/ *.egg-info

# Use pipx for build tools (works with Homebrew Python)
if command -v pipx >/dev/null 2>&1; then
    pipx run build
else
    python3 -m pip install --user --quiet --upgrade setuptools wheel build
    python3 -m build
fi

success "Built distribution:"
ls -la dist/

# Step 9: Upload to PyPI
echo ""
if confirm "Upload to PyPI?"; then
    info "Uploading to PyPI..."
    if command -v pipx >/dev/null 2>&1; then
        pipx run twine upload dist/*
    else
        python3 -m pip install --user --quiet --upgrade twine
        python3 -m twine upload dist/*
    fi
    success "Uploaded to PyPI"
else
    warn "Skipped PyPI upload"
    info "To upload later: pipx run twine upload dist/*"
fi

# Step 10: Push to remote
echo ""
if confirm "Push commits and tag to origin?"; then
    info "Pushing to origin..."
    git push origin "$BRANCH"
    git push origin "$TAG"
    success "Pushed to origin"
else
    warn "Skipped push"
    info "To push later:"
    echo "  git push origin $BRANCH"
    echo "  git push origin $TAG"
fi

# Step 11: Create GitHub Release
echo ""
if command -v gh >/dev/null 2>&1; then
    if confirm "Create GitHub Release?"; then
        info "Creating GitHub Release..."

        # Check if release notes file exists
        if [ -f "RELEASE_NOTES_v3.md" ] && [[ "$VERSION" == 3.* ]]; then
            gh release create "$TAG" \
                --title "$TAG" \
                --notes-file RELEASE_NOTES_v3.md \
                dist/*
        else
            # Extract notes from CHANGELOG
            gh release create "$TAG" \
                --title "$TAG" \
                --generate-notes \
                dist/*
        fi
        success "Created GitHub Release"
    else
        warn "Skipped GitHub Release"
        info "To create later: gh release create $TAG --title \"$TAG\" --generate-notes dist/*"
    fi
else
    info "Install gh CLI to create releases automatically:"
    echo "  brew install gh  # macOS"
    echo "  apt install gh   # Ubuntu"
fi

# Done
echo ""
echo "=========================================="
echo -e "${GREEN} Release $VERSION complete!${NC}"
echo "=========================================="
echo ""
echo "Verify:"
echo "  - PyPI: https://pypi.org/project/db-sync-tool-kmi/"
echo "  - GitHub: https://github.com/konradmichalik/db-sync-tool/releases"
echo "  - Install: pip install db-sync-tool-kmi==$VERSION"
echo ""
