#!/usr/bin/env bash
# Installs HTTrack when a package-manager build is unavailable.
# This sandbox used an upstream source build at tag 3.51.0 with the coucal submodule,
# a Linux config.h, local zlib headers and a direct gcc link. The resulting binary is
# available as `httrack` in ~/.local/bin and /usr/local/bin.
set -euo pipefail
if command -v httrack >/dev/null 2>&1; then
  httrack --version
  exit 0
fi
echo "HTTrack is not installed. On a normal Linux host:"
echo "  sudo apt-get install httrack"
echo "On macOS:"
echo "  brew install httrack"
echo "For this sandbox, build the upstream 3.51.0 source with the generated Linux config headers."
exit 1
