# assert-no-linter-config-files

A command-line tool that asserts there are no configuration files (or embedded
configuration sections) for common linters in your codebase. This is useful for
enforcing that linter configurations are managed centrally rather than in
individual repositories.

## Usage

```bash
assert-no-linter-config-files --linters LINTERS [OPTIONS] DIRECTORY [DIRECTORY ...]
```

### Required Arguments

- `--linters LINTERS` - Comma-separated linters to check: `jscpd,markdownlint,mypy,pylint,pytest,yamllint`
- `DIRECTORY` - One or more directories to scan

### Optional Arguments

- `--exclude PATTERN` - Glob pattern to exclude paths (repeatable)
- `--quiet` - Suppress output, exit code only
- `--count` - Print finding count only
- `--json` - Output findings as JSON
- `--fail-fast` - Exit on first finding
- `--warn-only` - Always exit 0, report only

### Exit Codes

- `0` - No linter configuration found (or `--warn-only`)
- `1` - One or more linter configurations found
- `2` - Usage/runtime error (invalid args, unreadable files)

### Examples

Check for pylint and mypy configs in the current directory:

```bash
assert-no-linter-config-files --linters pylint,mypy .
```

Check specific directories:

```bash
assert-no-linter-config-files --linters pylint,mypy src/ tests/
```

Check all linters:

```bash
assert-no-linter-config-files --linters pylint,mypy,pytest,yamllint,jscpd .
```

Exclude vendor directories:

```bash
assert-no-linter-config-files --linters pylint,mypy \
  --exclude "*vendor*" --exclude "*node_modules*" .
```

Get JSON output for CI integration:

```bash
assert-no-linter-config-files --linters pylint --json . | jq .
```

Use in CI to enforce no local linter configs:

```bash
assert-no-linter-config-files --linters pylint,mypy . || exit 1
```

## What It Checks

### Dedicated Config Files

The tool flags the presence of these files anywhere in the scanned tree:

**jscpd:** `.jscpd.json`, `.jscpd.yml`, `.jscpd.yaml`, `.jscpd.toml`,
`.jscpdrc`, `.jscpdrc.json`, `.jscpdrc.yml`, `.jscpdrc.yaml`

**markdownlint:** `.markdownlint.json`, `.markdownlint.jsonc`,
`.markdownlint.yaml`, `.markdownlint.yml`, `.markdownlintrc`

**mypy:** `mypy.ini`, `.mypy.ini`

**pylint:** `.pylintrc`, `pylintrc`, `.pylintrc.toml`

**pytest:** `pytest.ini`

**yamllint:** `.yamllint`, `.yamllint.yml`, `.yamllint.yaml`

### Embedded Config Sections

The tool also checks shared config files for tool-specific sections:

**pyproject.toml:**

- `[tool.jscpd]`
- `[tool.mypy]`
- `[tool.pylint]` or `[tool.pylint.*]`
- `[tool.pytest.ini_options]`
- `[tool.yamllint]`

**setup.cfg:**

- `[mypy]`
- Any section containing "pylint"
- `[tool:pytest]`

**tox.ini:**

- `[mypy]`
- Any section containing "pylint"
- `[pytest]` or `[tool:pytest]`

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

With `--json`:

```json
[{"path": "./pytest.ini", "tool": "pytest", "reason": "config file"}]
```
