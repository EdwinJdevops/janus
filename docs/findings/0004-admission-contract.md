# Finding 0004 — Synthetic AdmissionReview contract

Date: 2026-11-16

## Executed locally

`go test -race ./...` passed for `internal/admission` using Go 1.23.2.

The test invokes a local HTTP handler using `httptest`, supplies a synthetic AdmissionReview request, and checks:
- HTTP transport response status is 200.
- AdmissionReview.response.allowed is false.
- AdmissionReview.response.status.code is 429.
- The request UID is preserved.
- Invalid requests are rejected.

## Limits

This is **not** a Kubernetes API-server integration test. It does not demonstrate:
- the client-visible status after API-server admission processing;
- whether Argo CD or Flux retries, and on what schedule;
- any reduction in APF queueing or etcd latency;
- correctness of failurePolicy Ignore under runtime failures.

The handler is a synthetic test fixture, not a deployable webhook or production mitigation.

## Next gate

Use an isolated, disposable Kubernetes cluster to exercise a real ValidatingWebhookConfiguration with a scoped test resource, verify client-visible responses and retry traces, then compare native APF/controller tuning before evaluating Janus.
