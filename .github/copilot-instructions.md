# Copilot instructions for this repo

Summary
- This repository currently contains a single (empty) entrypoint: `main.py`.
- There are no existing agent instruction files or CI/config files discovered.

Big picture
- Current shape: a tiny single-file Python project. Expect changes to introduce a `src/` package, `tests/`, or dependency files (`requirements.txt` or `pyproject.toml`).
- Primary entrypoint: `main.py` — open this file first to determine intended functionality.

Developer workflows (what to run)
- Run the program locally: `python3 main.py` (no args found; inspect and follow CLI added by contributors).
- Add tests under `tests/` and run with `pytest` once `pytest` is added to project dependencies.

Conventions & patterns to follow in this codebase
- Keep changes minimal and self-contained: prefer adding a `src/` package for larger features rather than bloating `main.py`.
- Use explicit type hints and docstrings for public functions.
- Provide a `main()` function and a CLI guard:

  ```py
  def main() -> None:
      """Program entrypoint."""


  if __name__ == "__main__":
      main()
  ```

- Tests: add focused unit tests that exercise pure functions; use `tests/test_*.py` naming.
- Formatting/linting: the repo has no config yet — prefer `black`/`ruff`/`flake8` if added.

Integration points & external dependencies
- None discovered. If you add dependencies, include `requirements.txt` or `pyproject.toml` and update these instructions.

What the agent should do first
1. Open `main.py` and determine the intended behavior (it is currently empty).
2. If implementing a feature, add minimal tests in `tests/` and a brief `README.md` describing how to run the feature.
3. When adding dependencies, include a reproducible install command and CI step (e.g., GitHub Actions) in a follow-up PR.

PR & commit guidance
- Keep PRs small and focused. Include at least one unit test for functional changes.
- Commit message style: imperative, short summary first line (e.g., "Add user import CLI").

When to update this file
- Update `.github/copilot-instructions.md` when the repository structure grows (adding `src/`, tests, CI, or dependency files). Always reference the new files in this document.

Notes
- No project-specific conventions were found beyond the empty `main.py`. If you (the human) have preferred workflows, add them to this file for future AI agents.

If anything here is unclear or you'd like the agent to adopt additional conventions (testing frameworks, linters, CI), please update this file or tell the agent in the PR description.
