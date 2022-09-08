#!/usr/bin/env bash

# Run from .github/workflows/docker.yml
# Build the CamCOPS Docker image

set -euxo pipefail

cd server/docker/dockerfiles
docker compose version
docker compose -f docker-compose.yaml -f docker-compose-mysql.yaml build
