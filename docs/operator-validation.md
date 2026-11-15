# Operator validation protocol

Status: NOT STARTED. No interviews or customer commitments have been recorded.

## Target participants

Platform engineers and SREs who operate Kubernetes clusters with Argo CD or Flux; prioritize people responsible for on-call response and API-server/etcd incidents.

## Interview questions

1. During the last 12 months, did a GitOps reconciliation workload contribute to API-server or etcd saturation? What incident evidence supports that attribution?
2. What exact controller/version, workload scale, and failure condition were involved?
3. Which metrics, audit logs, traces or incident reviews are available (with sensitive data removed)?
4. What mitigations were attempted (APF, controller concurrency, retry tuning, suspension), and why were they insufficient?
5. What was the measurable impact on recovery time, operator access, and desired-state convergence?
6. Would an external component allowed to defer reconciliation be acceptable? Under which safety constraints?
7. Which writes must never be deferred? What failure behavior would disqualify adoption?
8. Would the team install a controlled experimental build in a nonproduction cluster and share measurements?

## Evidence classification

- E0: opinion without incident.
- E1: first-hand incident narrative without artifacts.
- E2: dated incident report, metrics, or logs with attributable client activity.
- E3: reproducible trace or independently repeatable experiment.

Do not treat expressions of interest as purchase commitments or usage validation.

## Go/no-go criteria

Do not assert demand or adoption until independent operators provide attributable incident evidence and at least one team agrees to a scoped nonproduction evaluation. Record refusals and existing satisfactory mitigations.
