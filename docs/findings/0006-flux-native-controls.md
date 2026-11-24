# Flux native-control comparison — 2026-11-22

VERIFIED using Kubernetes 1.37.0, etcd 3.7.0 and Flux kustomize-controller 1.10.1 on local WSL2. Three paired repetitions used eight Kustomizations and 32 ConfigMaps, with equivalent revision updates during healthy observation and a 35-second admission-rejection window. All six runs reached the final data and applied revisions, observed every Kustomization Ready at the target revision, and stopped every child process.

| Treatment | Fault-window API requests, three runs | Post-fault convergence seconds, three runs |
| --- | --- | --- |
| Default controller concurrency and inherited retry | 544, 542, 596 | 9.850, 10.359, 10.893 |
| Tuned retry, concurrency and dedicated APF level | 272, 272, 288 | 30.107, 33.136, 32.058 |

Median fault-window request count fell from 544 to 272 with native tuning. Median post-fault convergence increased from 10.359 to 32.058 seconds. Request counts attribute completed non-watch API requests to the controller's dedicated identity and include dry-run, status and event operations. The observed tradeoff supports comparing native controls before designing a new mechanism.

Healthy-window request counts were 569, 584 and 518 for the default treatment and 584, 550 and 509 for the tuned treatment. Fault periods therefore did not consistently produce more total requests than healthy periods. This experiment does not establish the original degradation-amplification hypothesis.

Fault responses included HTTP 504 as well as 429. Denial decisions received by the fixture exceeded the number of client-visible 429 responses. Flux's pinned SSA ApplyAll source uses a concurrency-limited errgroup with a shared cancellation context. Cancellation of sibling requests after a failure is consistent with the recorded context-cancellation logs. This is an inference about the mixed status pattern, rather than a complete trace of each individual request.

The pinned source is `fluxcd/pkg` commit `4bf3ea935541baf8b254aa52aeff62335b563113`, module tag `ssa/v0.83.0`. See [ApplyAll lines 257–414](https://github.com/fluxcd/pkg/blob/4bf3ea935541baf8b254aa52aeff62335b563113/ssa/manager_apply.go#L257). Retry scheduling was observed in controller logs at 10s and 30s and corresponds to [GetRetryInterval](https://github.com/fluxcd/kustomize-controller/blob/746d9d2d360bbc7a5ee75ab79dadcf05e48ab927/api/v1/kustomization_types.go#L393).

APF metrics confirmed dispatch through the dedicated `janus-controller` FlowSchema in the tuned treatment. This small workload had no competing client or demonstrated APF saturation. The treatment bundles retry interval, reconciliation concurrency and APF changes, so their individual effects cannot be inferred.

The experiment used a synthetic local source artifact and a complete API server. It did not run the source-controller, clone Git, inject storage latency or validate customer demand. The treatment order was fixed, default then tuned. Three repetitions provide descriptive observations, with host interference and measurement overhead still possible.

Reproduce with [the Flux experiment guide](../../experiments/admission-contract/FLUX.md). [Machine-readable results](../../experiments/admission-contract/evidence/2026-11-22/native-comparison.json) include input hashes, phase counts, statuses, latencies, convergence and cleanup status. Raw audit, metrics, source archives and object snapshots were retained locally.

## Failed and excluded work

* Preliminary Flux runs used Kubernetes 1.34. That version falls outside the documented Flux support window and is excluded from the supported baseline. Kubernetes 1.34 admission-contract results remain scoped to their tested version.
* An initial TLS fixture serialized handshakes and wrote event data synchronously before replying. Healthy webhook timeouts invalidated that setup. TLS now runs in worker threads, with buffered admission-event recording.
* A single simultaneous Ready snapshot incorrectly rejected a healthy state during periodic reconciliation. The check now observes each Kustomization Ready at the target revision and verifies all final object data and applied revisions.
* Source archives initially shared one mutable response body. They now retain distinct immutable bodies by revision to prevent overlap between fetches.
* A shell invocation lost loop-variable arguments while crossing PowerShell/WSL. A shell script was used for the execution loop.
* An initial backend-pause experiment lost a timeline event through concurrent appends from the timer and main thread. Its data is excluded. Timeline writes are now serialized.
* The security plugin could not resolve the supplied local Git worktree and did not start a scan. Direct source review continued. Image attestation verification failed first with a network error and then HTTP 404. Both verification gaps remain explicit.

Subsequent Standard source scanning, image-signature verification and source-release provenance verification are recorded in [the November 24 finding](0008-security-and-provenance.md). Container-image SLSA provenance remains a separate unresolved item.
