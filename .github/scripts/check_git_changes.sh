#!/usr/bin/env bash

# Check if there are changes within version control from the current directory

set -euo pipefail

git diff
git update-index --refresh
git diff-index --quiet HEAD --
test -z "$(git ls-files --exclude-standard --others)"
