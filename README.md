# Handoff

`handoff` preserves work across fresh conversations and agent platforms. It has
two modes:

- `HANDOFF` writes a verified, portable session record.
- `RESUME` checks that record against the current workspace before continuing.

The canonical Skill is `skills/handoff`. Generated installation bundles live in
`bundles/codex/handoff` and `bundles/antigravity/handoff`.

Build the bundles:

```bash
python3 scripts/build_bundles.py --authorized
```

Validate the Skill and run its tests:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/handoff
python3 -m unittest discover -s tests -v
```

Install the complete directory for the selected host. Do not merge files into an
older installation; replace the previous `handoff` directory and restart the
host so it reloads Skill metadata.

## Manual cross-platform smoke test

1. Codex explicitly requests `HANDOFF` (e.g., `handoff` or `交接`).
2. The agent writes the handoff record into the Git-ignored `doc/handoffs/` directory and updates `doc/handoffs/LATEST` after contract validation passes.
3. Antigravity executes `RESUME` using "从 LATEST 继续", validates the handoff contract, and compares repository Git state.
4. After completing work, Antigravity can explicitly request `HANDOFF` back to Codex.
5. All handoff files remain private in `doc/handoffs/` and must not be committed or pushed to version control.
