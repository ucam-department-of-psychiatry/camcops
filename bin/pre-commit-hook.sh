#!/bin/bash

# pre-commit hook script that runs lint & sort
#
# Usage: ln -s ./bin/pre-commit-hook.sh .git/hooks/pre-commit
#
# This does not run tests, as it would be slow to do at every commit.
# Linting and sorting however ensures we don't get cosmetic commits later
# that break git blame history for no reason.
#
# This script doesn't stash changes to avoid unexpected side effects.
# So if you have non-commited changes that break this you'll need to
# stash your changes before commiting.

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

make lint && make sort
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo -e "${RED}lint/sort failed; commit aborted. See errors above.${NC}\n"
  exit 1
fi
echo -e "${GREEN}lint/sort success.${NC}\n"
exit 0
