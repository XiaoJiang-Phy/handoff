# Handoff document contract

Use the following fixed headings and keep them in order. Write section prose in
the primary language of the source conversation. Use `None recorded`, `Not run`,
`unknown`, or `not applicable` explicitly; never leave a required section empty.

## Document skeleton

````markdown
# Handoff: <concise topic>

```json
{
  "format_version": 3,
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "source_platform": "codex",
  "target_platform": "antigravity",
  "conversation_language": "zh",
  "handoff_mode": "project-linked",
  "privacy": "private",
  "repository": {
    "root": ".",
    "remote": "owner/repository or unknown",
    "branch": "branch or unknown",
    "commit": "full commit SHA or unknown",
    "dirty": true,
    "status_hash_format": "git-status-porcelain-v1-z-untracked-files-all",
    "status_sha256": "<64 lowercase hex>",
    "unstaged_diff_sha256": "<64 lowercase hex>",
    "staged_diff_sha256": "<64 lowercase hex>"
  }
}
```

## Next-session goal

State the concrete goal, completion criteria, and explicit non-goals.

## User requirements and decisions

Record answered requirements and settled choices. Prefix only important user
decisions with `[USER_DECISION]`. Preserve stated rationale and scope without
copying the full conversation.

## Source state

Record the repository identity, branch, exact HEAD, staged/unstaged/untracked
paths, diffstat, Git hashes, relevant environment, source platform, and target
platform. Include hashes of key untracked files. State any capture limitation.

## State of play

Separate completed, verified, in-progress, and blocked work. Identify the exact
current implementation location.

## Execution plan

Record completed, active, and pending Nodes, their gates, the active Node's exact
stopping point, and the next file or command. Reference an authoritative plan
when available; otherwise preserve the remaining plan here.

## Rejected paths and failed attempts

Record rejected designs and actual failures, including reason or evidence. State
what must change before retrying a path.

## Open decisions, blockers, and preserved anomalies

Keep unresolved choices, missing evidence, warnings, negative results, and
anomalies visible. Do not assign an unestablished cause.

## Verification and evidence

List only commands and checks actually run, with observed results and relevant
artifact paths. Write `Not run` and the reason for missing verification. Never
infer a domain conclusion from a process exit code.

## Artifacts

List each authoritative artifact with its role, revision when relevant, exact
relative path or stable URL, and access limitation. Do not duplicate its full
content.

## Running tasks

Record each active local process with command, working directory, PID or job ID,
start time, log/output paths, last observed state, and safe monitoring boundary.
State `None observed` when no task is running. Never instruct the receiver to
restart or terminate a task automatically.

## Skills and platform mapping

List the capabilities needed next and the verified platform-specific Skill
names. Distinguish Skills already used from Skills required for the next action.

## Session-specific working preferences

Record only preferences specific to this task. Reference durable project rules
under **Artifacts**.

## Permissions and safety boundaries

Record actions already performed, actions explicitly authorized next, and
actions requiring fresh approval. Do not transfer broader authority than the
current conversation established.

## Immediate next action

Give exactly one bounded action, its prerequisites, target file or command, gate,
and expected evidence.

## Portable payload

Add this optional section only for essential content not stored in an accessible
artifact. Preserve the content exactly and identify its source.

## Task-specific continuity

Add this optional section for code, numerical, anomaly, literature, writing, or
planning modules from `task-continuity.md`.

## Scientific continuity

Add this optional section when routed by `scientific-continuity.md`.
````

## Metadata rules

- Use UTC with a trailing `Z`.
- Use `conversation_language: zh` for primarily Chinese prose and `en` for
  primarily English prose. Other short language tags are allowed when required.
- Use `project-linked` for the normal Codex ↔ Antigravity shared-checkout case.
- Default `privacy` to `private`.
- Use a full commit SHA when Git provides one.
- Write new handoffs as `format_version: 3`. The validator continues to accept
  immutable version 2 documents for resume and review; do not rewrite an old
  document to upgrade it.
- In version 3, compute `repository.status_sha256` from the exact raw bytes of
  `git status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none`.
  Set `repository.status_hash_format` to
  `git-status-porcelain-v1-z-untracked-files-all`.
- Version 2 computed `repository.status_sha256` from the readable output of
  `git status --short --untracked-files=all`. A version 2 status hash and a
  version 3 status hash are not directly comparable. Report the representation
  mismatch and compare the remaining repository evidence independently.
- Keep readable status output separate from the status hash input. Display
  formatting and line splitting do not define repository identity.
- Enumerate untracked files from the raw NUL-delimited output of
  `git ls-files --others --exclude-standard -z`. Decode supported paths as
  strict UTF-8 and report unsupported path encodings instead of substituting
  characters.
- Compute staged and unstaged diff hashes from raw command output through
  `capture_git_state.py`; their representation is unchanged between versions 2
  and 3.
- Use the SHA-256 of empty bytes for an empty staged or unstaged diff.
- Keep `repository.root` as `.`. Put machine-specific absolute paths nowhere in
  the portable document unless they are unavoidable and explicitly identified.
- Keep every persistent project-specific artifact under the target project's
  ignored `doc/handoffs/` directory. The installed Skill directory contains
  reusable Skill files only and remains read-only during handoff and resume.

## Evidence and decision labels

Use labels sparingly:

- `[USER_DECISION]` for important requirements and choices explicitly confirmed
  by the user.
- `[VERIFIED]` for scientific or numerical conclusions supported by identified
  evidence.
- `[AGENT_INFERENCE]` for scientific interpretation or Agent judgment.
- `[UNKNOWN]` when evidence is insufficient.

Do not label routine status lines.

## Source-of-truth order

1. Current system, user, and project instructions.
2. Current repository state and authoritative external systems.
3. Referenced artifacts at their recorded revision.
4. The handoff document.
5. Reconstructed conversation memory.

Report conflicts instead of silently choosing a lower-ranked source.
