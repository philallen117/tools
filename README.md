# tools

This is a single repo of several small tools.

Each child folder is a separate tool and a separate uv project.

I want vscode settings for this project to use `ruff format` for format on save, `ruff` for linting, `pylance` (vscode built-in) for type checking while editing,`pyrefly` for type checking offline and `pytest` for testing. Except for `pylance`, the project tools installed by uv found on my $PATH.

tasks.json - provides tasks to run:

- pyrefly: Type Check - run pyrefly type checking
- pytest: Run All Tests - run all tests
- ruff: Lint - run linting manually
- ruff: Format - format code manually

You can access tasks via the Command Palette (Cmd+Shift+P) → "Tasks: Run Task".
