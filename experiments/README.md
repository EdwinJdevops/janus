# Experiment harness — preparation

No experiment has been run. No cloud VM has been provisioned.

## Experimental matrix

A. Defaults, no induced fault.
B. Defaults, controlled fault.
C. Tuned APF and native controller settings, identical fault.
D. Candidate intervention, only after source audit and recovery-safety proof.

## Measurement contract

Record exact release versions and image digests, UTC timestamps, fault start/stop, per-client request counts and errors, APF queueing and rejections, etcd fsync latency, convergence time, and correctness checks.

## Abort conditions

Stop on loss of administrative access, inability to restore the fault, resource exhaustion outside the experiment scope, or failed cleanup.

## Non-claims

A single-node VM is not a representative multi-node control plane. Admission denial counts are not proof of recovered API-server capacity.
