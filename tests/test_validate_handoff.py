from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from handoff_fixture import valid_document


ROOT = Path(__file__).resolve().parents[1]


def _load_validator_module():
    script = ROOT / "skills" / "handoff" / "scripts" / "validate_handoff.py"
    spec = importlib.util.spec_from_file_location("validate_handoff", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_handoff.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateHandoffTest(unittest.TestCase):
    def test_accepts_valid_document(self) -> None:
        module = _load_validator_module()
        findings = module.validate_text(valid_document())
        self.assertFalse([finding for finding in findings if finding.level == "ERROR"])

    def test_rejects_missing_required_section(self) -> None:
        module = _load_validator_module()
        document = valid_document().replace(
            "## Immediate next action\n\nRead the referenced artifact.\n", ""
        )
        findings = module.validate_text(document)
        codes = {finding.code for finding in findings}
        self.assertIn("sections.missing", codes)

    def test_warns_on_possible_secret_and_absolute_path(self) -> None:
        module = _load_validator_module()
        document = valid_document().replace(
            "The repository state is recorded above.",
            "password=very-sensitive-value at /Users/example/private/file.",
        )
        findings = module.validate_text(document)
        codes = {finding.code for finding in findings}
        self.assertIn("sensitive.assigned-secret", codes)
        self.assertIn("portability.absolute_path", codes)

    def test_rejects_non_boolean_dirty_state(self) -> None:
        module = _load_validator_module()
        document = valid_document().replace('"dirty": false', '"dirty": "false"')
        findings = module.validate_text(document)
        codes = {finding.code for finding in findings}
        self.assertIn("metadata.repository_dirty", codes)

    def test_rejects_invalid_git_hash(self) -> None:
        module = _load_validator_module()
        document = valid_document().replace(
            '"status_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"',
            '"status_sha256": "invalid"',
        )
        findings = module.validate_text(document)
        codes = {finding.code for finding in findings}
        self.assertIn("metadata.repository_status_sha256", codes)

    def test_cli_accepts_valid_document(self) -> None:
        script = ROOT / "skills" / "handoff" / "scripts" / "validate_handoff.py"
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = Path(temporary_directory) / "handoff.md"
            document.write_text(valid_document(), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(document), "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
