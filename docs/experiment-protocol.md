# Controlled experiment protocol (draft)

## Safety

Use a disposable, isolated cluster with no production credentials, applications, or network dependencies. Bound fault duration and resource usage. Capture all results before teardown.

## Reproducibility metadata

Record Kubernetes, etcd, Argo CD/Flux, container runtime, kernel, VM type, configuration, manifests, and image digests. Pin versions before testing.

## Treatments

A. Native defaults.
B. Tuned APF plus native controller concurrency/retry controls.
C. Admission-based selective shedding (only if semantics and safety are proven).
D. Earlier intervention / reconciliation coordination candidate.

## Procedure

1. Capture healthy steady-state metrics and workload convergence.
2. Apply an identical controlled fault and workload profile for each treatment.
3. Record request attribution, latency, APF queueing/rejections, etcd fsync metrics, retries, and controller reconciliation outcomes.
4. Restore the fault, measure recovery and convergence, and check persistent drift.
5. Repeat runs and preserve raw evidence and experiment metadata; do not claim statistical significance from one run.

## Primary outcomes

- Recovery time and reconciliation convergence time.
- API-server request latency distribution and failed requests by client/verb.
- APF queue length, wait duration, and rejection rate.
- etcd persistence latency and resource saturation.
- Recovery-critical write success and post-recovery desired-state correctness.

## Interpretation

A lower request count alone is not success. Candidate must outperform the tuned-native baseline while preserving correctness. Single-node experiments are exploratory and cannot establish enterprise-scale behavior.
