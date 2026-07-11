<div align=center>
  <h1>👁️ File Watch</h1>
  <p><em>A production-quality file watcher CLI. Watch directories for file changes (create, modify, delete) and trigger commands automatically. Uses polling with configurable interval — works everywhere (no inotify dependency).</em></p>
  <p><a href=LICENSE><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt=License></a></p>
  <p><strong>Author:</strong> <a href=https://github.com/josezuma>Jose Zuma</a></p>
</div>

---

## Quick Start

```bash
# Watch current directory for .py changes, run tests on change
python3 scripts/watch.py . --pattern "*.py" --command "pytest"

# Watch a src directory recursively, rebuild on any change
python3 scripts/watch.py ./src --recursive --command "npm run build"

# Dry-run mode — see what would trigger without executing
python3 scripts/watch.py . --pattern "*.md" --command "echo changed" --dry-run
```

## The Problem This Solves

You're editing code and need to re-run tests, rebuild assets, or restart a server every time a file changes. Doing it manually is slow and breaks flow. File watching should be:

- **Cross-platform** — works on Linux, macOS, Windows (pure Python, no inotify)
- **Configurable** — debounce, interval, patterns, recursive
- **Safe** — dry-run mode, command templates with `{file}` and `{event}` variables
- **Zero dependencies** — Python stdlib only

## Demo

```bash
$ python3 scripts/watch.py . --pattern "*.py" --command "echo Changed: {file}" --verbose

📁 Watching: /home/user/project
   Pattern: *.py
   Recursive: yes
   Interval: 1.0s
   Command: echo Changed: {file}

[2026-07-11 00:35:01] 👀 Watching 12 files...
[2026-07-11 00:35:03] 🔄 MODIFIED: src/main.py → running: echo Changed: src/main.py
                     Output: Changed: src/main.py
[2026-07-11 00:35:05] 🔄 CREATED: tests/test_new.py → running: echo Changed: tests/test_new.py
                     Output: Changed: tests/test_new.py
[2026-07-11 00:35:10] 🔄 DELETED: old_temp.py → running: echo Changed: old_temp.py
                     Output: Changed: old_temp.py
```

## Features

| Feature | Description |
|---------|-------------|
| **Polling-based** | Checks file system every N seconds — works everywhere |
| **Debounce** | Waits for quiet period before triggering (prevents double-runs) |
| **Recursive** | Watch subdirectories with `--recursive` |
| **Glob patterns** | Filter by `*.py`, `*.md`, `*.{js,ts}` syntax |
| **Command templates** | Use `{file}`, `{event}`, `{dir}` in your command |
| **Dry-run** | See what would happen without executing |
| **Verbose logging** | Timestamps, file paths, command output |
| **Event types** | Detects CREATED, MODIFIED, DELETED |
| **No dependencies** | Pure Python stdlib — `os`, `time`, `glob`, `subprocess` |

## Installation

```bash
# Via git
git clone https://github.com/josezuma/file-watch.git
cd file-watch

# Or just download the script
curl -O https://raw.githubusercontent.com/josezuma/file-watch/main/scripts/watch.py
chmod +x scripts/watch.py
```

## Command Reference

```
Usage: python3 scripts/watch.py <directory> [options]

Arguments:
  directory                  Directory to watch

Options:
  --pattern PATTERN          File pattern to watch (e.g., "*.py", "*.md")
  --command CMD              Command to run on change. Use {file} for filename,
                             {event} for event type, {dir} for directory
  --recursive / -r           Watch subdirectories recursively
  --interval SECONDS         Polling interval in seconds (default: 1.0)
  --debounce SECONDS         Debounce time before triggering (default: 0.5)
  --dry-run                  Show what would happen without executing
  --verbose / -v             Show detailed logging
  --no-timestamp             Suppress timestamps in output
  --once                     Run once and exit (instead of continuous)
```

## How It Works

```
┌──────────────┐     every N seconds     ┌──────────────────┐
│  File System  │ ─────────────────────→  │  Scanner (os.walk)│
│  (directory)  │                         │  + glob matching  │
└──────────────┘                         └────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  Snapshot Diff    │
                                        │  (previous vs     │
                                        │   current files)  │
                                        └────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  Debounce Check   │
                                        │  (wait for quiet) │
                                        └────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  Command Runner   │
                                        │  (subprocess.run) │
                                        └──────────────────┘
```

## Examples

```bash
# Auto-run tests when Python files change
python3 scripts/watch.py . --pattern "*.py" --command "pytest {dir}"

# Auto-restart FastAPI dev server
python3 scripts/watch.py ./app --pattern "*.py" --command "kill -HUP $(cat server.pid)"

# Rebuild Jekyll site on markdown changes
python3 scripts/watch.py . --pattern "*.md" --recursive --command "jekyll build"

# Compile Sass to CSS on changes
python3 scripts/watch.py ./scss --pattern "*.scss" --command "sass {file}:css/{file}.css"

# Watch multiple extensions
python3 scripts/watch.py ./src --pattern "*.{js,ts,jsx,tsx}" --command "npm run build:fast"
```

## Related

- [file-organizer](https://github.com/josezuma/file-organizer)
- [backup-rotator](https://github.com/josezuma/backup-rotator)
- [duplicate-finder](https://github.com/josezuma/duplicate-finder)
- [bulk-rename](https://github.com/josezuma/bulk-rename)

## License

MIT © 2026 Jose Zuma
