@echo off
REM server/docker/windows/upgrade_db.bat
REM
REM Launches the "camcops_server" command within one of the Docker containers
REM running the CamCOPS server image.

set THIS_DIR=%~dp0
set CAMCOPS_SERVER=%THIS_DIR%\camcops_server.bat

if "%CAMCOPS_DOCKER_CONFIG_HOST_DIR%" == "" (
    echo "Must set CAMCOPS_DOCKER_CONFIG_HOST_DIR environment variable!"
    exit /b 1
)
if "%CAMCOPS_DOCKER_CONFIG_FILENAME%" == "" (
    REM Set to default (as per .env file):
    set CAMCOPS_DOCKER_CONFIG_FILENAME="camcops.conf"
fi

set CFG_ON_HOST="%CAMCOPS_DOCKER_CONFIG_HOST_DIR%\%CAMCOPS_DOCKER_CONFIG_FILENAME%"
set CFG_ON_DOCKER="/camcops/cfg/%CAMCOPS_DOCKER_CONFIG_FILENAME%"

echo "Upgrading CamCOPS database to current version."
echo "- Config file on host: %CFG_ON_HOST%"
echo "- Config file as seen by Docker: %CFG_ON_DOCKER%"

"%CAMCOPS_SERVER%" upgrade_db --config "${CFG_ON_DOCKER}"
