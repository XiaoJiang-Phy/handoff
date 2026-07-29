from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from handoff_fixture import valid_document


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, script: Path):
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


class CaptureGitStateTest(unittest.TestCase):
    def test_supports_repository_without_first_commit(self) -> None:
        module = _load_module(
            "capture_git_state_unborn",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / "new.txt").write_text("new\n", encoding="utf-8")
            state = module.capture_state(repository, ["new.txt"])

        self.assertEqual(state["commit"], "unborn")
        self.assertTrue(state["dirty"])

    def test_captures_dirty_state_and_sanitizes_remote(self) -> None:
        module = _load_module(
            "capture_git_state",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
            _run_git(repository, "add", "tracked.txt")
            _run_git(
                repository,
                "-c",
                "user.name=Handoff Test",
                "-c",
                "user.email=handoff@example.invalid",
                "commit",
                "-m",
                "initial",
            )
            _run_git(
                repository,
                "remote",
                "add",
                "origin",
                "https://token:secret@github.com/owner/repository.git",
            )
            (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
            (repository / "staged.txt").write_text("staged\n", encoding="utf-8")
            (repository / "note.txt").write_text("untracked\n", encoding="utf-8")
            _run_git(repository, "add", "staged.txt")

            state = module.capture_state(repository, ["note.txt"])

        self.assertTrue(state["dirty"])
        self.assertEqual(state["root"], ".")
        self.assertEqual(
            state["remote"], "https://github.com/owner/repository.git"
        )
        self.assertNotIn("observed_root", state)
        self.assertIn("note.txt", state["untracked_paths"])
        self.assertEqual(
            state["key_untracked_files"][0]["sha256"],
            hashlib.sha256(b"untracked\n").hexdigest(),
        )
        for field_name in (
            "status_sha256",
            "unstaged_diff_sha256",
            "staged_diff_sha256",
        ):
            self.assertRegex(state[field_name], r"^[0-9a-f]{64}$")

    def test_rejects_tracked_file_as_untracked_hash_target(self) -> None:
        module = _load_module(
            "capture_git_state_reject",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
            _run_git(repository, "add", "tracked.txt")
            _run_git(
                repository,
                "-c",
                "user.name=Handoff Test",
                "-c",
                "user.email=handoff@example.invalid",
                "commit",
                "-m",
                "initial",
            )
            with self.assertRaises(module.GitStateError):
                module.capture_state(repository, ["tracked.txt"])


class ManageLatestTest(unittest.TestCase):
    def _ignored_repository(self, root: Path) -> Path:
        _run_git(root, "init", "-b", "main")
        (root / ".gitignore").write_text("doc/\n", encoding="utf-8")
        handoffs = root / "doc" / "handoffs"
        handoffs.mkdir(parents=True)
        return handoffs

    def test_updates_and_resolves_latest(self) -> None:
        module = _load_module(
            "manage_latest",
            ROOT / "skills" / "handoff" / "scripts" / "manage_latest.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            handoffs = self._ignored_repository(Path(temporary_directory))
            handoff = handoffs / "20260729T120000Z-example-task.md"
            handoff.write_text(valid_document(), encoding="utf-8")

            pointer = module.update_latest(handoff)
            resolved = module.resolve_latest(pointer)

            self.assertEqual(pointer.read_text(encoding="utf-8"), f"{handoff.name}\n")
            self.assertEqual(resolved, handoff.resolve())

    def test_rejects_unignored_handoff_directory(self) -> None:
        module = _load_module(
            "manage_latest_unignored",
            ROOT / "skills" / "handoff" / "scripts" / "manage_latest.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            handoffs = repository / "doc" / "handoffs"
            handoffs.mkdir(parents=True)
            handoff = handoffs / "20260729T120000Z-example-task.md"
            handoff.write_text(valid_document(), encoding="utf-8")
            with self.assertRaises(module.LatestError):
                module.update_latest(handoff)

    def test_rejects_malformed_latest_value(self) -> None:
        module = _load_module(
            "manage_latest_malformed",
            ROOT / "skills" / "handoff" / "scripts" / "manage_latest.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            handoffs = self._ignored_repository(Path(temporary_directory))
            pointer = handoffs / "LATEST"
            pointer.write_text("../outside.md\n", encoding="utf-8")
            with self.assertRaises(module.LatestError):
                module.resolve_latest(pointer)

    def test_cli_updates_and_resolves_latest(self) -> None:
        script = ROOT / "skills" / "handoff" / "scripts" / "manage_latest.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            handoffs = self._ignored_repository(Path(temporary_directory))
            handoff = handoffs / "20260729T120000Z-example-task.md"
            handoff.write_text(valid_document(), encoding="utf-8")
            update_result = subprocess.run(
                [sys.executable, str(script), "update", str(handoff)],
                check=False,
                capture_output=True,
                text=True,
            )
            resolve_result = subprocess.run(
                [sys.executable, str(script), "resolve", str(handoffs / "LATEST")],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(update_result.returncode, 0, update_result.stderr)
        self.assertEqual(resolve_result.returncode, 0, resolve_result.stderr)
        self.assertEqual(Path(resolve_result.stdout.strip()), handoff.resolve())


if __name__ == "__main__":
    unittest.main()
