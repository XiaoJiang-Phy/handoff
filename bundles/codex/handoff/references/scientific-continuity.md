# Scientific continuity

Apply this reference when the session involves physical models, simulation
parameters, numerical evidence, scientific claims, or unexplained anomalies.
The handoff records prior evidence; it does not validate a new claim.

Do not add a separate theoretical-derivation module. Preserve a derivation only
when it is an artifact or essential portable payload needed by another routed
task.

## Required scientific content

Add **Scientific continuity** to the handoff and preserve, when applicable:

- the model, approximation, observable, parameter regime, and declared units;
- Fourier, \(i\eta\), retarded Green-function, spectral-function, and analytic
  continuation conventions;
- basis ordering, tensor axes, memory layout, normalization, boundary
  conditions, and relevant discretization;
- validator name and version, input identity, structured result, tolerance
  provenance, and exact status;
- evidence class, uncertainty, counterevidence, negative results, and known
  applicability limits;
- unresolved anomalies without assigning an unestablished cause;
- calculations, tests, writes, or parameter changes that still require fresh
  authorization.

Write `not applicable` only when the quantity is genuinely irrelevant. Write
`unknown` when the source does not establish it.

Label only scientific and numerical claim boundaries:

- `[VERIFIED]` requires identified supporting evidence and its exact status.
- `[AGENT_INFERENCE]` identifies interpretation or a proposed explanation.
- `[UNKNOWN]` identifies missing or insufficient evidence.

Do not turn these labels into decoration for routine file or process status.

## Claim boundary

- Never convert a successful command, solver convergence, schema validation, or
  numerical agreement into a physical PASS.
- Never replace a non-PASS with a summary that sounds resolved.
- Never infer a missing sign, unit, convention, normalization, tolerance, or
  approximation.
- Preserve immutable findings and reference their authoritative record instead
  of rewriting them.
- Route new physical claims through the receiving environment's physical
  validation process before acting on them.
- Route preserved anomalies to the receiving environment's anomaly-audit
  process when available, without assigning root cause.

## Resume checks

Before continuing affected scientific work:

1. Compare the recorded conventions and units with current project rules.
2. Verify referenced evidence identity, revision, and structured status.
3. Confirm that current code and parameters match the recorded commit and dirty
   state.
4. Report missing evidence or conflicts.
5. Obtain any fresh authorization required for execution, mutation, or a new
   physical conclusion.
