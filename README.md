# Project Janus

Reproducible experiments for Kubernetes admission behavior, GitOps retries and control-plane recovery.

**Experimental research preview. Product effectiveness and operator demand remain under investigation.**

The [local admission experiment](experiments/admission-contract/README.md) verifies client-visible HTTP status, failure policy behavior, namespace isolation and object persistence against a disposable API server. [Results from November 21, 2026](docs/findings/0005-real-admission-contract.md) record seven passing cases and the remaining evidence gaps.

Six Flux runs against Kubernetes 1.37.0 and etcd 3.7.0 measured a native-control tradeoff. Tuning reduced median request count during a 35-second admission-denial window from 544 to 272. Median post-fault convergence increased from 10.36 to 32.06 seconds. All 32 managed ConfigMaps and eight Kustomizations converged in every run. [Protocol and limitations](docs/findings/0006-flux-native-controls.md)

Six further runs paused the disposable etcd backend for ten seconds. All recovered the final workload state. These runs establish bounded interruption and recovery behavior for this fixture. [Backend experiment and limitations](docs/findings/0007-bounded-backend-interruption.md)

## Run the experiments

Use Linux amd64 or WSL with Python 3.11+, OpenSSL, curl, tar and an accessible Docker daemon for asset extraction. The experiments create a loopback-only control plane with temporary credentials. Runtime uses the extracted binaries.

```bash
bash experiments/admission-contract/prepare-assets.sh /tmp/janus-assets
python3 experiments/admission-contract/run.py \
  --assets /tmp/janus-assets/envtest/controller-tools/envtest \
  --flux-assets /tmp/janus-assets/flux \
  --treatment default \
  --output /tmp/janus-run-default
```

Choose `--treatment tuned` for the native-control comparison and a fresh output directory for every run. Add `--fault-mode etcd-pause` for a bounded ten-second interruption of the fixture's own backend. [Experiment details](experiments/admission-contract/FLUX.md)

Evidence includes input hashes, controller logs, API audit records, metrics, final object state and cleanup status. [Compare completed runs](experiments/admission-contract/analyze_flux.py)

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

Licensed under Apache-2.0. See [LICENSE](LICENSE).
