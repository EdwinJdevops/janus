# Project Janus

Research-stage investigation of control-plane pressure induced by automated Kubernetes reconciliation.

**Status: Hypothesis unvalidated. No production readiness or industry-first claim.**

## Objective

Determine whether GitOps reconciliation materially amplifies API-server/etcd degradation, and whether intervention improves recovery compared with tuned native Kubernetes API Priority and Fairness (APF) and controller controls.

## Validation gates

1. Reproduce attributable amplification under a controlled fault.
2. Compare against tuned native APF and GitOps concurrency/retry controls.
3. Prove recovery-critical operations are not blocked.
4. Quantify recovery time, request latency, queueing, and reconciliation convergence.
5. Validate operator demand before committing to a product mechanism.

No production cluster should be used for fault injection. No cloud resources are provisioned by this repository.

See [falsifiable hypotheses](docs/hypotheses.md), [experiment protocol](docs/experiment-protocol.md), and [architecture decision](docs/decisions/0001-validation-before-implementation.md).
