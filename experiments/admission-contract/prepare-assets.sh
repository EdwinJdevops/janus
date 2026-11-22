#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
  echo 'Usage: prepare-assets.sh OUTPUT_DIRECTORY' >&2
  exit 2
fi
mkdir -p -- "$1"
destination=$(cd -- "$1" && pwd)
mkdir -p "$destination/envtest" "$destination/flux"

archive="$destination/envtest/assets.tgz"
curl -fL --retry 2 -o "$archive" \
  https://github.com/kubernetes-sigs/controller-tools/releases/download/envtest-v1.37.0/envtest-v1.37.0-linux-amd64.tar.gz
echo "f03faedfc68d2a78cee5cb02618bb44e7f67044f4c5fc957f72d3307fda61a9c  $archive" | sha256sum -c -
tar xzf "$archive" -C "$destination/envtest"

source_revision=701d9a9d24763b668d6ef0634cc5f88f5bfbb861
for resource in buckets externalartifacts gitrepositories ocirepositories; do
  curl -fL --retry 2 -o "$destination/flux/$resource.yaml" \
    "https://raw.githubusercontent.com/fluxcd/source-controller/$source_revision/config/crd/bases/source.toolkit.fluxcd.io_$resource.yaml"
done
curl -fL --retry 2 -o "$destination/flux/kustomizations.yaml" \
  https://raw.githubusercontent.com/fluxcd/kustomize-controller/746d9d2d360bbc7a5ee75ab79dadcf05e48ab927/config/crd/bases/kustomize.toolkit.fluxcd.io_kustomizations.yaml

image=ghcr.io/fluxcd/kustomize-controller@sha256:37db29b25dae35b881a5e064acedb0cc954442da453a39eaa0eab7a90dbecc4e
docker pull --platform linux/amd64 "$image"
container_id=$(docker create --platform linux/amd64 "$image")
cleanup() {
  docker rm "$container_id" >/dev/null
}
trap cleanup EXIT
docker cp "$container_id":/usr/local/bin/kustomize-controller "$destination/flux/kustomize-controller"

cd "$destination/flux"
sha256sum -c <<'CHECKSUMS'
86c81cb80ed002322f27a4a4042422fc04d58b418863711d09ccf85e7faf304e  buckets.yaml
f78536e2c0c6719221adff02da257bf3d2dc20dcd9636ce304656fa3f320c102  externalartifacts.yaml
ae4d504172dd9504b38d4e770842fcc086168e83707308dd56cba708f3c1daa0  gitrepositories.yaml
dec77e391bff9307e47898d2d7448c5083a49b85700f6f870c7849449e11aad0  kustomizations.yaml
dcb7198a1c747ad96b8ca5218d2780896800306098497159fa77ecd7aba9a886  ocirepositories.yaml
8065052997318646e734597f5c760b436480ff2f5611e1aaeecd7bb4f5769dba  kustomize-controller
CHECKSUMS
