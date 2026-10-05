#!/usr/bin/env python

"""
server/installer/installer.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

Installs CamCOPS running under Docker with optional database.
Bootstrapped from ``installer_boot.py``. Note that the full CamCOPS Python
environment is NOT available.

"""

from argparse import ArgumentParser
from datetime import datetime
from os import chdir, rename
from os.path import dirname, exists, join, realpath
from pathlib import Path
import sys

# noinspection PyUnresolvedReferences
from python_on_whales import docker
from ucam_installkit import EXIT_USER, Installer


class DockerPath:
    """
    Directories and filenames as seen from the Docker containers.
    """

    ROOT_DIR = "/camcops"

    CONFIG_DIR = join(ROOT_DIR, "cfg")

    TMP_DIR = join(ROOT_DIR, "tmp")
    PRIVATE_FILE_STORAGE_ROOT = join(TMP_DIR, "files")

    VENV_DIR = join(ROOT_DIR, "venv")
    CAMCOPS_INSTALL_DIR = join(VENV_DIR, "lib", "python3.10", "site-packages")


class DockerComposeServices:
    """
    Subset of services named in
    ``server/docker/dockerfiles/docker-compose.yaml``.
    """

    CAMCOPS_SCHEDULER = "camcops_scheduler"
    CAMCOPS_SERVER = "camcops_server"
    CAMCOPS_WORKERS = "camcops_workers"
    MYSQL = "mysql"


class EnvVar:
    PASSWORD_SUFFIX = "PASSWORD"


# =============================================================================
# Installer base class
# =============================================================================


class CamcopsInstaller(Installer):
    def __init__(
        self,
        camcops_root_dir: str = None,
        light_mode: bool = False,
        verbose: bool = False,
        update: bool = False,
    ) -> None:
        super().__init__(
            "CamCOPS", light_mode=light_mode, verbose=verbose, update=update
        )

        camcops_root_dir = camcops_root_dir or self.get_installer_env(
            "CAMCOPS_ROOT_HOST_DIR"
        )
        if camcops_root_dir is None:
            print(
                "You must specify --camcops_root_dir or set the environment "
                "variable "
                f"{self.get_installer_envvar_prefix()}_CAMCOPS_ROOT_HOST_DIR"
            )

            sys.exit(EXIT_USER)

        self.set_installer_env("CAMCOPS_ROOT_HOST_DIR", camcops_root_dir)

    def get_compose_files(self) -> list[str | Path]:
        compose_files = ["docker-compose.yaml"]

        create_mysql_container = self.get_installer_env(
            "CREATE_MYSQL_CONTAINER"
        )

        if create_mysql_container == "1":
            compose_files.append("docker-compose-mysql.yaml")

        return compose_files

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def pre_start(self) -> None:
        self.create_superuser()

    def get_services(self) -> list[str]:
        return [
            DockerComposeServices.CAMCOPS_SCHEDULER,
            DockerComposeServices.CAMCOPS_SERVER,
            DockerComposeServices.CAMCOPS_WORKERS,
        ]

    def get_shell_service(self) -> str:
        return DockerComposeServices.CAMCOPS_SERVER

    def get_run_service(self) -> str:
        return DockerComposeServices.CAMCOPS_WORKERS

    def get_web_service(self) -> str:
        return DockerComposeServices.CAMCOPS_SERVER

    def get_exec_service(self) -> str:
        return DockerComposeServices.CAMCOPS_SERVER

    def run_dbshell_in_db_container(self) -> None:
        chdir(self.dockerfiles_host_dir())

        mysql_user = self.get_docker_env("MYSQL_USER_NAME")
        db_name = self.get_docker_env("MYSQL_DATABASE_NAME")

        command = [
            DockerPath.BASH,
            "-c",
            f"mysql -u {mysql_user} -p {db_name}",
        ]
        self.docker.compose.execute(DockerComposeServices.MYSQL, command)

    # -------------------------------------------------------------------------
    # Installation
    # -------------------------------------------------------------------------

    def configure_custom(self) -> None:
        self.configure_config_files()
        self.configure_camcops_server_ports()
        self.configure_https()
        self.configure_camcops_db()
        self.configure_superuser()
        self.configure_flower_host_port()

    def configure_config_files(self) -> None:
        config_dir = self.default_config_host_dir()

        self.set_docker_env("CONFIG_HOST_DIR", config_dir)
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        self.set_docker_env("CAMCOPS_CONFIG_FILENAME", "camcops.conf")

    def configure_camcops_server_ports(self) -> None:
        self.set_docker_env("CAMCOPS_HOST_PORT", self.get_camcops_host_port)
        self.set_docker_env(
            "CAMCOPS_INTERNAL_PORT",
            self.get_camcops_internal_port,
        )

    def configure_camcops_db(self) -> None:
        self.set_installer_env(
            "CREATE_MYSQL_CONTAINER",
            self.get_create_mysql_container,
        )

        if self.should_create_mysql_container():
            return self.configure_mysql_container()

        self.configure_external_db()

    def configure_mysql_container(self) -> None:
        self.set_docker_env(
            "MYSQL_ROOT_PASSWORD",
            self.get_mysql_root_password,
            obscure=True,
        )
        self.set_installer_env("MYSQL_SERVER", "mysql")
        self.set_installer_env("MYSQL_PORT", "3306")
        self.set_docker_env("MYSQL_DATABASE_NAME", "camcops")
        self.set_docker_env("MYSQL_USER_NAME", "camcops")
        self.set_docker_env(
            "MYSQL_USER_PASSWORD",
            self.get_mysql_user_password,
            obscure=True,
        )
        self.set_docker_env(
            "MYSQL_HOST_PORT",
            self.get_mysql_host_port,
        )

    def configure_external_db(self) -> None:
        self.info(
            "CamCOPS will attempt to connect to the external database during "
            "installation."
        )
        self.info("Before continuing:")
        self.info(
            "1. The database server must allow remote connections "
            "(e.g. bind-address = 0.0.0.0 in mysqld.cnf)."
        )
        self.info("2. The database must exist.")
        self.info(
            "3. A user must exist with access to the database using "
            "mysql_native_password authentication."
        )
        self.set_insatller_env(
            "MYSQL_SERVER",
            self.get_external_mysql_server,
        )
        self.set_installer_env(
            "MYSQL_PORT",
            self.get_external_mysql_port,
        )
        self.set_docker_env(
            "MYSQL_DATABASE_NAME",
            self.get_external_mysql_database_name,
        )
        self.set_docker_env(
            "MYSQL_USER_NAME",
            self.get_external_mysql_user_name,
        )
        self.set_docker_env(
            "MYSQL_USER_PASSWORD",
            self.get_external_mysql_user_password,
            obscure=True,
        )

    def configure_superuser(self) -> None:
        self.set_installer_env(
            "SUPERUSER_USERNAME",
            self.get_superuser_username,
        )
        self.set_installer_env(
            "SUPERUSER_PASSWORD",
            self.get_superuser_password,
            obscure=True,
        )

    def configure_flower_host_port(self) -> None:
        self.set_docker_env("FLOWER_HOST_PORT", self.get_flower_host_port)

    def create_config(self) -> None:
        config = self.config_full_path()

        if exists(config):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_filename = f"{config}.saved.{timestamp}"
            self.info(
                "Your existing config file has been renamed as "
                f"{backup_filename}"
            )
            rename(config, backup_filename)

        self.info(f"Creating {config}")
        Path(config).touch()
        self.run_command_and_output_to_file(
            ["camcops_server", "demo_camcops_config", "--docker"],
            config,
        )
        self.configure_config()

    def configure_config(self) -> None:
        ssl_certificate = ""
        ssl_private_key = ""

        if self.use_https():
            ssl_certificate = join(DockerPath.CONFIG_DIR, "camcops.crt")
            ssl_private_key = join(DockerPath.CONFIG_DIR, "camcops.key")

        replace_dict = {
            "db_server": self.get_installer_env("MYSQL_SERVER"),
            "db_port": self.get_installer_env("MYSQL_PORT"),
            "db_user": self.get_docker_env("MYSQL_USER_NAME"),
            "db_password": self.get_docker_env("MYSQL_USER_PASSWORD"),
            "db_database": self.get_docker_env("MYSQL_DATABASE_NAME"),
            "host": "0.0.0.0",
            "ssl_certificate": ssl_certificate,
            "ssl_private_key": ssl_private_key,
        }

        self.search_replace_file(self.config_full_path(), replace_dict)

    def create_or_update_databases(self) -> None:
        container_config_file = join(
            DockerPath.CONFIG_DIR,
            self.get_docker_env("CAMCOPS_CONFIG_FILENAME"),
        )

        self.run_command(
            [
                "camcops_server",
                "upgrade_db",
                "--config",
                container_config_file,
            ]
        )

    def create_superuser(self) -> None:
        # Will either create a superuser or update an existing one
        # with the given username
        username = self.get_installer_env("SUPERUSER_USERNAME")
        password = self.get_installer_env("SUPERUSER_PASSWORD")
        self.run_command(
            [
                "camcops_server",
                "make_superuser",
                "--username",
                username,
                "--password",
                password,
            ]
        )

    def report_status(self) -> None:
        localhost_url = self.get_camcops_server_localhost_url()
        self.info(f"The CamCOPS application is running at {localhost_url}")

    # -------------------------------------------------------------------------
    # Fetching information from environment variables or statically
    # -------------------------------------------------------------------------

    def config_full_path(self) -> str:
        return join(
            self.get_docker_env("CONFIG_HOST_DIR"),
            self.get_docker_env("CAMCOPS_CONFIG_FILENAME"),
        )

    def should_create_mysql_container(self) -> bool:
        return self.get_installer_env("CREATE_MYSQL_CONTAINER") == "1"

    @staticmethod
    def get_camcops_server_ip_address() -> str:
        container = docker.container.inspect("camcops_camcops_server")
        network_settings = container.network_settings

        return network_settings.networks["camcops_camcops_network"].ip_address

    def get_camcops_server_port(self) -> str:
        return self.get_docker_env("CAMCOPS_INTERNAL_PORT")

    def get_camcops_server_port_from_host(self) -> str:
        return self.get_docker_env("CAMCOPS_HOST_PORT")

    def dockerfiles_host_dir(self) -> str:
        return join(self.docker_host_dir(), "dockerfiles")

    def docker_host_dir(self) -> str:
        return join(self.src_host_dir(), "docker")

    def default_config_host_dir(self) -> str:
        return join(self.camcops_root_host_dir(), "config")

    def camcops_root_host_dir(self) -> str:
        return self.get_installer_env("CAMCOPS_ROOT_HOST_DIR")

    def installer_host_dir(self) -> str:
        return dirname(realpath(__file__))

    # -------------------------------------------------------------------------
    # Fetching information from the user
    # -------------------------------------------------------------------------

    def get_camcops_host_port(self) -> str:
        return self.get_user_input(
            ("Enter the port where CamCOPS will appear on the host:"),
            default="443",
        )

    def get_camcops_internal_port(self) -> str:
        return "8000"  # Matches PORT in camcops.conf

    def get_create_mysql_container(self) -> str:
        return self.get_user_boolean(
            "Create a MySQL container? "
            "Answer 'n' to use an external database (y/n)"
        )

    def get_mysql_root_password(self) -> str:
        return self.get_user_password(
            "Enter a new root password for the MySQL database:"
        )

    def get_mysql_user_password(self) -> str:
        username = self.get_docker_env("MYSQL_USER_NAME")
        return self.get_user_password(
            f"Enter a new password for the MySQL user ({username!r}) "
            f"that CamCOPS will create:"
        )

    def get_mysql_host_port(self) -> str:
        return self.get_user_input(
            (
                "Enter the port where the CamCOPS MySQL database will "
                "appear on the host:"
            ),
            default="43306",
        )

    def get_external_mysql_server(self) -> str:
        return self.get_user_input(
            (
                "Enter the name of the external CamCOPS database server. "
                "Use host.docker.internal for the host machine:"
            ),
            default="host.docker.internal",
        )

    def get_external_mysql_port(self) -> str:
        return self.get_user_input(
            "Enter the port number of the external CamCOPS database server:",
            default="3306",
        )

    def get_external_mysql_database_name(self) -> str:
        return self.get_user_input(
            "Enter the name of the external CamCOPS database:"
        )

    def get_external_mysql_user_name(self) -> str:
        return self.get_user_input(
            "Enter the name of the external CamCOPS database user:"
        )

    def get_external_mysql_user_password(self) -> str:
        return self.get_user_password(
            "Enter the password of the external CamCOPS database user:"
        )

    def get_superuser_username(self) -> str:
        return self.get_user_input(
            "Enter the user name for the CamCOPS administrator:",
            default="admin",
        )

    def get_superuser_password(self) -> str:
        return self.get_user_password(
            "Enter the password for the CamCOPS administrator:",
        )

    def get_flower_host_port(self) -> str:
        return self.get_user_input(
            (
                "Enter the port where the Flower event monitoring tool "
                "will appear on the host:"
            ),
            default="5555",
        )

    def get_envvar_dir(self) -> str:
        return self.get_docker_env("CONFIG_HOST_DIR", fail_if_unset=False)


# =============================================================================
# Command-line entry point
# =============================================================================


class Command:
    DBSHELL = "dbshell"
    EXEC_COMMAND = "exec"
    INSTALL = "install"
    RUN_COMMAND = "run"
    START = "start"
    STOP = "stop"
    SHELL = "shell"


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--camcops_root_dir",
        help=(
            "Top level CamCOPS directory containing config files and source "
            "code (if not running the installer locally)"
        ),
    )
    parser.add_argument(
        "--light_mode",
        action="store_true",
        default=False,
        help="Use this if your terminal has a light background",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Rebuild the CamCOPS Docker image",
    )
    subparsers = parser.add_subparsers(
        title="commands",
        description="Valid CamCOPS installer commands are:",
        help="Specify one command.",
        dest="command",
    )
    subparsers.required = True

    subparsers.add_parser(
        Command.INSTALL,
        help="Install CamCOPS into a Docker Compose environment",
    )

    subparsers.add_parser(
        Command.START, help="Start the Docker Compose application"
    )

    subparsers.add_parser(
        Command.STOP, help="Stop the Docker Compose application"
    )

    run_camcops_command = subparsers.add_parser(
        Command.RUN_COMMAND,
        help=f"Run a command within the CamCOPS Docker environment, in the "
        f"{DockerComposeServices.CAMCOPS_WORKERS!r} service/container",
    )
    run_camcops_command.add_argument("camcops_command", type=str)

    exec_camcops_command = subparsers.add_parser(
        Command.EXEC_COMMAND,
        help=f"Execute a command within the CamCOPS Docker environment, in "
        f"the existing {DockerComposeServices.CAMCOPS_SERVER!r} "
        "service/container (with a terminal, so output is visible).",
    )
    exec_camcops_command.add_argument("camcops_command", type=str)
    exec_camcops_command.add_argument(
        "--as_root",
        action="store_true",
        help="Enter as the 'root' user instead of the 'camcops' user",
        default=False,
    )

    shell = subparsers.add_parser(
        Command.SHELL,
        help="Start a shell (command prompt) within an already-running "
        "CamCOPS Docker environment, in the "
        f"{DockerComposeServices.CAMCOPS_SERVER!r} container",
    )
    shell.add_argument(
        "--as_root",
        action="store_true",
        help="Enter as the 'root' user instead of the 'camcops' user",
        default=False,
    )

    subparsers.add_parser(
        Command.DBSHELL,
        help=(
            "Start a MySQL command-line client within an already-running "
            "CamCOPS Docker environment, in the "
            f"{DockerComposeServices.MYSQL!r} container"
        ),
    )

    args = parser.parse_args()

    installer = CamcopsInstaller(
        camcops_root_dir=args.camcops_root_dir,
        light_mode=args.light_mode,
        update=args.update,
        verbose=args.verbose,
    )

    if args.command == Command.INSTALL:
        installer.install()

    elif args.command == Command.START:
        installer.start()

    elif args.command == Command.STOP:
        installer.stop()

    elif args.command == Command.RUN_COMMAND:
        installer.run_camcops_command(args.camcops_command)

    elif args.command == Command.EXEC_COMMAND:
        installer.exec_camcops_command(
            args.camcops_command, as_root=args.as_root
        )

    elif args.command == Command.SHELL:
        installer.run_shell_in_camcops_container(as_root=args.as_root)

    elif args.command == Command.DBSHELL:
        installer.run_dbshell_in_db_container()

    else:
        raise AssertionError("Bug")


if __name__ == "__main__":
    main()
