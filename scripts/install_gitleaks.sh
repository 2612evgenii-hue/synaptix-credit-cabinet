#!/bin/sh
# CI-only installer. Fixed upstream release and verified archive; no action license.
set -eu
if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
  echo 'This installer is for Linux x64 CI. Install Gitleaks for your OS separately.' >&2
  exit 1
fi
target="${1:?usage: install_gitleaks.sh TARGET_DIRECTORY}"
mkdir -p "$target"
target="$(cd "$target" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
  https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
  --output "$scratch/gitleaks.tar.gz"
echo '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  gitleaks.tar.gz' > "$scratch/checksum"
(cd "$scratch" && sha256sum --check checksum)
tar -xzf "$scratch/gitleaks.tar.gz" -C "$target" gitleaks
"$target/gitleaks" version
