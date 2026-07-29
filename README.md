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
