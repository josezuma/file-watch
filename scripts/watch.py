#!/usr/bin/env python3
"""
file-watch — Production file watcher CLI.

Watches directories for file changes (create, modify, delete) using polling.
Triggers commands automatically. Pure Python stdlib — no dependencies.

Usage:
    python3 scripts/watch.py . --pattern "*.py" --command "pytest"
    python3 scripts/watch.py ./src --recursive --command "npm run build"
    python3 scripts/watch.py . --pattern "*.md" --dry-run
"""

import os
import sys
import time
import glob
import json
import hashlib
import argparse
import datetime
import subprocess
from pathlib import Path


class FileWatcher:
    """Polling-based file watcher with debounce and command templating."""

    def __init__(self, directory: str, pattern: str = None, recursive: bool = True,
                 interval: float = 1.0, debounce: float = 0.5,
                 command: str = None, dry_run: bool = False,
                 verbose: bool = False, show_timestamp: bool = True):
        self.directory = Path(directory).resolve()
        self.pattern = pattern or "*"
        self.recursive = recursive
        self.interval = interval
        self.debounce = debounce
        self.command = command
        self.dry_run = dry_run
        self.verbose = verbose
        self.show_timestamp = show_timestamp
        self._snapshot = {}
        self._last_trigger = 0.0

    def _log(self, msg: str):
        if self.show_timestamp:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] {msg}")
        else:
            print(msg)

    def _scan(self) -> dict:
        """Scan directory and return {relative_path: (mtime, size, hash)}."""
        result = {}
        pattern = self.pattern
        search_dir = self.directory

        if self.recursive:
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    full = Path(root) / f
                    try:
                        rel = str(full.relative_to(search_dir))
                        stat = full.stat()
                        # Use mtime + size as fingerprint (fast, no content hash)
                        result[rel] = (stat.st_mtime, stat.st_size)
                    except (OSError, ValueError):
                        continue
        else:
            for f in search_dir.glob(pattern):
                try:
                    rel = str(f.relative_to(search_dir))
                    stat = f.stat()
                    result[rel] = (stat.st_mtime, stat.st_size)
                except (OSError, ValueError):
                    continue

        return result

    def _diff(self, old: dict, new: dict) -> list:
        """Compare snapshots and return list of (event, path) tuples."""
        events = []
        old_set = set(old.keys())
        new_set = set(new.keys())

        # Deleted files
        for path in old_set - new_set:
            events.append(("DELETED", path))

        # Created files
        for path in new_set - old_set:
            events.append(("CREATED", path))

        # Modified files
        for path in old_set & new_set:
            if old[path] != new[path]:
                events.append(("MODIFIED", path))

        return events

    def _run_command(self, event: str, filepath: str):
        """Execute the command with template variables."""
        if not self.command:
            return

        full_path = self.directory / filepath
        context = {
            "file": str(full_path),
            "event": event,
            "dir": str(self.directory),
            "filename": Path(filepath).name,
            "ext": Path(filepath).suffix,
            "relpath": filepath,
        }

        cmd = self.command
        for key, val in context.items():
            cmd = cmd.replace("{" + key + "}", val)

        if self.dry_run:
            self._log(f"  ⚡ WOULD RUN: {cmd}")
            return

        self._log(f"  🔄 Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    self._log(f"     {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n"):
                    self._log(f"     ! {line}")
            if result.returncode != 0:
                self._log(f"     ⚠️ Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            self._log(f"     ⚠️ Command timed out (60s)")
        except Exception as e:
            self._log(f"     ❌ Error: {e}")

    def watch(self):
        """Main watch loop — scan, diff, trigger."""
        self._log(f"📁 Watching: {self.directory}")
        self._log(f"   Pattern: {self.pattern}")
        self._log(f"   Recursive: {'yes' if self.recursive else 'no'}")
        self._log(f"   Interval: {self.interval}s")
        if self.command:
            self._log(f"   Command: {self.command}")
        if self.dry_run:
            self._log(f"   ⚡ DRY RUN — no commands will execute")
        self._log("")

        # Initial scan
        self._snapshot = self._scan()
        file_count = len(self._snapshot)
        self._log(f"👀 Watching {file_count} files...")
        if file_count == 0:
            self._log(f"⚠️  No files match pattern '{self.pattern}' in {self.directory}")
            self._log(f"   Tip: use --recursive or change --pattern")

        try:
            while True:
                time.sleep(self.interval)
                current = self._scan()
                events = self._diff(self._snapshot, current)
                self._snapshot = current

                if not events:
                    continue

                # Debounce: wait for quiet period
                now = time.time()
                if now - self._last_trigger < self.debounce:
                    continue
                self._last_trigger = now

                for event, path in events:
                    self._log(f"{'🔄 ' + event:20s} {path}")
                    if self.command:
                        self._run_command(event, path)

        except KeyboardInterrupt:
            self._log("\n👋 Stopped.")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="File watcher — watch directories and trigger commands on changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/watch.py . --pattern "*.py" --command "pytest"
  python3 scripts/watch.py ./src --recursive --command "npm run build"
  python3 scripts/watch.py . --pattern "*.md" --dry-run
  python3 scripts/watch.py /var/log --pattern "*.log" --command "echo {file} changed"
        """
    )
    parser.add_argument("directory", nargs="?", default=".", help="Directory to watch")
    parser.add_argument("--pattern", default=None, help="File pattern (e.g., '*.py', '*.md')")
    parser.add_argument("--command", "-c", default=None, help="Command to run on change")
    parser.add_argument("--recursive", "-r", action="store_true", help="Watch recursively")
    parser.add_argument("--interval", "-i", type=float, default=1.0, help="Polling interval (seconds)")
    parser.add_argument("--debounce", "-d", type=float, default=0.5, help="Debounce time (seconds)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would happen")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-timestamp", action="store_true", help="Suppress timestamps")
    parser.add_argument("--json", action="store_true", help="JSON output (one-shot scan)")
    parser.add_argument("--once", action="store_true", help="Scan once and exit")

    args = parser.parse_args()

    watcher = FileWatcher(
        directory=args.directory,
        pattern=args.pattern,
        recursive=args.recursive,
        interval=args.interval,
        debounce=args.debounce,
        command=args.command,
        dry_run=args.dry_run,
        verbose=args.verbose,
        show_timestamp=not args.no_timestamp,
    )

    if args.json:
        snapshot = watcher._scan()
        print(json.dumps({
            "directory": str(watcher.directory),
            "files": len(snapshot),
            "watched_files": sorted(snapshot.keys()),
        }, indent=2))
        return

    if args.once:
        snapshot = watcher._scan()
        watcher._log(f"📁 {watcher.directory}: {len(snapshot)} files matching '{watcher.pattern}'")
        return

    watcher.watch()


if __name__ == "__main__":
    main()
