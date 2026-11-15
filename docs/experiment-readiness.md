# Experiment readiness checklist

Status: BLOCKED until environment and instrumentation are verified.

## Prerequisites

- [ ] Pin Kubernetes, etcd, Argo CD and Flux release tags and image digests.
- [ ] Verify cloud promotional credit or approve an explicit spending cap.
- [ ] Provision disposable, isolated infrastructure only.
- [ ] Capture baseline resource and API metrics before injecting faults.
- [ ] Establish a tested cleanup procedure and automatic teardown deadline.
- [ ] Identify recovery-critical requests and correctness checks.
- [ ] Establish maximum fault duration and abort criteria.
- [ ] Capture machine-readable run manifests, metrics, logs, and timestamps.

## First experiment

A: baseline controller defaults.
B: tuned APF and controller limits.
C and D: candidate mechanisms only after source audit and safety tests.

Do not claim representative high-scale Kubernetes behavior from a single small VM. Do not apply fault injection to production infrastructure.
