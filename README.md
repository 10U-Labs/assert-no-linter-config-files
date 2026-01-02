# assert-no-linter-config-files

A command-line tool that asserts there are no configuration files (or embedded
configuration sections) for common linters in your codebase. This is useful for
enforcing that linter configurations are managed centrally rather than in
individual repositories.

## Installation

```bash
pip install assert-no-linter-config-files
```

Or install from source:

```bash
pip install -e .
```

## Usage

```bash
assert-no-linter-config-files [DIRECTORY ...]
```

If no directories are provided, the current directory is scanned.

### Exit Codes

- `0` - No linter configuration found
- `1` - One or more linter configurations found
- `2` - Usage/runtime error (invalid args, unreadable files)

### Examples

Check the current directory:

```bash
assert-no-linter-config-files
```

Check specific directories:

```bash
assert-no-linter-config-files src/ tests/
```

Use in CI to enforce no local linter configs:

```bash
assert-no-linter-config-files . || exit 1
```

## What It Checks

### Dedicated Config Files

The tool flags the presence of these files anywhere in the scanned tree:

| Tool     | Files                                                                                       |
|----------|----------------------------------------------------------------------------------------------|
| pylint   | `.pylintrc`, `pylintrc`, `.pylintrc.toml`                                                   |
| pytest   | `pytest.ini`                                                                                |
| mypy     | `mypy.ini`, `.mypy.ini`                                                                     |
| yamllint | `.yamllint`, `.yamllint.yml`, `.yamllint.yaml`                                              |
| jscpd    | `.jscpd.json`, `.jscpd.yml`, `.jscpd.yaml`, `.jscpd.toml`, `.jscpdrc`, `.jscpdrc.*`         |

### Embedded Config Sections

The tool also checks shared config files for tool-specific sections:

**pyproject.toml:**

- `[tool.pylint]` or `[tool.pylint.*]`
- `[tool.mypy]`
- `[tool.pytest.ini_options]`
- `[tool.jscpd]`
- `[tool.yamllint]`

**setup.cfg:**

- `[mypy]`
- `[tool:pytest]`
- Any section containing "pylint"

**tox.ini:**

- `[pytest]` or `[tool:pytest]`
- `[mypy]`
- Any section containing "pylint"

## Output Format

When findings are detected, each is printed on a separate line:

```text
<path>:<tool>:<reason>
```

Examples:

```text
./pytest.ini:pytest:config file
./pyproject.toml:mypy:tool.mypy section
./setup.cfg:pylint:pylint.messages_control section
```

## CI Checks

The following checks run on every push and pull request:

- **yamllint** - YAML linting for workflow files
- **markdownlint** - Markdown linting
- **pylint** - Python linting for source and test code
- **mypy** - Static type checking for source code
- **jscpd** - Duplicate code detection
- **pytest** - Unit, integration, and E2E tests
