# Real admission contract — 2026-11-21

VERIFIED on a disposable loopback-only Kubernetes v1.34.0 API server with etcd 3.6.4, using the controller-tools envtest-v1.34.0 linux-amd64 assets. Archive SHA256 `9c45e40aa56971b105e596ebb3e84af6742e8709cc0523733baf8d9bb725e69c` was checked before execution. Binary versions and hashes are recorded by the experiment.

| Case | Client HTTP status | Object after request |
| --- | --- | --- |
| Healthy baseline | 201 | Present |
| Explicit denial, Ignore | 429 | Absent |
| Outside selected namespace, Ignore | 201 | Present |
| Explicit denial, Fail | 429 | Absent |
| Outside selected namespace, Fail | 201 | Present |
| Webhook connection refused, Ignore | 201 | Present |
| Webhook connection refused, Fail | 500 | Absent |

The first seven-case run passed. A second run of the repository harness added persistence assertions and binary metadata and passed all seven cases. Both control-plane processes were terminated, and temporary certificates, tokens and etcd data were removed. Output directories retained response bodies, AdmissionReviews and process logs locally.

An initial startup attempt failed with `Text file busy` because archive extraction was still writing kube-apiserver. The harness now terminates previously started children when a subsequent child fails to start. Extraction completed before the successful runs. A script launched through stdin also failed its document-presence check because its script-relative path changed. Executing the checked-in shell script with LF line endings passed.

The API server logs contain loopback-address errors from its default Kubernetes Service endpoint reconciler. Admission requests and persistence checks succeeded. This fixture deliberately advertises loopback and supplies no node or controller-manager. These log errors must be considered when using the fixture for broader experiments.

## Design implication

An explicit denial can send HTTP 429 to a client. `failurePolicy: Ignore` still permits that denial to reject the request. An unreachable webhook fails open under Ignore. These observations resolve one protocol question and one outage case for this version.

The Python webhook is an independent AdmissionReview fixture. The experiment does not execute the repository's Go handler. Go race tests separately exercise that handler using httptest.

PENDING are timeout and malformed-response cases, UPDATE/PATCH/DELETE and subresources, Retry-After and actual controller retry behavior, APF baselines, attributed GitOps amplification, fault recovery, convergence, workload correctness and operator demand. No overload-control mechanism has passed a product validation gate.

## Reproduction

Use [the experiment instructions](../../experiments/admission-contract/README.md). The runner accepts explicit assets and fresh evidence directories and never loads a kubeconfig.

## Immutable upstream source candidates

* Kubernetes v1.34.0 — `f28b4c9efbca5c5c0af716d9f2d5702667ee8a45`
* Argo CD v3.6.1 — `94037c4d4e1af4bd0651d37a179fbd9e347e668c`
* Flux kustomize-controller v1.10.1 — `746d9d2d360bbc7a5ee75ab79dadcf05e48ab927`
* etcd v3.6.4 — `5400cdc39b829ee5dadacb77002256cf86357da1`

These candidates were resolved through Git refs. Only Kubernetes and etcd were executed in this experiment. Controller image digests and full retry/APF source audits remain pending.
