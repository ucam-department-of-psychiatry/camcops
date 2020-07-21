@echo off
REM server/docker/windows/bash_within_camcops_docker.bat
REM
REM Launches the "camcops_server" command within one of the Docker containers
REM running the CamCOPS server image.

setlocal

set THIS_DIR=%~dp0
set WITHIN_DOCKER=%THIS_DIR%\within_docker.bat

"%WITHIN_DOCKER%" /bin/bash
