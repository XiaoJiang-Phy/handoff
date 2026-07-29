# Cross-platform portability

Optimize the default path for bidirectional Codex ↔ Antigravity transfer on the
same Mac and shared Git checkout.

## Shared-checkout protocol

- Use `project-linked` mode.
- Store immutable handoffs in `doc/handoffs/`.
- Store only the latest relative filename in `doc/handoffs/LATEST`.
- Verify that `doc/` is ignored before writing. Do not modify ignore rules.
- Reference repository content with relative POSIX-style paths.
- Record full HEAD and working-tree hashes. Do not create a patch, commit, stash,
  branch, or full diff for handoff.
- Keep one primary repository. Describe rare related repositories as optional
  artifacts only when they affect the next action.

Use the same protocol in both directions. Map capability names before
platform-specific Skill names:

| Capability | Codex | Antigravity |
|---|---|---|
| Session transfer | `handoff` | `handoff` |
| Physical preflight | `sci-validator` | `sci_validator` |
| Physical anomaly audit | `physics-audit` | `physics_audit` |

Verify availability at resume time; the mapping does not prove installation.

## LATEST semantics

- Write a timestamped handoff first.
- Validate it before updating `LATEST`.
- Update `LATEST` atomically with the timestamped file's basename.
- Keep the old pointer unchanged when writing or validation fails.
- Reject absolute paths, parent traversal, nested paths, missing targets, and
  malformed filenames.
- Never fall back to whichever handoff has the newest modification time.
- Never delete, archive, overwrite, or mark a historical handoff consumed.

## Language and filenames

- Keep headings and JSON field names in English.
- Follow the source conversation's primary language for prose.
- Use an English `kebab-case` topic in the filename.
- Preserve code, commands, paths, identifiers, mathematics, paper titles, and
  exact quotations.

## Standalone export

Use `standalone` only when the user explicitly needs another machine or a
non-shared filesystem.

- Reassess privacy before export. Do not directly export the private
  project-linked handoff.
- Embed only essential content that the receiver cannot access.
- Attach or link authoritative artifacts when permitted.
- Identify omitted private or oversized artifacts by relative identity and hash.
- Never embed credentials or private keys.

## Privacy boundary

The ignored private handoff may contain unpublished results, negative results,
internal judgments, necessary parameters, and private relative paths. It may not
contain credentials, passwords, tokens, private keys, or unrelated personal
information. Record large or private data by path, identity, hash, and access
requirements rather than embedding it.
