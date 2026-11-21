# Project Janus

Research-stage investigation of control-plane pressure induced by automated Kubernetes reconciliation.

**Status: Hypothesis unvalidated. No production readiness or industry-first claim.**

The [local admission experiment](experiments/admission-contract/README.md) verifies client-visible HTTP status, failure policy behavior, namespace isolation and object persistence against a disposable API server. [Results from November 21, 2026](docs/findings/0005-real-admission-contract.md) record seven passing cases and the remaining evidence gaps.

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
