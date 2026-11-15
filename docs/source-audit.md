# Source audit register

Status: OPEN — source paths and release tags must be verified before claims are marked confirmed.

## Audit requirements

For each claim record: project, exact release tag and commit SHA, file path and lines, execution path, evidence excerpt, behavior under failure, and an executable test or trace. A documentation reference alone is insufficient for a retry-path claim.

| ID | Project | Claim to test | Required evidence | Status |
| --- | --- | --- | --- | --- |
| S01 | Kubernetes API server | Validating admission denial with Status.Code=429 propagates to client as expected | Version-pinned handler and response traces | OPEN |
| S02 | Kubernetes API server | failurePolicy Ignore affects webhook call failures but not allowed=false | Version-pinned code and integration test | OPEN |
| S03 | Kubernetes APF | FlowSchema matching can isolate GitOps controller service accounts | Version-pinned configuration, metrics and request traces | OPEN |
| S04 | Argo CD | Specific apply failure produces retry/backoff rather than tight loop | Controller call graph and observed timings | OPEN |
| S05 | Flux | Apply failures are retried at bounded intervals with jitter | Controller call graph and observed timings | OPEN |
| S06 | Kubernetes admission | Admission does not intercept every write operation | API-server operation matrix and test | OPEN |
| S07 | Kubernetes metrics | Selected etcd and inflight metrics exist with expected labels and semantics | Metric exposition from pinned versions | OPEN |

## Evidence rules

- Do not infer client-visible HTTP status from AdmissionReview JSON alone.
- Do not infer a global API-server load reduction from webhook rejection counts.
- Record separate results for CREATE, UPDATE, PATCH, DELETE and subresources.
- Capture client identity, response status, APF priority level, retries, and convergence.
- Preserve counterexamples and failed hypotheses.
