# Formal planning runtime contract

This document defines the runtime side of the cross-repository boundary with
`chboishabba/dashi_agda`.

## Ownership split

`dashi_agda` owns:

- semantic carriers and invariants;
- finite depth/truncation and escalation rules;
- spatial-path, conservation, calibration, Pareto, evidence, governance, and
  deployment receipt shapes;
- promotion and non-promotion boundaries.

Living Environment System owns:

- GIS ingestion and reprojection;
- process-model adapters and numerical runs;
- latent/surrogate training and inference;
- scenario generation and optimisation;
- map and report outputs;
- serialisation of evidence into runtime receipts.

A structurally valid runtime receipt is not proof that its external data are
true. Artifact hashes, provenance, validation, and human/domain approval remain
mandatory.

## Python contract

`les.contracts.planning_receipt` provides:

- hashed `Artifact` references;
- Path A/B/C `ModelLane` values;
- fail-closed `EscalationEvidence`;
- explicit conservation balances with bounded residuals;
- unit-labelled objective vectors;
- finite Pareto dominance and front extraction;
- `PlanningRuntimeReceipt.validate()`.

Escalation occurs when any of the following is true:

- the input lies outside surrogate training support;
- residual error is too large;
- uncertainty is too large;
- conservation fails;
- the decision is policy-critical.

A single escalation advances Path A to B or Path B to C. Path C is fixed.
Deployment additionally requires Path C and completed human approval.

## Springfield pond fixture

The Agda golden scenario is intentionally synthetic. The runtime implementation
should eventually supply audited artifacts for:

1. DEM and catchment boundaries;
2. drainage and stormwater connectivity;
3. rainfall and antecedent moisture;
4. land use and nutrient-source layers;
5. pond geometry and residence time;
6. nutrient and pondweed observations;
7. candidate intervention footprints;
8. labour, machinery, fuel, maintenance, and capital costs;
9. model calibration and held-out validation;
10. community, ecological, engineering, and regulatory review.

Expected output layers include ranked source hypotheses, candidate
interventions, Pareto membership, uncertainty, model-lane escalation, and
provenance.
