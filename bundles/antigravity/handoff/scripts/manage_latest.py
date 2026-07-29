#!/usr/bin/env python3
"""Atomically update or safely resolve a private handoff LATEST pointer."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


HANDOFF_NAME_PATTERN = re.compile(
    r"^[0-9]{8}T[0-9]{6}Z-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"
)


class LatestError(RuntimeError):
    """Raised when a LATEST pointer or target is unsafe."""


def _validated_target(path: Path) -> Path:
    if path.is_symlink():
        raise LatestError(f"handoff target must not be a symlink: {path}")
    resolved = path.resolve()
    if not resolved.is_file():
        raise LatestError(f"handoff target must be a regular file: {path}")
    if HANDOFF_NAME_PATTERN.fullmatch(resolved.name) is None:
        raise LatestError(f"handoff filename does not match the UTC topic format: {resolved.name}")
    if resolved.parent.name != "handoffs" or resolved.parent.parent.name != "doc":
        raise LatestError("handoff target must be directly under doc/handoffs")
    return resolved


def _require_ignored(path: Path) -> None:
    root_result = subprocess.run(
        ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if root_result.returncode != 0:
        raise LatestError("handoff path is not inside a Git repository")
    root = Path(root_result.stdout.strip()).resolve()
    try:
        relative_path = path.relative_to(root)
    except ValueError as exc:
        raise LatestError("handoff path is outside the repository root") from exc
    ignored_result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "--quiet", "--", relative_path.as_posix()],
        check=False,
    )
    if ignored_result.returncode != 0:
        raise LatestError("doc/handoffs is not ignored by Git")


def _require_valid_handoff(path: Path) -> None:
    validator = Path(__file__).with_name("validate_handoff.py")
    result = subprocess.run(
        [sys.executable, str(validator), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        raise LatestError(f"handoff validation failed: {detail}")


def update_latest(handoff_path: Path) -> Path:
    target = _validated_target(handoff_path)
    _require_ignored(target)
    _require_valid_handoff(target)
    pointer = target.parent / "LATEST"
    if pointer.exists() and (pointer.is_symlink() or not pointer.is_file()):
        raise LatestError("existing LATEST must be a regular file")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".LATEST-", dir=target.parent, text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(f"{target.name}\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, pointer)
    finally:
        if temporary.exists():
            temporary.unlink()
    return pointer


def resolve_latest(pointer_path: Path) -> Path:
    if pointer_path.is_symlink():
        raise LatestError(f"LATEST must not be a symlink: {pointer_path}")
    pointer = pointer_path.resolve()
    if not pointer.is_file():
        raise LatestError(f"LATEST must be a regular file: {pointer_path}")
    value = pointer.read_text(encoding="utf-8").strip()
    if HANDOFF_NAME_PATTERN.fullmatch(value) is None:
        raise LatestError("LATEST contains an invalid handoff filename")
    target = _validated_target(pointer.parent / value)
    _require_ignored(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("handoff", type=Path)
    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("latest", type=Path)
    args = parser.parse_args()

    try:
        result = (
            update_latest(args.handoff)
            if args.command == "update"
            else resolve_latest(args.latest)
        )
    except (LatestError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
