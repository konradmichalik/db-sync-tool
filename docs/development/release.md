# Release Guide

How to release a new version of db-sync-tool.

## Prerequisites

- Python 3.10+
- pip with `setuptools`, `wheel`, and `twine`
- PyPI account with upload permissions

## Release Steps

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
__version__ = "1.5.0"
```

### 3. Build Distribution

Install build tools (if needed):
```bash
python3 -m pip install --user --upgrade setuptools wheel
```

Generate the distribution archive:
```bash
python3 setup.py sdist bdist_wheel
```

This creates files in `dist/`:
- `db_sync_tool_kmi-1.5.0.tar.gz` (source)
- `db_sync_tool_kmi-1.5.0-py3-none-any.whl` (wheel)

### 4. Upload to PyPI

Install twine (if needed):
```bash
python3 -m pip install --user --upgrade twine pkginfo
```

Upload:
```bash
python3 -m twine upload dist/*
```

You'll be prompted for your PyPI credentials.

### 5. Create Git Tag

```bash
git tag v1.5.0
git push origin v1.5.0
```

### 6. Push to GitHub

```bash
git push origin main
```

### 7. Create GitHub Release

1. Go to [Releases](https://github.com/konradmichalik/db-sync-tool/releases)
2. Click "Draft a new release"
3. Select the tag you just created
4. Add release notes (copy from CHANGELOG)
5. Publish release

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
