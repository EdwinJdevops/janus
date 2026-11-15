# ADR 0001: Validate mechanism before product implementation

Status: Accepted for research phase

## Decision

Do not build the proposed metrics-driven admission webhook as the default solution until the failure mechanism, existing mitigations, and admission retry semantics have been demonstrated.

## Rationale

The original design asserts uncontrolled GitOps write storms and automatic HTTP 429 backoff without adequate evidence. A webhook adds an API-server dependency and can deny recovery-critical operations even with failurePolicy Ignore.

## Alternatives under evaluation

- Native APF and controller configuration (baseline).
- Controller-side reconciliation coordination.
- Adaptive APF configuration.
- Admission-based selective rejection.

## Revisit when

Version-pinned source review, controlled traces, comparative recovery measurements, and operator interviews support a defensible mechanism.
