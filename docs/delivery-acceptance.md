# Delivery acceptance

Updated November 27, 2026.

JANUS currently ships a working local control-plane experiment toolkit. The deployed control plane in those experiments is upstream Kubernetes and etcd. The repository's Go admission handler is a synthetic fixture. A JANUS production intervention remains to be implemented and validated.

## Executable evidence

The manual Integration evidence workflow prepares checksum-pinned assets, starts a real disposable API server, checks admission responses and persistence, compares default and tuned Flux reconciliation, and verifies interruption teardown. Its timeout is 12 minutes and artifacts are retained for seven days. Default CI checks Go race tests, Python syntax, phase-accounting tests, shell syntax and required research artifacts.

Historical measurements, runtime pins, failed attempts and verification limits are recorded in findings 0005–0008. Existing measurements establish a native tuning tradeoff. They do not establish incremental benefit from a new controller.

## Working intervention acceptance

The next component must have an explicit entry point and deployment model, a documented authority boundary, versioned configuration, observable decisions and a reversible effect on the intended controller or APF configuration. Its acceptance must exercise the normal deployment and recovery path.

| Boundary | Acceptance evidence still needed |
| --- | --- |
| Attributable problem | Fault-only control, fault with GitOps defaults and identical fault with tuned native controls, including sustained timeout/retry cycles |
| Recovery access | A separate non-exempt recovery-critical client, measured success and latency under each treatment |
| Desired-state correctness | Exact object and ownership checks after recovery, including concurrent user edits and controller restarts |
| Mechanism selection | Measured benefit beyond native tuning, with recovery delay and operational burden included |
| Failure behavior | Freshness validation, missing telemetry, restart, partial update, conflict, rollback and termination cases |
| Authority | Minimum required permissions, identity classification and explicit target selection |
| Compatibility | Tested version matrix and documented limits of each input/control API |
| Operator validation | Current firsthand incident evidence and an independently owned nonproduction evaluation |

These rows define evidence to collect for the intended intervention. They do not certify the existing experiment fixture for production deployment. Acceptance thresholds for production benefit must be agreed with the evaluating operator before measurements are collected.

## Foundation readiness

The CNCF entry route is its Sandbox application process. Prepare the application against the current official form, describing the implemented software, maintainers, governance, cloud-native fit, license, alternatives, users and remaining work accurately. Foundation acceptance requires its own review and agreements. No application or acceptance has been recorded for JANUS.

Official references checked November 27, 2026.

* [CNCF project submission](https://contribute.cncf.io/projects/submit-project/)
* [CNCF Sandbox application form](https://github.com/cncf/sandbox/blob/main/.github/ISSUE_TEMPLATE/application.yml)
* [Linux Foundation project hosting](https://www.linuxfoundation.org/projects/hosting)
