# Release Guide

How to release a new version of db-sync-tool.

## Quick Release (Recommended)

Use the automated release script:

```bash
./scripts/release.sh 3.0.0
```

The script handles all steps interactively:
- Pre-flight checks (clean git state, correct branch, tag availability)
- Version bump in `info.py` and `composer.json`
- Changelog update (`[Unreleased]` → `[3.0.0] - 2024-01-20`)
- Build distribution
- PyPI upload
- Git tag and push
- GitHub Release creation

## Prerequisites

- Python 3.10+
- pip with `setuptools`, `wheel`, `build`, and `twine`
- PyPI account with upload permissions
- GitHub CLI (`gh`) for automated releases (optional)

Install prerequisites:
```bash
pip install --upgrade setuptools wheel build twine
brew install gh  # macOS
```

## Manual Release Steps

If you prefer to release manually or need to debug issues:

### 1. Update Changelog

Update the [CHANGELOG.md](https://github.com/konradmichalik/db-sync-tool/blob/main/CHANGELOG.md) with all changes since the last release.

### 2. Bump Version

Update the version number according to [Semantic Versioning](https://semver.org/):

| File | Location |
|------|----------|
| `db_sync_tool/info.py` | `__version__` |
| `composer.json` | `"version"` |

Example:
```python
# db_sync_tool/info.py
__version__ = "3.0.0"
```

### 3. Build Distribution

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build
python3 -m build
```

This creates files in `dist/`:
- `db_sync_tool_kmi-3.0.0.tar.gz` (source)
- `db_sync_tool_kmi-3.0.0-py3-none-any.whl` (wheel)

### 4. Upload to PyPI

```bash
python3 -m twine upload dist/*
```

You'll be prompted for your PyPI credentials.

### 5. Create Git Tag and Push

```bash
git add db_sync_tool/info.py composer.json CHANGELOG.md
git commit -m "release: v3.0.0"
git tag -a v3.0.0 -m "Release 3.0.0"
git push origin main
git push origin v3.0.0
```

### 6. Create GitHub Release

Using GitHub CLI:
```bash
gh release create v3.0.0 --title "v3.0.0" --generate-notes dist/*
```

Or with custom release notes:
```bash
gh release create v3.0.0 --title "v3.0.0" --notes-file RELEASE_NOTES_v3.md dist/*
```

Or manually:
1. Go to [Releases](https://github.com/konradmichalik/db-sync-tool/releases)
2. Click "Draft a new release"
3. Select the tag you just created
4. Add release notes
5. Attach dist files
6. Publish release

## Verification

After release, verify:

- [PyPI package](https://pypi.org/project/db-sync-tool-kmi/) shows new version
- [Packagist](https://packagist.org/packages/kmi/db-sync-tool) is updated
- Installation works: `pip install db-sync-tool-kmi==1.5.0`

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

| Change | Version | Example |
|--------|---------|---------|
| Major (breaking) | X.0.0 | 2.0.0 |
| Minor (features) | 1.X.0 | 1.5.0 |
| Patch (fixes) | 1.4.X | 1.4.1 |

## Troubleshooting

### Upload Failed

- Check PyPI credentials
- Verify version doesn't already exist
- Ensure `twine` is up to date

### Tag Already Exists

```bash
# Delete local tag
git tag -d v1.5.0

# Delete remote tag (if pushed)
git push origin :refs/tags/v1.5.0
```

### Build Issues

Clean previous builds:
```bash
rm -rf build/ dist/ *.egg-info
```
