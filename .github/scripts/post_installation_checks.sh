#!/usr/bin/env bash

# Run from .github/workflows/installer.yml
# Check various things after running the installer

set -euxo pipefail

# Check server is running
cd "${CAMCOPS_HOME}/docker/dockerfiles"
docker compose logs
SERVER_IP=$(docker inspect camcops_camcops_server --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
wait-for-it "${SERVER_IP}:8000" --timeout=300
curl -I -L --retry 10 --fail "${SERVER_IP}:8000/camcops/"
