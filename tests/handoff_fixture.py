from __future__ import annotations

import textwrap


def valid_document() -> str:
    return textwrap.dedent(
        """\
        # Handoff: validator test

        ```json
        {
          "format_version": 2,
          "created_at": "2026-07-29T12:00:00Z",
          "source_platform": "codex",
          "target_platform": "antigravity",
          "conversation_language": "en",
          "handoff_mode": "project-linked",
          "privacy": "private",
          "repository": {
            "root": ".",
            "remote": "owner/repository",
            "branch": "main",
            "commit": "0123456789abcdef0123456789abcdef01234567",
            "dirty": false,
            "status_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "unstaged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "staged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          }
        }
        ```

        ## Next-session goal

        Continue the bounded task.

        ## User requirements and decisions

        [USER_DECISION] Keep one handoff Skill.

        ## Source state

        The repository state is recorded above.

        ## State of play

        The setup is complete.

        ## Execution plan

        The next Node is ready.

        ## Rejected paths and failed attempts

        The portable contract is selected.

        ## Open decisions, blockers, and preserved anomalies

        No blockers are known.

        ## Verification and evidence

        The contract validator passed.

        ## Artifacts

        `README.md` describes the repository.

        ## Running tasks

        None observed.

        ## Skills and platform mapping

        Use the handoff capability.

        ## Session-specific working preferences

        None recorded.

        ## Permissions and safety boundaries

        No external publication is authorized.

        ## Immediate next action

        Read the referenced artifact.
        """
    )
