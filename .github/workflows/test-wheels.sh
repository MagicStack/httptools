#!/bin/bash

set -Eexuo pipefail
shopt -s nullglob

pip install -f "file:///${GITHUB_WORKSPACE}/dist" "httptools[test]==${PKG_VERSION}"
make -C "${GITHUB_WORKSPACE}" testinstalled
