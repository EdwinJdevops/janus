# Security and provenance verification — 2026-11-24

The plugin-backed Standard source scan completed on the experimental toolkit snapshot `codex-security-snapshot/v1:sha256:f5d192741f463b3ced2895deca9989f1546d95a6044c0657c1e18da123de8a4d`. Scan ID `d70c787e-6f61-46bb-a73d-bc479622d8aa` reported zero exploitable findings. An independent offline baseline reviewer examined all executable source, tests, shell scripts and CI configuration. Large evidence JSON and remaining prose received targeted inspection. External binaries and upstream dependencies were outside this source review.

The review identified robustness follow-up and an unresolved boundary involving local unauthenticated etcd, the external controller and ambient host authority. It established no exploit through that boundary. The local fixture remains suitable for a trusted experimental host. Production threat surfaces and hostile multi-user isolation need additional assessment.

After sealing the scan, fault setup was hardened to hold the resume lock while starting the watchdog and delivering SIGSTOP. This prevents a delayed setup thread from pausing the backend after the watchdog already attempted to resume it. The change is a robustness correction. It is subsequent to the scanned snapshot and received separate source review and integration checks.

## Verified image signature

Cosign v3.1.4, executable SHA256 `424e2c97d0b45fd7a6b608a87f090f35633f4c23ece5f092d48bba11aaf4bbfa`, successfully verified the image digest `sha256:37db29b25dae35b881a5e064acedb0cc954442da453a39eaa0eab7a90dbecc4e` from `ghcr.io/fluxcd/kustomize-controller`.

The expected certificate identity was `https://github.com/fluxcd/gha-workflows/.github/workflows/controller-release.yaml@refs/tags/v0.17.0`, with issuer `https://token.actions.githubusercontent.com`. The pinned controller release configuration references that reusable workflow. Cosign validated claims, transparency-log evidence and the certificate chain. [Pinned release configuration](https://github.com/fluxcd/kustomize-controller/blob/746d9d2d360bbc7a5ee75ab79dadcf05e48ab927/.github/workflows/release.yaml)

An earlier attempt expected the old SLSA container-generator identity and failed. A subsequent attempt found a signed image-signature statement with predicate `https://sigstore.dev/cosign/sign/v1`, which is distinct from SLSA provenance. Container-image SLSA provenance remains unresolved.

## Verified source-release provenance

The published `provenance.intoto.jsonl` bundle had SHA256 `96cbb27efc791507a25f01026217cd68d10dd6a32ea03ceb89a7dd52ec19ded7`. Cosign verified its SLSA v0.2 statement for source archive digest `d6457a339291e0620fa334ee27239ce461ec38c215e87d4f879d4cad16ac57e2`, repository `fluxcd/kustomize-controller`, tag `v1.10.1`, source commit `746d9d2d360bbc7a5ee75ab79dadcf05e48ab927`, issuer GitHub Actions and generic SLSA generator identity at `v2.1.0`. This verifies the named source-archive attestation, with digest supplied directly to the verifier. It does not establish reproducible image builds or vulnerability freedom.

The original GitHub CLI image-attestation query returned HTTP 404. Correct Cosign verification subsequently established the image signature and the separate source-release attestation. A local pre-existing Cosign executable had a different checksum from the intended asset and was replaced with a checksum-verified release download before these verification commands.

## Reproduction

Run `cosign verify` with the pinned image digest, exact reusable-workflow identity and GitHub Actions issuer above. For source provenance, use `cosign verify-blob-attestation --bundle provenance.intoto.jsonl --type slsaprovenance --digest <source-digest> --digestAlg sha256`, the exact generic generator certificate identity, and expected repository/ref/SHA certificate claims. Retain verification output and distinguish each artifact's scope.

The checked-in evidence directory contains the verified image statement and verifier logs. The complete sealed security report and provenance bundle are retained with the local output artifacts. Operator contacts, incident evidence and independent nonproduction evaluations remain pending.
