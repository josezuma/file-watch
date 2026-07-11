# FAQ

## How does file-watch detect changes?
It uses polling — scans the directory every N seconds and compares file modification times and sizes. No inotify or platform-specific APIs needed.

## Why polling instead of inotify?
Polling works everywhere (Linux, macOS, Windows, Docker, WSL) without installing anything. Inotify requires platform-specific code and doesn't work on network filesystems.

## What's the debounce for?
Prevents multiple triggers when saving a file (many editors save atomically, which can cause 2-3 rapid events). The debounce waits for a quiet period before executing.

## Can I use it in CI/CD?
Yes. Use `--once` to scan and exit, or `--json` for machine-readable output.

## What variables can I use in --command?
- `{file}` — full path to the changed file
- `{event}` — CREATED, MODIFIED, or DELETED
- `{dir}` — the watched directory
- `{filename}` — just the filename
- `{ext}` — file extension (.py, .md, etc.)
- `{relpath}` — path relative to watch directory
