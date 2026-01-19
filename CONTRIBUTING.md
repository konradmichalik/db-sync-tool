# Contributing

Thank you for your interest in contributing to db-sync-tool!

## 🛠️ Setup

```bash
# Clone the repository
git clone https://github.com/konradmichalik/db-sync-tool.git
cd db-sync-tool

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

**Requirements:** Python 3.10+, Docker (for integration tests), Node.js (for docs)

## ✅ Code Quality

```bash
# Linting
pipx run ruff check db_sync_tool/
pipx run ruff check db_sync_tool/ --fix

# Type checking
pipx run mypy db_sync_tool/
```

## 🧪 Testing

```bash
# Unit tests (fast, no Docker)
./tests/run-unit-tests.sh

# Integration tests (requires Docker)
./tests/run-integration-tests.sh

# With coverage
./tests/run-unit-tests.sh --cov
```

## 📕 Documentation

Documentation is built with [VitePress](https://vitepress.dev/) and deployed to GitHub Pages.

```bash
# Install dependencies
npm install

# Start local dev server
npm run docs:dev

# Build for production
npm run docs:build
```

Edit files in `docs/`:
- `getting-started/` - Installation, quickstart, framework guides
- `configuration/` - Config options, auto-discovery, authentication
- `reference/` - Sync modes, CLI reference
- `development/` - Testing, release guide

## 🔀 Pull Request Process

1. Create a branch from `main`
2. Make changes following existing code style
3. Run linting and tests
4. Commit with [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Refactoring
5. Push and open a PR

## 🤖 CI/CD

All PRs are checked by GitHub Actions:
- Unit tests (Python 3.10-3.13)
- Integration tests (Docker)
- Linting (ruff)
- Type checking (mypy)
- Docs build (VitePress)

## ❓ Questions?

Open an [issue](https://github.com/konradmichalik/db-sync-tool/issues) on GitHub.
