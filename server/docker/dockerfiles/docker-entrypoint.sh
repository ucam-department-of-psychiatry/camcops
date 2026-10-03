#!/bin/bash

set -e

# If we need to wait for any containers to start up, do that here.
# See CRATE.

. /camcops/venv/bin/activate
exec "$@"
