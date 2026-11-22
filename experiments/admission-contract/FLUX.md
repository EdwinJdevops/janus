# Flux native-control comparison

Runs the actual Flux kustomize-controller v1.10.1 binary against the disposable API-server fixture. A local HTTP server supplies deterministic, versioned source archives through a synthetic GitRepository status. The source-controller and a Git hosting service are outside this experiment.

Eight Kustomizations each manage four ConfigMaps. Every run performs an initial convergence, a revision update during a 35-second healthy observation, and another equivalent revision update during a 35-second admission-denial window. The webhook rejects only ConfigMap CREATE/UPDATE admission in `janus-workload`. After rejection ends, all ConfigMap data and applied revisions must match the final revision. Each Kustomization must have been observed Ready at that revision. Periodic reconciliation may transiently change conditions afterward.

| Setting | Native defaults treatment | Native tuned treatment |
| --- | --- | --- |
| Kustomization interval, chosen for this experiment | 10s | 10s |
| Retry interval | Inherits 10s interval | Explicit 30s |
| Concurrent reconciliations | 4, controller default | 1 |
| Concurrent server-side apply | 4, controller default | 4, controller default |
| APF | Bootstrap defaults | Dedicated service-account FlowSchema, Limited level, five nominal shares, zero lending, 16 queues, hand size four, queue length 16 |

The defaults treatment uses native controller defaults with an experiment-selected workload interval. It does not represent every Flux installation's configuration. The tuned treatment bundles several changes, so the experiment cannot isolate their individual effects. It has no competing API workload, so APF saturation and recovery-critical request protection are untested.

## Assets

On Linux amd64 with an accessible Docker daemon, prepare all pinned assets with `bash experiments/admission-contract/prepare-assets.sh /absolute/path/to/assets`. This downloads public inputs and extracts the controller from a temporary container without starting it. The command requires curl, tar, sha256sum and Docker. It does not start the Docker service or change existing containers. Use `/absolute/path/to/assets/envtest/controller-tools/envtest` and `/absolute/path/to/assets/flux` as the two runner asset arguments.

Use Kubernetes 1.37.0 envtest assets for this Flux comparison. Flux's documented support window begins at Kubernetes 1.35. The existing Kubernetes 1.34 admission-contract tests remain valid for that protocol experiment. Exploratory Flux runs against 1.34 are excluded from the supported baseline comparison.

Download `envtest-v1.37.0-linux-amd64.tar.gz` from the `kubernetes-sigs/controller-tools` GitHub release `envtest-v1.37.0`. Verify archive SHA256 `f03faedfc68d2a78cee5cb02618bb44e7f67044f4c5fc957f72d3307fda61a9c` before extraction. Prepare a separate Flux asset directory containing the controller executable and the five CRD files below.

The executed controller image is pinned as `ghcr.io/fluxcd/kustomize-controller@sha256:37db29b25dae35b881a5e064acedb0cc954442da453a39eaa0eab7a90dbecc4e`. Extract `/usr/local/bin/kustomize-controller` with `docker create`, `docker cp`, and `docker rm` using a new temporary container. No image process needs to run. Docker must already be available to the caller. The executable is a Linux binary.

The Kustomization CRD comes from kustomize-controller source commit `746d9d2d360bbc7a5ee75ab79dadcf05e48ab927` in `fluxcd/kustomize-controller`, at `config/crd/bases/kustomize.toolkit.fluxcd.io_kustomizations.yaml`. Save it as `kustomizations.yaml`.

The four source CRDs come from `fluxcd/source-controller` commit `701d9a9d24763b668d6ef0634cc5f88f5bfbb861`, at `config/crd/bases/source.toolkit.fluxcd.io_<name>.yaml`. This is source-controller v1.10.0, matching the API dependency recorded in kustomize-controller v1.10.1's go.mod. Save each under the corresponding short filename.

| Local filename | SHA256 |
| --- | --- |
| buckets.yaml | 86c81cb80ed002322f27a4a4042422fc04d58b418863711d09ccf85e7faf304e |
| externalartifacts.yaml | f78536e2c0c6719221adff02da257bf3d2dc20dcd9636ce304656fa3f320c102 |
| gitrepositories.yaml | ae4d504172dd9504b38d4e770842fcc086168e83707308dd56cba708f3c1daa0 |
| kustomizations.yaml | dec77e391bff9307e47898d2d7448c5083a49b85700f6f870c7849449e11aad0 |
| ocirepositories.yaml | dcb7198a1c747ad96b8ca5218d2780896800306098497159fa77ecd7aba9a886 |

The image digest and executable hash identify the tested inputs. GitHub CLI image attestation verification failed first with a network error and then HTTP 404. Signature/provenance verification remains incomplete.

## Execute

```bash
python3 experiments/admission-contract/run.py \
  --assets /absolute/path/to/envtest \
  --flux-assets /absolute/path/to/flux-assets \
  --treatment default \
  --output /absolute/path/to/fresh-run-directory
```

Repeat with `--treatment tuned`. Use identical assets and a new output directory for every run. For repeated local experiments, copying binaries to a Linux-native temporary directory avoids measuring Windows shared-filesystem binary loading overhead. Keep treatment order and host conditions in the evidence.

The harness captures metadata-level API audit events, controller logs, controller/API-server/etcd metric snapshots, manifests, final object/status snapshots, fault timestamps, binary and CRD hashes, and child-process cleanup status. Audit records attribute the controller to `system:serviceaccount:flux-system:controller`, which has a disposable cluster-admin binding and passes through APF. The harness administrator uses a separate exempt identity. Admission events are buffered in memory and persisted after fixture shutdown to keep disk writes off the response path.

```bash
python3 experiments/admission-contract/analyze_flux.py \
  /path/to/run-default /path/to/run-tuned --output /path/to/comparison.json
```

The analyzer excludes watches and attributes completed API requests by their request-received timestamp. Counts include server-side dry runs. Long-lived watches and requests crossing phase boundaries require separate interpretation. Admission decisions received by the fixture can exceed client-visible 429 responses because sibling requests may be cancelled.

This experiment measures controller behavior under admission rejection. It does not inject etcd latency or API-server resource exhaustion and cannot establish the original degradation-amplification hypothesis or production safety.
