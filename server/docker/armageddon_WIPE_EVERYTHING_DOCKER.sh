#!/bin/bash
#
# server/docker/armageddon_WIPE_EVERYTHING_DOCKER.sh
# https://stackoverflow.com/questions/34658836/docker-is-in-volume-in-use-but-there-arent-any-docker-containers

# set -e

removecontainers() {
    echo "- Stopping all Docker containers..."
    docker stop $(docker ps -aq)
    echo "- Deleting all Docker containers..."
    docker rm $(docker ps -aq)
}

armageddon() {
    removecontainers
    echo "- Pruning all networks..."
    docker network prune -f
    echo "- Deleting all images..."
    docker rmi -f $(docker images --filter dangling=true -qa)
    echo "- Deleting all volumes..."
    docker volume rm $(docker volume ls --filter dangling=true -q)
    echo "- Deleting all images (again)..."
    docker rmi -f $(docker images -qa)
}

read -p "Wipe entire Docker setup. EVERY Docker setup on this computer will be wiped. Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # do dangerous stuff
    armageddon
fi
