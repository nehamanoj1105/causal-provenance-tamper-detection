#!/usr/bin/env bash
# Downloads DARPA Transparent Computing E3 Theia data into data/raw/
#
# The TC dataset is distributed via a public GitHub repo (manifest + links to
# hosted files, not the raw data itself in-repo). This script clones the
# manifest repo; you'll still need to follow the linked download instructions
# in README-E3.md for the actual data files, since DARPA hosts those
# separately (not on GitHub directly).

set -euo pipefail

DATA_DIR="$(dirname "$0")/../data/raw"
mkdir -p "$DATA_DIR"

echo "Cloning DARPA Transparent-Computing manifest repo..."
git clone --depth 1 https://github.com/darpa-i2o/Transparent-Computing.git "$DATA_DIR/manifest"

echo ""
echo "Manifest cloned to $DATA_DIR/manifest"
echo "Next: open $DATA_DIR/manifest/README-E3.md and follow the E3 Theia"
echo "download instructions to pull the actual dataset files."
