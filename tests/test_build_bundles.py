from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_build_module():
    script = ROOT / "scripts" / "build_bundles.py"
    spec = importlib.util.spec_from_file_location("build_bundles", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load build_bundles.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildBundlesTest(unittest.TestCase):
    def test_builds_platform_specific_metadata(self) -> None:
        module = _load_build_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "bundles"
            module.build_bundles(output_root)

            codex = output_root / "codex" / "handoff"
            antigravity = output_root / "antigravity" / "handoff"
            self.assertTrue((codex / "SKILL.md").is_file())
            self.assertTrue((codex / "agents" / "openai.yaml").is_file())
            self.assertTrue((codex / "scripts" / "capture_git_state.py").is_file())
            self.assertTrue((codex / "scripts" / "manage_latest.py").is_file())
            self.assertTrue((antigravity / "SKILL.md").is_file())
            self.assertFalse((antigravity / "agents").exists())
            self.assertEqual(
                (codex / "references" / "handoff-contract.md").read_text(),
                (antigravity / "references" / "handoff-contract.md").read_text(),
            )

    def test_refuses_unmarked_output(self) -> None:
        module = _load_build_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "bundles"
            output_root.mkdir()
            (output_root / "user-file").write_text("preserve", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                module.build_bundles(output_root)


if __name__ == "__main__":
    unittest.main()
