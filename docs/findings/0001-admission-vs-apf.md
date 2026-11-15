# Finding 0001 — Admission rejection versus APF (documentation-level)

Date: 2026-11-15
Status: DOCUMENTATION VERIFIED; SOURCE-LEVEL AND RUNTIME VERIFICATION PENDING

## Verified from Kubernetes official documentation

1. APF classifies requests using FlowSchemas and PriorityLevelConfigurations, isolates concurrency, queues requests, and can reject overload with HTTP 429. It already supports service-account-specific matching.
   Source: https://kubernetes.io/docs/concepts/cluster-administration/flow-control/
2. Webhook failurePolicy Ignore applies to errors invoking the webhook. It does not override a successfully transmitted AdmissionReview with allowed=false.
   Source: https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/
3. Kubernetes documents an admission webhook rejection metric with rejection_code, and describes honoring webhook status codes >=400. This does NOT establish client-specific retry timing.
   Source: https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/
4. Kubernetes warns admission webhooks can create dependency loops with components they depend upon.
   Source: https://kubernetes.io/docs/concepts/cluster-administration/admission-webhooks-good-practices/

## Architectural consequence

A Janus admission webhook must not claim novelty in generating 429 responses or service-account-based isolation. A successful allowed=false response is a deliberate denial even when failurePolicy=Ignore. Test client-visible status and actual Argo CD/Flux retry behavior before relying on it.

## Unverified

- Exact API-server implementation at a pinned release commit.
- GitOps controller retry path and timings.
- Whether earlier intervention improves recovery compared with tuned APF.
- Any performance claim, including 200 microseconds.

## Required next evidence

Pin releases; inspect implementation paths; capture API-server request/response traces and controller retry timestamps in an isolated cluster. Compare APF-only baseline first.
