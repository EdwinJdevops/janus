# Finding 0002 — GitOps reconciliation is not a single retry loop

Date: 2026-11-15
Status: Upstream documentation and upstream test evidence reviewed; release-pinned runtime behavior not verified.

## Argo CD

- Automated sync semantics and exponential retry configuration are documented: https://github.com/argoproj/argo-cd/blob/master/docs/user-guide/auto_sync.md
- Application controller supports workqueue rate limits and global throttling: https://github.com/argoproj/argo-cd/blob/master/docs/operator-manual/high_availability.md
- Upstream controller tests include a case asserting a requeue after remaining retry backoff: https://github.com/argoproj/argo-cd/blob/master/controller/appcontroller_test.go

## Flux

- Kustomization .spec.retryInterval controls failed reconciliation retries and defaults to .spec.interval.
- Generation and source revision changes can trigger reconciliation outside the interval.
- Source: https://github.com/fluxcd/kustomize-controller/blob/main/docs/spec/v1/kustomizations.md

## Consequence

The claim that GitOps clients simply retry every rejected API write in a tight loop is unsupported. A useful Janus experiment must distinguish: periodic reconciliation, source-change triggers, drift/self-heal triggers, explicit operation retries, and workqueue retries.

## Next source-level verification

Pin immutable release tags and commit hashes. Trace API write errors to controller workqueue requeue scheduling. Run client-visible admission-denial integration tests. Measure per-controller request attribution under controlled faults.

## Falsification

If native APF and controller tuning eliminate the attributable excess load without unacceptable recovery delay, do not build the webhook mechanism.
