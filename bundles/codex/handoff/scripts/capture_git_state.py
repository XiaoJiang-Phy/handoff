#!/usr/bin/env python3
"""Capture portable, read-only Git state and content hashes for handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


MAX_HASHED_UNTRACKED_BYTES = 64 * 1024 * 1024


class GitStateError(RuntimeError):
    """Raised when portable Git state cannot be captured safely."""


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitStateError(detail or f"git {' '.join(arguments)} failed")
    return result.stdout


def _git_text(repository: Path, *arguments: str) -> str:
    return _git_bytes(repository, *arguments).decode("utf-8", errors="strict").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_sha256(repository: Path, *arguments: str) -> str:
    process = subprocess.Popen(
        ["git", "-C", str(repository), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None or process.stderr is None:
        raise GitStateError("cannot capture Git process streams")
    digest = hashlib.sha256()
    with process.stdout, process.stderr:
        for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
            digest.update(chunk)
        stderr = process.stderr.read()
    returncode = process.wait()
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise GitStateError(detail or f"git {' '.join(arguments)} failed")
    return digest.hexdigest()


def _sanitize_remote(remote: str) -> str:
    if "://" in remote:
        parsed = urlsplit(remote)
        host = parsed.hostname or "unknown"
        netloc = f"{host}:{parsed.port}" if parsed.port is not None else host
        return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
    scp_style = re.fullmatch(r"[^@]+@([^:]+):(.+)", remote)
    if scp_style is not None:
        return f"{scp_style.group(1)}:{scp_style.group(2)}"
    return remote


def _hash_untracked(
    repository_root: Path,
    relative_path: str,
    untracked_paths: set[str],
) -> dict[str, object]:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise GitStateError(f"untracked hash path must be repository-relative: {relative_path}")
    normalized = candidate.as_posix()
    if normalized not in untracked_paths:
        raise GitStateError(f"hash target is not an untracked file: {relative_path}")
    resolved = (repository_root / candidate).resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError as exc:
        raise GitStateError(f"untracked hash path escapes repository: {relative_path}") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise GitStateError(f"untracked hash target must be a regular file: {relative_path}")
    size = resolved.stat().st_size
    if size > MAX_HASHED_UNTRACKED_BYTES:
        raise GitStateError(
            f"untracked hash target exceeds {MAX_HASHED_UNTRACKED_BYTES} bytes: "
            f"{relative_path}"
        )
    return {
        "path": normalized,
        "size": size,
        "sha256": _sha256(resolved.read_bytes()),
    }


def capture_state(repository: Path, hash_untracked: list[str]) -> dict[str, object]:
    root = Path(_git_text(repository, "rev-parse", "--show-toplevel")).resolve()
    status_bytes = _git_bytes(root, "status", "--short", "--untracked-files=all")
    branch = _git_text(root, "branch", "--show-current") or "detached"
    remote_result = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
    )
    remote = (
        _sanitize_remote(remote_result.stdout.decode("utf-8", errors="strict").strip())
        if remote_result.returncode == 0
        else "unknown"
    )
    commit_result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        check=False,
        capture_output=True,
    )
    commit = (
        commit_result.stdout.decode("utf-8", errors="strict").strip()
        if commit_result.returncode == 0
        else "unborn"
    )
    untracked_paths = _git_text(
        root, "ls-files", "--others", "--exclude-standard"
    ).splitlines()

    return {
        "root": ".",
        "remote": remote,
        "branch": branch,
        "commit": commit,
        "dirty": bool(status_bytes),
        "status_short": status_bytes.decode("utf-8", errors="strict").splitlines(),
        "status_sha256": _sha256(status_bytes),
        "unstaged_diff_sha256": _git_sha256(
            root, "diff", "--binary", "--no-ext-diff"
        ),
        "staged_diff_sha256": _git_sha256(
            root, "diff", "--cached", "--binary", "--no-ext-diff"
        ),
        "unstaged_diffstat": _git_text(root, "diff", "--stat", "--no-ext-diff"),
        "staged_diffstat": _git_text(
            root, "diff", "--cached", "--stat", "--no-ext-diff"
        ),
        "untracked_paths": untracked_paths,
        "key_untracked_files": [
            _hash_untracked(root, relative_path, set(untracked_paths))
            for relative_path in hash_untracked
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--hash-untracked",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
    )
    args = parser.parse_args()
    try:
        state = capture_state(args.repository.resolve(), args.hash_untracked)
    except (GitStateError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
