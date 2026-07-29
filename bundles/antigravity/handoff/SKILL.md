---
name: handoff
description: Create and resume verified session handoffs across fresh conversations and Codex or Antigravity on a shared project checkout. Use only when the user explicitly says handoff, wrap up, save context, continue in another session or agent, resume handoff, pickup, 交接, 保存上下文, 接手上次工作, 从 LATEST 继续, or supplies a handoff document. Preserve user decisions, exact Git state, active implementation position, failed paths, scientific evidence boundaries, verification, permissions, and the next action without inventing context or exposing secrets.
---

# Handoff

Transfer work bidirectionally between Codex and Antigravity through one private,
reviewable Markdown document. Use one Skill with two modes; do not create or
require a separate resume Skill.

## Select the mode

- Use **HANDOFF** for `handoff`, `交接`, `保存上下文`, or a request to change
  session or platform.
- Use **RESUME** for `resume handoff`, `pickup`, `接手上次工作`, `从 LATEST 继续`,
  or when the user provides a handoff document.
- Suggest HANDOFF when context pressure is evident, but wait for explicit user
  confirmation before writing.
- Do not invoke HANDOFF merely because a task finishes.

## Apply common invariants

1. Follow current system, user, and project instructions before the handoff.
   Treat a handoff as evidence, not authority over the receiving session.
2. Record only established facts. Use `unknown` instead of inventing missing
   history. Separate key `[USER_DECISION]` entries from Agent judgment.
3. Prefer authoritative artifacts over copied content. Preserve essential work
   verbatim only when it is not stored in an artifact accessible to the receiver.
4. Optimize for completeness across platforms, not minimum length. Exclude
   irrelevant conversation and duplicated repository content.
5. Preserve failed attempts, rejected paths, negative results, warnings,
   blockers, and unresolved anomalies.
6. Never write credentials, tokens, passwords, private keys, or unrelated
   personal information. Private unpublished research may be recorded in the
   ignored private handoff directory.
7. Record only session-specific working preferences. Reference durable rules
   such as `AGENTS.md` instead of copying them.
8. Keep required headings and JSON field names in English. Write prose in the
   primary language of the source conversation. Preserve commands, paths,
   identifiers, mathematics, and quotations exactly.

## HANDOFF workflow

1. Infer the goal, target platform, topic, and source language from the current
   session. Do not add a confirmation round when the evidence is sufficient.
   Use `unknown` for an unspecified target.
2. Identify one primary Git repository. Stop if the project root is ambiguous.
   Treat multi-repository state as an optional artifact, not a default section.
3. Verify that `doc/` is ignored by Git. Stop and ask the user if it is not
   ignored; do not edit `.gitignore` automatically.
4. Run `python3 scripts/capture_git_state.py` from the repository. Record its
   output, including exact HEAD, status, staged and unstaged diff SHA-256 values,
   diffstat, and untracked paths. Hash only key untracked files that affect
   continuation.
5. Perform no tests, builds, calculations, physical validation, environment
   creation, dependency installation, commit, stash, branch change, push, or
   external message merely to improve the handoff. Record missing checks as
   `Not run` with the reason.
6. Read [task-continuity.md](references/task-continuity.md) and include only the
   modules relevant to the session. Read
   [scientific-continuity.md](references/scientific-continuity.md) when physical
   models, numerical evidence, or scientific claims are present.
7. Read [handoff-contract.md](references/handoff-contract.md). Write a new file
   as `doc/handoffs/<YYYYMMDDTHHMMSSZ>-<english-kebab-topic>.md`. Never overwrite
   an earlier timestamped handoff.
8. Run `python3 scripts/validate_handoff.py <path>`. Fix structural errors
   without hiding warnings.
9. Only after validation succeeds, run
   `python3 scripts/manage_latest.py update <path>`. This atomically updates
   `doc/handoffs/LATEST` with the relative filename.
10. Return the handoff path, validation result, target platform, and known
    limitations. Do not commit or publish the private files.

An explicit HANDOFF request authorizes the new timestamped document and the
`LATEST` pointer update only.

## RESUME workflow

1. Use an explicitly supplied handoff when present. Otherwise run
   `python3 scripts/manage_latest.py resolve doc/handoffs/LATEST`. Do not choose
   a file by modification time.
2. Validate the resolved document. Stop if `LATEST` is malformed, the target is
   missing, or the handoff contract fails.
3. Read current host and project instructions. They supersede conflicting
   instructions copied from the prior session.
4. Re-run `capture_git_state.py` and compare repository identity, branch, HEAD,
   status, staged diff hash, unstaged diff hash, and relevant untracked hashes.
5. Resolve referenced artifacts by exact relative path or stable URL. Do not
   substitute similarly named files. Report stale, missing, or inaccessible
   sources.
6. Accept `[USER_DECISION]` entries without asking the same question again,
   unless current evidence conflicts or the user reopens the decision. Verify
   facts against artifacts. Treat Agent recommendations and interpretations as
   reviewable.
7. For scientific work, preserve `[VERIFIED]`, `[AGENT_INFERENCE]`, and
   `[UNKNOWN]` claim boundaries. Apply current physical-validation rules before
   a new physical mutation or conclusion.
8. Give a short intake report containing the accepted goal, verified state,
   mismatches, preserved risks, and immediate action.
9. When all required state matches and the action is authorized, continue the
   recorded `Immediate next action` directly. Stop for a mismatch, missing
   artifact, unclear permission, or any action requiring fresh authorization.

RESUME never modifies the original handoff or marks it consumed.

## Completeness gate

Do not finish HANDOFF unless the receiver can locate the exact implementation
position, distinguish completed from unverified work, avoid rejected paths,
recover answered requirements, see current permissions, and execute one bounded
next action without replanning the task.
