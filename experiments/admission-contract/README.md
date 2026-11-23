# Local admission contract experiment

Starts dedicated loopback-only etcd, kube-apiserver and a TLS webhook using Python's standard library. Generates temporary certificates and credentials, scopes the webhook to ConfigMap CREATE requests in `janus-test`, and terminates child processes on completion or failure. Uses no existing kubeconfig. Requires Linux or WSL, Python 3.11+, OpenSSL, and the release binaries below.

The Python webhook is an independent protocol fixture. This experiment verifies Kubernetes admission behavior. The Go handler has its own unit tests.

Download and verify the assets before extracting or running them.

```bash
mkdir -p work/envtest
cd work/envtest
curl -fL --retry 2 -o assets.tgz https://github.com/kubernetes-sigs/controller-tools/releases/download/envtest-v1.34.0/envtest-v1.34.0-linux-amd64.tar.gz
echo '9c45e40aa56971b105e596ebb3e84af6742e8709cc0523733baf8d9bb725e69c  assets.tgz' | sha256sum -c -
tar xzf assets.tgz
cd ../..
python3 experiments/admission-contract/run.py --assets work/envtest/controller-tools/envtest --output work/admission-run-1
```

Use a fresh output directory for each run. Evidence includes binary versions and hashes, API response bodies, object persistence checks, AdmissionReviews, process logs, and cleanup status. Temporary keys and tokens stay outside the evidence directory and are removed on exit.

Expected results are baseline 201, explicit denial 429 under both Ignore and Fail, namespace controls 201, unreachable webhook 201 under Ignore and 500 under Fail. Denied or failed creates must be absent afterward.

This control plane has no kubelet or controller-manager. GitOps workload, APF tuning, timeout behavior, retry timing, recovery, and production-scale performance require separate experiments. Ephemeral loopback ports are selected before process startup, so a port collision causes startup failure.
