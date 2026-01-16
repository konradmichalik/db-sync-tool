# Contributing to db-sync-tool

Thank you for your interest in contributing to db-sync-tool! This document outlines the process for contributing to this project.

## Requirements

- Python 3.10+
- Docker & Docker Compose (for integration tests)
- pipx (recommended for running tools without global installation)

## Initial Setup

```bash
# Clone the repository
git clone https://github.com/jackd248/db-sync-tool.git
cd db-sync-tool

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Code Quality

### Linting

We use [ruff](https://docs.astral.sh/ruff/) for linting and code formatting.

```bash
# Check for issues
pipx run ruff check db_sync_tool/

# Auto-fix issues
pipx run ruff check db_sync_tool/ --fix

# Format code
pipx run ruff format db_sync_tool/
```

### Static Analysis

```bash
# Type checking
pipx run mypy db_sync_tool/
```

Type checking runs automatically in CI on every pull request.

## Testing

### Unit Tests

Unit tests run without Docker and are fast (~0.1s).

```bash
# Run unit tests
./tests/run-unit-tests.sh

# Run with coverage report
./tests/run-unit-tests.sh --cov

# Run specific test file
./tests/run-unit-tests.sh -k "security"
```

### Integration Tests

Integration tests require Docker and test the full sync workflow.

```bash
# Run integration tests (starts Docker automatically)
./tests/run-integration-tests.sh

# Run specific test
./tests/run-integration-tests.sh -k "receiver"

# Verbose output
./tests/run-integration-tests.sh -v
```

### Test Structure

```
tests/
├── unit/                    # Fast, no Docker required
│   ├── test_security.py     # Security functions (46 tests)
│   ├── test_pure.py         # Utility functions (38 tests)
│   └── test_config.py       # Configuration (33 tests)
│
└── integration/             # Full E2E tests, Docker required
    ├── test_sync_modes.py   # RECEIVER, SENDER, PROXY, etc.
    ├── test_frameworks.py   # TYPO3, Symfony, WordPress, etc.
    └── ...                  # 38 tests total
```

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the existing code style

3. **Run quality checks** before committing:
   ```bash
   # Linting
   pipx run ruff check db_sync_tool/

   # Unit tests
   ./tests/run-unit-tests.sh

   # Integration tests (if applicable)
   ./tests/run-integration-tests.sh
   ```

4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add new feature X"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `refactor:` - Code refactoring
   - `docs:` - Documentation
   - `test:` - Tests
   - `build:` - Build/dependencies

5. **Push and create a Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

   Then open a PR on GitHub with:
   - Clear description of changes
   - Reference to related issue (if applicable)
   - Any breaking changes noted

## CI/CD

All pull requests are automatically checked by GitHub Actions:

- **Unit Tests**: Python 3.10, 3.11, 3.12, 3.13 with coverage
- **Integration Tests**: Full E2E tests with Docker
- **Linting**: ruff check and format
- **Type Checking**: mypy static analysis

Please ensure all checks pass before requesting a review.

## Questions?

If you have questions or need help, feel free to open an issue on GitHub.
