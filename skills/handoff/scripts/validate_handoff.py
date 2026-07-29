#!/usr/bin/env python3
"""Validate the portable structure of a handoff Markdown document."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = (
    "Next-session goal",
    "User requirements and decisions",
    "Source state",
    "State of play",
    "Execution plan",
    "Rejected paths and failed attempts",
    "Open decisions, blockers, and preserved anomalies",
    "Verification and evidence",
    "Artifacts",
    "Running tasks",
    "Skills and platform mapping",
    "Session-specific working preferences",
    "Permissions and safety boundaries",
    "Immediate next action",
)

REQUIRED_METADATA = {
    "format_version",
    "created_at",
    "source_platform",
    "target_platform",
    "conversation_language",
    "handoff_mode",
    "privacy",
    "repository",
}

REQUIRED_REPOSITORY_FIELDS = {
    "root",
    "remote",
    "branch",
    "commit",
    "dirty",
    "status_sha256",
    "unstaged_diff_sha256",
    "staged_diff_sha256",
}

SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "assigned-secret",
        re.compile(
            r"(?i)\b(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*"
            r"[\"']?(?!redacted\b)[^\s\"']{8,}"
        ),
    ),
)

ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?<![\w.])/(?:Users|home|private|tmp|var|opt)/[^\s)`]+"),
    re.compile(r"\b[A-Za-z]:\\[^\s)`]+"),
)

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


def _parse_metadata(text: str) -> tuple[dict[str, Any] | None, list[Finding]]:
    match = re.search(r"^```json\s*\n(.*?)\n```", text, re.MULTILINE | re.DOTALL)
    if match is None:
        return None, [
            Finding("ERROR", "metadata.missing", "Missing fenced JSON metadata block.")
        ]
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return None, [
            Finding("ERROR", "metadata.invalid_json", f"Invalid metadata JSON: {exc}.")
        ]
    if not isinstance(metadata, dict):
        return None, [
            Finding("ERROR", "metadata.type", "Metadata must be a JSON object.")
        ]
    return metadata, []


def _validate_metadata(metadata: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    missing = sorted(REQUIRED_METADATA - metadata.keys())
    if missing:
        findings.append(
            Finding(
                "ERROR",
                "metadata.fields",
                f"Missing metadata fields: {', '.join(missing)}.",
            )
        )

    if metadata.get("format_version") != 2:
        findings.append(
            Finding("ERROR", "metadata.version", "format_version must be 2.")
        )

    created_at = metadata.get("created_at")
    if not isinstance(created_at, str) or not created_at.endswith("Z"):
        findings.append(
            Finding(
                "ERROR",
                "metadata.created_at",
                "created_at must be an RFC 3339 UTC string ending in Z.",
            )
        )
    else:
        try:
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            findings.append(
                Finding(
                    "ERROR",
                    "metadata.created_at",
                    "created_at is not a valid RFC 3339 timestamp.",
                )
            )

    if metadata.get("handoff_mode") not in {"project-linked", "standalone"}:
        findings.append(
            Finding(
                "ERROR",
                "metadata.mode",
                "handoff_mode must be project-linked or standalone.",
            )
        )

    for field_name in (
        "source_platform",
        "target_platform",
        "conversation_language",
        "privacy",
    ):
        value = metadata.get(field_name)
        if not isinstance(value, str) or not value.strip():
            findings.append(
                Finding(
                    "ERROR",
                    f"metadata.{field_name}",
                    f"{field_name} must be a non-empty string.",
                )
            )

    repository = metadata.get("repository")
    if not isinstance(repository, dict):
        findings.append(
            Finding("ERROR", "metadata.repository", "repository must be an object.")
        )
    else:
        missing_repository = sorted(REQUIRED_REPOSITORY_FIELDS - repository.keys())
        if missing_repository:
            findings.append(
                Finding(
                    "ERROR",
                    "metadata.repository_fields",
                    "Missing repository fields: "
                    + ", ".join(missing_repository)
                    + ".",
                )
            )
        if "dirty" in repository and not isinstance(repository["dirty"], bool):
            findings.append(
                Finding(
                    "ERROR",
                    "metadata.repository_dirty",
                    "repository.dirty must be a boolean.",
                )
            )
        for field_name in (
            "status_sha256",
            "unstaged_diff_sha256",
            "staged_diff_sha256",
        ):
            value = repository.get(field_name)
            if value is not None and (
                not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None
            ):
                findings.append(
                    Finding(
                        "ERROR",
                        f"metadata.repository_{field_name}",
                        f"repository.{field_name} must be 64 lowercase hex characters.",
                    )
                )

    return findings


def _validate_sections(text: str) -> list[Finding]:
    findings: list[Finding] = []
    if re.search(r"^# Handoff:\s+\S.*$", text, re.MULTILINE) is None:
        findings.append(
            Finding(
                "ERROR",
                "document.title",
                "Document must contain a non-empty '# Handoff:' title.",
            )
        )

    heading_matches = list(re.finditer(r"^## (.+?)\s*$", text, re.MULTILINE))
    positions = {match.group(1): match.start() for match in heading_matches}
    missing = [section for section in REQUIRED_SECTIONS if section not in positions]
    if missing:
        findings.append(
            Finding(
                "ERROR",
                "sections.missing",
                f"Missing required sections: {', '.join(missing)}.",
            )
        )
        return findings

    required_positions = [positions[section] for section in REQUIRED_SECTIONS]
    if required_positions != sorted(required_positions):
        findings.append(
            Finding(
                "ERROR",
                "sections.order",
                "Required sections are not in contract order.",
            )
        )

    for index, match in enumerate(heading_matches):
        section = match.group(1)
        if section not in REQUIRED_SECTIONS:
            continue
        content_start = match.end()
        content_end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(text)
        )
        if not text[content_start:content_end].strip():
            findings.append(
                Finding(
                    "ERROR",
                    "sections.empty",
                    f"Required section '{section}' is empty.",
                )
            )

    return findings


def _scan_warnings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(
                Finding(
                    "WARNING",
                    f"sensitive.{name}",
                    f"Possible unredacted sensitive value detected: {name}.",
                )
            )
    if any(pattern.search(text) for pattern in ABSOLUTE_PATH_PATTERNS):
        findings.append(
            Finding(
                "WARNING",
                "portability.absolute_path",
                "Possible machine-specific absolute path detected.",
            )
        )
    return findings


def validate_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    metadata, metadata_findings = _parse_metadata(text)
    findings.extend(metadata_findings)
    if metadata is not None:
        findings.extend(_validate_metadata(metadata))
    findings.extend(_validate_sections(text))
    findings.extend(_scan_warnings(text))
    return findings


def _render_text(findings: list[Finding]) -> str:
    if not findings:
        return "PASS: handoff contract is valid."
    lines = [f"{finding.level} [{finding.code}] {finding.message}" for finding in findings]
    if not any(finding.level == "ERROR" for finding in findings):
        lines.append("PASS WITH WARNINGS: handoff contract is structurally valid.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        size = args.document.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            findings = [
                Finding(
                    "ERROR",
                    "document.size",
                    f"Document exceeds {MAX_DOCUMENT_BYTES} bytes.",
                )
            ]
        else:
            findings = validate_text(args.document.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        findings = [Finding("ERROR", "document.read", f"Cannot read document: {exc}.")]

    if args.json_output:
        payload = {
            "valid": not any(finding.level == "ERROR" for finding in findings),
            "findings": [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_render_text(findings))

    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
