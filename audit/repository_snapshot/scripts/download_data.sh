#!/usr/bin/env bash
# Pulls the DARPA Transparent Computing manifest (schema + tools + ground
# truth + README-E3.md) into data/raw/manifest/.
#
# This does NOT download the actual .bin event data. That's hosted
# separately by Five Directions Inc. on Google Drive, not in this git repo.
# After running this script, open data/raw/manifest/README-E3.md, follow the
# Google Drive link there, and manually pull the Theia .bin files into
# data/raw/theia/. See data/README.md for which files to grab.

set -euo pipefail

DATA_DIR="$(dirname "$0")/../data/raw"
mkdir -p "$DATA_DIR"

echo "Cloning DARPA Transparent-Computing manifest repo..."
git clone --depth 1 https://github.com/darpa-i2o/Transparent-Computing.git "$DATA_DIR/manifest"

echo ""
echo "Manifest cloned to $DATA_DIR/manifest"
echo "Next: open $DATA_DIR/manifest/README-E3.md and follow the E3 Theia"
echo "download instructions to pull the actual dataset files."
