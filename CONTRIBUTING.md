# Contributing to HyprGlyph

Bug reports, feature suggestions, parser optimizations, and desktop HUD integration patches are welcome.

## Development Requirements

HyprGlyph requires Python `>= 3.11` and standard tooling:
- `pytest` (`>= 8.0`)
- `ruff` (`>= 0.8`)
- `hatchling` (PEP 517/621 build backend)

Optional tools:
- `uv` for fast package and environment management

## Development Workflow

1. Clone the repository and install the package in editable mode:
   ```bash
   git clone https://github.com/Execorn/HyprGlyph.git
   cd HyprGlyph
   pip install -e .
   ```

2. Run the test suite:
   ```bash
   pytest -v
   ```

3. Verify test suite portability in a clean headless environment (mimicking CI):
   ```bash
   HOME=/tmp pytest -v
   ```

4. Run the code linter:
   ```bash
   ruff check .
   ```

## Code Style & Conventions

- Follow PEP 8 and project `pyproject.toml` guidelines.
- Keep the runtime parser dependency-free (standard library modules only).
- When modifying parser behavior for `.conf` or `.lua` inputs, add or update regression tests under `tests/`.
- Use Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
