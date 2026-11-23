# Bounded backend interruption — 2026-11-22

VERIFIED using Kubernetes 1.37.0, etcd 3.7.0 and Flux kustomize-controller 1.10.1. Three paired repetitions suspended only the fixture's own etcd process for a nominal ten seconds immediately after publishing the final source revision. The admission webhook continued allowing writes. All six runs restored the backend, reached the expected final ConfigMap data and applied revisions, observed every Kustomization Ready at the target revision, and stopped all child processes.

| Treatment | Requests overlapping the pause, three runs | Post-resume convergence seconds, three runs |
| --- | --- | --- |
| Default | 6, 4, 5 | 2.389, 5.250, 7.920 |
| Native tuned | 1, 1, 1 | 3.005, 2.492, 7.143 |

Observed pause durations were approximately 10.000–10.004 seconds. Total latency at the 99th percentile for requests overlapping the fault was approximately ten seconds in every run. These observations confirm the backend interruption affected real API requests.

Most affected requests were already in flight when the pause began. Counting only requests started during the fault would show zero to five requests and miss much of the waiting work. The analyzer therefore records both started-during-phase counts and requests whose audited intervals overlap a phase. Summed overlap duration measures request time in flight, including waiting. It is not a CPU or etcd-work measurement.

The tuned treatment reduced concurrency in flight during this small interruption. Median recovery observations were 5.250 seconds for default and 3.005 seconds for tuned, with overlapping ranges. Three repetitions, a fixed treatment order, a single local backend and this small workload do not support a general recovery-performance claim.

This experiment did not establish recurring amplification beyond native controls. There was no fault-only control group without GitOps, no competing recovery-critical client, and no sustained latency profile long enough to exercise multiple timeout/retry cycles. The source revision was committed immediately before the pause, so treatment-dependent progress before the pause remains part of the observation. Further causal experiments and current operator evidence remain necessary before selecting a JANUS intervention.

## Evidence and lifecycle correction

[Machine-readable results](../../experiments/admission-contract/evidence/2026-11-22/backend-comparison.json) retain input hashes, request counts, latency observations, measured pause intervals, resume-event counts, final convergence and cleanup. Raw audit events, metrics, manifests and object snapshots were retained locally. The measured producer code is preserved in commit `eb82485` and identified by the scenario hash in each result.

One default run recorded two idempotent resume signals because the watchdog and main thread raced. The backend's first resume defines the end of the fault in the analysis. This duplicate did not extend the pause. The fixture now serializes resumption and captures transition timestamps before writing events to disk. Subsequent lifecycle checks exercise normal watchdog resumption and termination during an active pause.

An earlier backend-pause attempt lost a timeline event through concurrent file appends and was excluded. The six runs above used serialized event writes. Earlier preliminary runs, interrupted cohorts and failures are retained locally and summarized in [the experiment record](0006-flux-native-controls.md).

## Immutable runtime pins

* Kubernetes v1.37.0 — `f54c212e3a2f75d674b717a9b29052b20b60aefc`
* etcd v3.7.0 — `4d71f7c83a2cef992d57abd3284edfaf66c91a4a`
* Flux kustomize-controller v1.10.1 — `746d9d2d360bbc7a5ee75ab79dadcf05e48ab927`

Executable, CRD, scenario and image hashes are included in the evidence. Image attestation verification and a plugin-backed security scan remain incomplete, as documented in the native-control finding.
