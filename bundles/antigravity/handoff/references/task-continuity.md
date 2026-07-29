# Task-specific continuity

Include only modules that affect the next session. Put their content under
**Task-specific continuity** and keep authoritative details in referenced
artifacts.

## Code implementation and debugging

- Record files changed and the exact function, type, test, or line of work where
  implementation stopped.
- Record build, test, lint, sanitizer, benchmark, and numerical-regression
  commands actually run.
- Preserve the smallest useful failure excerpt with the full log path.
- Record interface, layout, compatibility, and performance constraints.
- Use **Execution plan** to preserve completed, active, and pending Nodes plus
  each gate.

## Local numerical validation

- Record the model or algorithm, parameters, input identity, random seed when
  applicable, environment, command, and output paths.
- Record units, tolerances, convergence criteria, uncertainty, and applicability
  boundaries from authoritative sources.
- Preserve negative results and incomplete runs.
- Do not run a calculation merely to complete the handoff.

Do not add specialized Slurm or PBS fields by default. This Skill primarily
supports local development and small validation runs. Represent an unusual
remote job through **Running tasks** only when it directly affects continuation.

## Anomaly diagnosis and physical interpretation

- Identify immutable findings, evidence classes, competing explanations,
  counterevidence, and minimum unresolved checks.
- Use `[VERIFIED]`, `[AGENT_INFERENCE]`, and `[UNKNOWN]` only where claim
  boundaries matter.
- Do not assign root cause or convert a non-PASS into resolved prose.

## Literature search and reading

- Record DOI, arXiv ID, exact title, and stable URL.
- Record what was actually read: abstract, section, page, figure, or supplement.
- State what each source supports and what remains unverified.
- Reference local PDFs by relative path and SHA-256 when identity matters.
- Do not copy full papers or treat search-result summaries as paper content.
- Do not capture Zotero, BibTeX, or other library state unless the user
  explicitly requests it.

## Writing and documentation

- Record the target document, intended audience, current section, argument
  status, unresolved wording, and required evidence or citations.
- Reference the current draft by path. Include exact text only when it exists
  solely in the conversation.
- Preserve publication status and private/public boundaries.

## Project design and planning

- Record accepted scope, non-goals, decision owners, milestones, Node gates,
  blockers, dependencies, and completion criteria.
- Reference plans and ADRs rather than duplicating them.
- Preserve the active plan position so the receiver does not restart planning.

## Environment

Record only task-relevant environment state:

- active Conda or virtual environment name and Python path;
- compiler, CMake, CUDA, MPI, or external-solver versions when relevant;
- actual build and test commands;
- dependency intent through `pyproject.toml`, environment files, or lockfiles.

Do not create or switch environments, install dependencies, or export complete
package lists for HANDOFF. RESUME reports an environment mismatch and does not
silently rebuild it.
