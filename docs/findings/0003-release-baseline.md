# Release baseline candidates — 2026-11-15

Upstream release listings checked:
- Argo CD v3.6.1, published 2026-11-04: https://github.com/argoproj/argo-cd/releases/tag/v3.6.1
- Flux kustomize-controller v1.10.1, published 2026-10-26: https://github.com/fluxcd/kustomize-controller/releases/tag/v1.10.1

These are **release tag candidates**, not immutable full-commit pins. Kubernetes release and complete source SHAs remain unresolved. Do not report source-level audit complete.

## Local test executed

A standard-library Go probe emits timestamped JSONL HTTP status results. Unit tests with httptest confirm three explicitly scheduled requests to a mock 429 endpoint and argument validation.

This is **not** a Kubernetes admission integration test, does not simulate Argo CD or Flux, and does not prove controller retry behavior.

Command: `go test ./...`
Probe usage: `go run ./cmd/retryprobe -url http://127.0.0.1:8080 -attempts 3 -interval 1s`
Only probe endpoints you control or are authorized to test.
