# Falsifiable hypotheses

## H1 — Amplification

Under an injected control-plane/storage degradation, automated GitOps reconciliation causes measurable additional API-server or etcd load beyond the injected fault.

**Reject if:** attributable excess load cannot be reproduced.

## H2 — Native-control gap

Tuned APF and documented Argo CD/Flux reconciliation controls fail to sufficiently contain that additional load without unacceptable recovery delays.

**Reject if:** native controls achieve equivalent safety and recovery.

## H3 — Safe intervention

A candidate intervention can reduce harmful reconciliation work without blocking recovery-critical writes or leaving unacceptable persistent drift.

**Reject if:** intervention impairs recovery or convergence.

## H4 — Practical adoption

Operators report a recurring incident pattern, can provide supporting traces or incident reports, and would accept the integration/operational risk.

**Reject or narrow if:** evidence is anecdotal, rare, or already adequately mitigated.

## Open questions

- Is the original 429 admission denial mapped to client-visible HTTP 429, and what exact retry path follows?
- Which API verbs/resources are admitted versus bypass admission?
- Which identities and request contexts safely distinguish GitOps writes from recovery actions?
- How should telemetry staleness, partitions, and conflicting signals affect decisions?
- Is early controller-side intervention or APF adaptation superior to admission rejection?

These questions must be answered by version-pinned source review and experiment traces, not assumed.
