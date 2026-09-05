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
    def test_rejects_non_utf8_nul_delimited_path(self) -> None:
        module = _load_module(
            "capture_git_state_non_utf8",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with self.assertRaisesRegex(module.GitStateError, "non-UTF-8"):
            module._decode_nul_paths(b"bad-\xff-name\0")

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
        self.assertEqual(
            state["status_hash_format"],
            "git-status-porcelain-v1-z-untracked-files-all",
        )

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

    def test_preserves_and_hashes_special_untracked_names(self) -> None:
        module = _load_module(
            "capture_git_state_special_names",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        names = [
            "中文.txt",
            "with space.txt",
            'with"quote.txt',
            "with\ttab.txt",
            "with\nnewline.txt",
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            for index, name in enumerate(names):
                (repository / name).write_bytes(f"content-{index}\n".encode())

            state = module.capture_state(repository, names)

        self.assertEqual(set(state["untracked_paths"]), set(names))
        hashes = {
            item["path"]: item["sha256"] for item in state["key_untracked_files"]
        }
        for index, name in enumerate(names):
            self.assertEqual(
                hashes[name], hashlib.sha256(f"content-{index}\n".encode()).hexdigest()
            )

    def test_status_hash_and_paths_ignore_core_quote_path(self) -> None:
        module = _load_module(
            "capture_git_state_quote_path",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / "中文.txt").write_text("content\n", encoding="utf-8")
            _run_git(repository, "config", "core.quotePath", "true")
            quoted = module.capture_state(repository, ["中文.txt"])
            _run_git(repository, "config", "core.quotePath", "false")
            unquoted = module.capture_state(repository, ["中文.txt"])

        self.assertEqual(quoted["untracked_paths"], unquoted["untracked_paths"])
        self.assertEqual(quoted["status_sha256"], unquoted["status_sha256"])
        self.assertEqual(quoted["status_hash_format"], unquoted["status_hash_format"])

    def test_tracked_modification_changes_status_and_diff_evidence(self) -> None:
        module = _load_module(
            "capture_git_state_modification",
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
            clean = module.capture_state(repository, [])
            (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
            dirty = module.capture_state(repository, [])

        self.assertNotEqual(clean["status_sha256"], dirty["status_sha256"])
        self.assertNotEqual(
            clean["unstaged_diff_sha256"], dirty["unstaged_diff_sha256"]
        )

    def test_rejects_missing_escape_and_oversized_hash_targets(self) -> None:
        module = _load_module(
            "capture_git_state_guards",
            ROOT / "skills" / "handoff" / "scripts" / "capture_git_state.py",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / "large.bin").write_bytes(b"12345")
            with self.assertRaises(module.GitStateError):
                module.capture_state(repository, ["missing.txt"])
            with self.assertRaises(module.GitStateError):
                module.capture_state(repository, ["../outside.txt"])
            module.MAX_HASHED_UNTRACKED_BYTES = 4
            with self.assertRaises(module.GitStateError):
                module.capture_state(repository, ["large.bin"])


class ScriptResolutionTest(unittest.TestCase):
    def test_uses_skill_scripts_and_project_relative_handoff_paths(self) -> None:
        skill_root = ROOT / "skills" / "handoff"
        skill_scripts = ROOT / "skills" / "handoff" / "scripts"
        skill_state_before = {
            path.relative_to(skill_root): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in skill_root.rglob("*")
            if path.is_file()
        }
        with tempfile.TemporaryDirectory(prefix="handoff project ") as temporary_directory:
            repository = Path(temporary_directory)
            _run_git(repository, "init", "-b", "main")
            (repository / ".gitignore").write_text("doc/\n", encoding="utf-8")
            decoy_scripts = repository / "scripts"
            decoy_scripts.mkdir()
            for name in (
                "capture_git_state.py",
                "validate_handoff.py",
                "manage_latest.py",
            ):
                (decoy_scripts / name).write_text(
                    "raise SystemExit(97)\n", encoding="utf-8"
                )
            handoffs = repository / "doc" / "handoffs"
            handoffs.mkdir(parents=True)
            handoff = handoffs / "20260729T120000Z-example-task.md"
            handoff.write_text(valid_document(), encoding="utf-8")

            capture_result = subprocess.run(
                [
                    sys.executable,
                    str(skill_scripts / "capture_git_state.py"),
                    "--repository",
                    ".",
                ],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )
            validate_result = subprocess.run(
                [
                    sys.executable,
                    str(skill_scripts / "validate_handoff.py"),
                    str(handoff.relative_to(repository)),
                ],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )
            update_result = subprocess.run(
                [
                    sys.executable,
                    str(skill_scripts / "manage_latest.py"),
                    "update",
                    str(handoff.relative_to(repository)),
                ],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )
            resolve_result = subprocess.run(
                [
                    sys.executable,
                    str(skill_scripts / "manage_latest.py"),
                    "resolve",
                    "doc/handoffs/LATEST",
                ],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertTrue((repository / "doc" / "handoffs" / "LATEST").is_file())

        skill_state_after = {
            path.relative_to(skill_root): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in skill_root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(capture_result.returncode, 0, capture_result.stderr)
        self.assertEqual(validate_result.returncode, 0, validate_result.stderr)
        self.assertEqual(update_result.returncode, 0, update_result.stderr)
        self.assertEqual(resolve_result.returncode, 0, resolve_result.stderr)
        self.assertEqual(Path(resolve_result.stdout.strip()), handoff.resolve())
        self.assertEqual(skill_state_before, skill_state_after)


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
