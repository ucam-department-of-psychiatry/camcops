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

Installs CamCOPS running under Docker with demonstration databases.
Bootstrapped from ``installer.sh``. Note that the full CamCOPS Python
environment is NOT available.

"""

from argparse import ArgumentParser
import os
from pathlib import Path
from platform import uname
import re
import secrets
import shutil
import string
from subprocess import run
import sys
from tempfile import NamedTemporaryFile
import textwrap
from typing import Callable, Dict, Iterable, NoReturn, TextIO, Union
import urllib.parse

# See installer-requirements.txt
from prompt_toolkit import HTML, print_formatted_text, prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

# noinspection PyUnresolvedReferences
from python_on_whales import docker, DockerException
from semantic_version import Version


# =============================================================================
# Constants
# =============================================================================

EXIT_FAILURE = 1


class HostPath:
    """
    Directories and filenames as seen from the host OS.
    """

    INSTALLER_DIR = os.path.dirname(os.path.realpath(__file__))
    PROJECT_ROOT = os.path.join(INSTALLER_DIR, "..")
    DOCKER_DIR = os.path.join(PROJECT_ROOT, "docker")
    DOCKERFILES_DIR = os.path.join(DOCKER_DIR, "dockerfiles")

    HOME_DIR = os.path.expanduser("~")
    DEFAULT_HOST_CAMCOPS_CONFIG_DIR = os.path.join(HOME_DIR, "camcops_config")

    ENVVAR_SAVE_FILE = "set_camcops_docker_host_envvars"


class DockerPath:
    """
    Directories and filenames as seen from the Docker containers.
    """

    BASH = "/bin/bash"

    ROOT_DIR = "/camcops"

    CONFIG_DIR = os.path.join(ROOT_DIR, "cfg")

    TMP_DIR = os.path.join(ROOT_DIR, "tmp")
    PRIVATE_FILE_STORAGE_ROOT = os.path.join(TMP_DIR, "files")

    VENV_DIR = os.path.join(ROOT_DIR, "venv")
    CAMCOPS_INSTALL_DIR = os.path.join(
        VENV_DIR, "lib", "python3.8", "site-packages"
    )


class DockerComposeServices:
    """
    Subset of services named in
    ``server/docker/dockerfiles/docker-compose.yaml``.
    """

    CAMCOPS_SERVER = "camcops_server"
    CAMCOPS_WORKERS = "camcops_workers"


class DockerEnvVar:
    """
    Environment variables governing the Docker setup.
    """

    PREFIX = "CAMCOPS_DOCKER"
    PASSWORD_SUFFIX = "PASSWORD"

    CONFIG_HOST_DIR = f"{PREFIX}_CONFIG_HOST_DIR"
    CAMCOPS_CONFIG_FILENAME = f"{PREFIX}_CAMCOPS_CONFIG_FILENAME"
    CAMCOPS_HOST_PORT = f"{PREFIX}_CAMCOPS_HOST_PORT"
    CAMCOPS_SSL_CERTIFICATE = f"{PREFIX}_CAMCOPS_SSL_CERTIFICATE"
    CAMCOPS_SSL_PRIVATE_KEY = f"{PREFIX}_CAMCOPS_SSL_PRIVATE_KEY"
    CAMCOPS_SUPERUSER_USERNAME = f"{PREFIX}_CAMCOPS_SUPERUSER_USERNAME"
    CAMCOPS_USE_HTTPS = f"{PREFIX}_CAMCOPS_USE_HTTPS"

    INSTALL_USER_ID = f"{PREFIX}_INSTALL_USER_ID"

    MYSQL_CAMCOPS_DATABASE_NAME = f"{PREFIX}_MYSQL_CAMCOPS_DATABASE_NAME"
    MYSQL_HOST_PORT = f"{PREFIX}_MYSQL_HOST_PORT"
    MYSQL_ROOT_PASSWORD = f"{PREFIX}_MYSQL_ROOT_{PASSWORD_SUFFIX}"
    MYSQL_CAMCOPS_USER_NAME = f"{PREFIX}_MYSQL_CAMCOPS_USER_NAME"
    MYSQL_CAMCOPS_USER_PASSWORD = (
        f"{PREFIX}_MYSQL_CAMCOPS_USER_{PASSWORD_SUFFIX}"
    )


# =============================================================================
# Validators
# =============================================================================


class NotEmptyValidator(Validator):
    def validate(self, document: Document) -> None:
        if not document.text:
            raise ValidationError(message="Must provide an answer")


class YesNoValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text

        if text.lower() not in ("y", "n"):
            raise ValidationError(message="Please answer 'y' or 'n'")


class FileValidator(Validator):
    def validate(self, document: Document) -> None:
        filename = document.text

        if not os.path.isfile(os.path.expanduser(filename)):
            raise ValidationError(message=f"{filename!r} is not a valid file")


class PasswordMatchValidator(Validator):
    def __init__(self, first_password: str) -> None:
        self.first_password = first_password

    def validate(self, document: Document) -> None:
        password = document.text

        if password != self.first_password:
            raise ValidationError(message="Passwords do not match")


class EmailValidator(Validator):
    _SIMPLE_EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    def validate(self, document: Document) -> None:
        email = document.text
        if self._SIMPLE_EMAIL_REGEX.match(email) is None:
            raise ValidationError(message=f"{email!r} is not a valid e-mail")


# =============================================================================
# Installer base class
# =============================================================================


class Installer:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.title = "CamCOPS Setup"
        self.intro_style = Style.from_dict(
            {
                "span": "#ffffff bg:#0000b8",
            }
        )
        self.prompt_style = Style.from_dict(
            {
                "span": "#ffffff bg:#005eb8",
            }
        )
        self.info_style = Style.from_dict(
            {
                "span": "#00cc00 bg:#000000",
            }
        )
        self.error_style = Style.from_dict(
            {
                "span": "#ffffff bg:#b80000",
            }
        )
        self.envvar_style = Style.from_dict(
            {
                "span": "#008800 bg:#000000",
            }
        )

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def install(self) -> None:
        self.start_message()
        self.check_setup()
        self.configure()
        self.create_directories()
        self.write_environment_variables()
        self.create_config()
        if self.use_https():
            self.copy_ssl_files()
        self.create_database()
        self.create_superuser()
        self.start()
        self.report_status()

    @staticmethod
    def start() -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        docker.compose.up(detach=True)

    @staticmethod
    def stop() -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        docker.compose.down()

    @staticmethod
    def run_shell_in_camcops_container(as_root: bool = False) -> None:
        # python_on_whales doesn't support docker compose exec yet
        os.chdir(HostPath.DOCKERFILES_DIR)

        command = ["docker", "compose", "exec"]
        user_option = ["-u", "0"] if as_root else []

        run(
            command
            + user_option
            + [DockerComposeServices.CAMCOPS_SERVER, DockerPath.BASH]
        )

    def run_camcops_command(self, camcops_command: str) -> None:
        self.run_bash_command_inside_docker(
            f"source /camcops/venv/bin/activate; {camcops_command}"
        )

    # -------------------------------------------------------------------------
    # Info messages
    # -------------------------------------------------------------------------

    @staticmethod
    def report(text: str, style: Style) -> None:
        print_formatted_text(HTML(f"<span>{text}</span>"), style=style)

    def start_message(self) -> None:
        self.report("CamCOPS Installer", self.intro_style)

    def info(self, text: str) -> None:
        self.report(text, self.info_style)

    def envvar_info(self, text: str) -> None:
        if not self.verbose:
            return
        self.report(text, self.envvar_style)

    def error(self, text: str) -> None:
        self.report(text, self.error_style)

    def fail(self, text: str) -> NoReturn:
        self.error(text)
        sys.exit(EXIT_FAILURE)

    # -------------------------------------------------------------------------
    # Installation
    # -------------------------------------------------------------------------

    def check_setup(self) -> None:
        info = docker.info()
        if info.id is None:
            self.fail(
                "Could not connect to Docker. Check that Docker is "
                "running and your user is in the 'docker' group."
            )

        try:
            # python_on_whales doesn't support --short or --format so we do
            # some parsing
            version_string = docker.compose.version().split()[-1].lstrip("v")
        except DockerException:
            self.fail(
                "It looks like you don't have Docker Compose installed. "
                "Please install Docker Compose v2 or greater. See "
                "https://github.com/docker/compose; "
                "https://docs.docker.com/compose/cli-command/"
            )

        version = Version(version_string)
        if version.major < 2:
            self.fail(
                f"The version of Docker Compose ({version}) is too old. "
                "Please install v2 or greater."
            )

    def configure(self) -> None:
        try:
            self.configure_user()
            self.configure_config_files()
            self.configure_camcops_db()
            self.configure_superuser()
        except (KeyboardInterrupt, EOFError):
            # The user pressed CTRL-C or CTRL-D
            self.error("Installation aborted")
            self.write_environment_variables()
            sys.exit(EXIT_FAILURE)

    def configure_user(self) -> None:
        self.setenv(
            DockerEnvVar.INSTALL_USER_ID, self.get_docker_install_user_id
        )

    def configure_config_files(self) -> None:
        self.setenv(
            DockerEnvVar.CONFIG_HOST_DIR, self.get_docker_config_host_dir
        )
        self.setenv(DockerEnvVar.CAMCOPS_CONFIG_FILENAME, "camcops.conf")

    def configure_camcops(self) -> None:
        self.setenv(
            DockerEnvVar.CAMCOPS_HOST_PORT, self.get_docker_camcops_host_port
        )
        self.setenv(
            DockerEnvVar.CAMCOPS_USE_HTTPS, self.get_docker_camcops_use_https
        )
        if self.use_https():
            self.setenv(
                DockerEnvVar.CAMCOPS_SSL_CERTIFICATE,
                self.get_docker_camcops_ssl_certificate,
            )
            self.setenv(
                DockerEnvVar.CAMCOPS_SSL_PRIVATE_KEY,
                self.get_docker_camcops_ssl_private_key,
            )

    def configure_camcops_db(self) -> None:
        self.setenv(
            DockerEnvVar.MYSQL_ROOT_PASSWORD,
            self.get_docker_mysql_root_password,
            obscure=True,
        )
        self.setenv(DockerEnvVar.MYSQL_CAMCOPS_DATABASE_NAME, "camcops")
        self.setenv(DockerEnvVar.MYSQL_CAMCOPS_USER_NAME, "camcops")
        self.setenv(
            DockerEnvVar.MYSQL_CAMCOPS_USER_PASSWORD,
            self.get_docker_mysql_camcops_user_password,
            obscure=True,
        )
        self.setenv(
            DockerEnvVar.MYSQL_HOST_PORT,
            self.get_docker_mysql_camcops_host_port,
        )

    def configure_superuser(self) -> None:
        self.setenv(
            DockerEnvVar.CAMCOPS_SUPERUSER_USERNAME,
            self.get_docker_camcops_superuser_username,
        )

    @staticmethod
    def create_directories() -> None:
        camcops_config_dir = os.environ.get(DockerEnvVar.CONFIG_HOST_DIR)
        Path(camcops_config_dir).mkdir(parents=True, exist_ok=True)

    def create_config(self) -> None:
        config = self.config_full_path()
        if not os.path.exists(config):
            self.info(f"Creating {config}")
            Path(config).touch()
            self.run_camcops_command("env")
            self.run_camcops_command(
                "camcops_server demo_camcops_config --docker > "
                "$CAMCOPS_CONFIG_FILE"
            )
        self.configure_config()

    def configure_config(self) -> None:
        replace_dict = {
            "db_password": os.getenv(
                DockerEnvVar.MYSQL_CAMCOPS_USER_PASSWORD,
            ),
        }

        self.search_replace_file(self.config_full_path(), replace_dict)

    @staticmethod
    def copy_ssl_files() -> None:
        config_dir = os.getenv(DockerEnvVar.CONFIG_HOST_DIR)

        cert_dest = os.path.join(config_dir, "camcops.crt")
        key_dest = os.path.join(config_dir, "camcops.key")

        shutil.copy(os.getenv(DockerEnvVar.CAMCOPS_SSL_CERTIFICATE), cert_dest)
        shutil.copy(os.getenv(DockerEnvVar.CAMCOPS_SSL_PRIVATE_KEY), key_dest)

    def create_database(self) -> None:
        self.run_camcops_command(
            "camcops_server upgrade_db --config $CAMCOPS_CONFIG_FILE"
        )

    def create_superuser(self) -> None:
        # Will either create a superuser or update an existing one
        # with the given username
        username = os.getenv(DockerEnvVar.CAMCOPS_SUPERUSER_USERNAME)
        self.run_camcops_command(
            f"camcops_server makesuperuser --username {username}"
        )

    def report_status(self) -> None:
        localhost_url = self.get_camcops_server_localhost_url()
        self.info(f"The CamCOPS application is running at {localhost_url}")

    # -------------------------------------------------------------------------
    # Fetching information from environment variables or statically
    # -------------------------------------------------------------------------

    @staticmethod
    def get_docker_install_user_id() -> str:
        return str(os.geteuid())

    @staticmethod
    def get_hmac_md5_key() -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(16))

    @staticmethod
    def config_full_path() -> str:
        return os.path.join(
            os.getenv(DockerEnvVar.CONFIG_HOST_DIR),
            os.getenv(DockerEnvVar.CAMCOPS_CONFIG_FILENAME),
        )

    def get_camcops_server_localhost_url(self) -> str:
        scheme = self.get_camcops_server_scheme()
        port = self.get_camcops_server_port_from_host()
        netloc = f"localhost:{port}"
        path = self.get_camcops_server_path()
        params = query = fragment = None
        return urllib.parse.urlunparse(
            (scheme, netloc, path, params, query, fragment)
        )

    def get_camcops_server_scheme(self) -> str:
        if self.use_https():
            return "https"
        return "http"

    @staticmethod
    def use_https() -> bool:
        return os.getenv(DockerEnvVar.CAMCOPS_USE_HTTPS) == "1"

    @staticmethod
    def get_camcops_server_path() -> str:
        return "/"

    @staticmethod
    def get_camcops_server_ip_address() -> str:
        container = docker.container.inspect("camcops_camcops_server")
        network_settings = container.network_settings

        return network_settings.networks[
            "camcops_camcopsanon_network"
        ].ip_address

    @staticmethod
    def get_camcops_server_port_from_host() -> str:
        return os.getenv(DockerEnvVar.CAMCOPS_HOST_PORT)

    # -------------------------------------------------------------------------
    # Fetching information from the user
    # -------------------------------------------------------------------------

    def get_docker_config_host_dir(self) -> str:
        return self.get_user_dir(
            "Select the host directory where CamCOPS will store its "
            "configuration:",
            default=HostPath.DEFAULT_HOST_CAMCOPS_CONFIG_DIR,
        )

    def get_docker_camcops_host_port(self) -> str:
        return self.get_user_input(
            ("Enter the port where CamCOPS will appear on the host:"),
            default="8000",
        )

    def get_docker_camcops_use_https(self) -> str:
        return self.get_user_boolean("Access CamCOPS over HTTPS (y/n)?")

    def get_docker_camcops_ssl_certificate(self) -> str:
        return self.get_user_file("Select the SSL certificate file:")

    def get_docker_camcops_ssl_private_key(self) -> str:
        return self.get_user_file("Select the SSL private key file:")

    def get_docker_mysql_root_password(self) -> str:
        return self.get_user_password(
            "Enter a new root password for the MySQL database:"
        )

    def get_docker_mysql_camcops_user_password(self) -> str:
        username = os.environ[DockerEnvVar.MYSQL_CAMCOPS_USER_NAME]
        return self.get_user_password(
            f"Enter a new password for the MySQL user ({username!r}) "
            f"that CamCOPS will create:"
        )

    def get_docker_mysql_camcops_host_port(self) -> str:
        return self.get_user_input(
            (
                "Enter the port where the CamCOPS MySQL database will "
                "appear on the host:"
            ),
            default="43306",
        )

    def get_docker_camcops_superuser_username(self) -> str:
        return self.get_user_input(
            "Enter the user name for the CamCOPS administrator:",
            default="admin",
        )

    # -------------------------------------------------------------------------
    # Generic input
    # -------------------------------------------------------------------------

    def get_user_dir(self, text: str, default: str = "") -> str:
        completer = PathCompleter(only_directories=True, expanduser=True)
        directory = self.prompt(text, completer=completer, default=default)

        return os.path.expanduser(directory)

    def get_user_file(self, text: str) -> str:
        completer = PathCompleter(only_directories=False, expanduser=True)
        file = self.prompt(
            text,
            completer=completer,
            complete_while_typing=True,
            validator=FileValidator(),
        )

        return os.path.expanduser(file)

    def get_user_password(self, text: str) -> str:
        first = self.prompt(
            text, is_password=True, validator=NotEmptyValidator()
        )
        self.prompt(
            "Enter the same password again:",
            is_password=True,
            validator=PasswordMatchValidator(first),
        )
        return first

    def get_user_boolean(self, text: str) -> str:
        value = self.prompt(text, validator=YesNoValidator())
        if value.lower() == "y":
            return "1"
        return "0"

    def get_user_email(self, text: str) -> str:
        return self.prompt(text, validator=EmailValidator())

    def get_user_input(self, text: str, default: str = "") -> str:
        return self.prompt(
            text, default=default, validator=NotEmptyValidator()
        )

    def prompt(self, text: str, *args, **kwargs) -> str:
        """
        Shows a prompt and returns user input.
        """
        return prompt(
            HTML(f"\n<span>{text}</span> "),
            *args,
            **kwargs,
            style=self.prompt_style,
        )

    # -------------------------------------------------------------------------
    # Generic environment variable handling
    # -------------------------------------------------------------------------

    def setenv(
        self,
        name: str,
        value: Union[str, Callable[[], str]],
        obscure: bool = False,
    ) -> None:
        """
        Set an environment variable if it is not already set.
        Reports the final value (pre-existing or new) if we are being verbose.
        """
        if name not in os.environ:
            if not isinstance(value, str):
                value = value()
            os.environ[name] = value
        value_shown = "*" * 4 if obscure else os.environ[name]
        self.envvar_info(f"{name}={value_shown}")

    @staticmethod
    def _write_envvars_to_file(
        f: TextIO, include_passwords: bool = False
    ) -> None:
        """
        We typically avoid saving passwords. Note that some of the config files
        do contain passwords.
        """
        for key, value in os.environ.items():
            if not key.startswith(DockerEnvVar.PREFIX):
                continue
            if not include_passwords and key.endswith(
                DockerEnvVar.PASSWORD_SUFFIX
            ):
                continue
            f.write(f"export {key}={value}\n")

    def write_environment_variables(
        self, permit_cfg_dir_save: bool = True
    ) -> None:
        config_dir = os.environ.get(DockerEnvVar.CONFIG_HOST_DIR)
        if config_dir and permit_cfg_dir_save:
            filename = os.path.join(config_dir, HostPath.ENVVAR_SAVE_FILE)
            with open(filename, mode="w") as f:
                self._write_envvars_to_file(f)
        else:
            with NamedTemporaryFile(delete=False, mode="w") as f:
                filename = f.name
                self._write_envvars_to_file(f)
        self.info(
            "Settings have been saved and can be loaded with "
            f"'source {filename}'."
        )

    # -------------------------------------------------------------------------
    # Shell handling
    # -------------------------------------------------------------------------

    @staticmethod
    def run_bash_command_inside_docker(bash_command: str) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        docker.compose.run(
            DockerComposeServices.CAMCOPS_WORKERS,
            remove=True,
            command=[DockerPath.BASH, "-c", bash_command],
        )

    # -------------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------------

    @staticmethod
    def format_multiline(values: Iterable[str]) -> str:
        indented_values = textwrap.indent("\n".join(values), 4 * " ")
        return f"\n{indented_values}"

    # -------------------------------------------------------------------------
    # Local file handling
    # -------------------------------------------------------------------------

    def search_replace_file(
        self, filename: str, replace_dict: Dict[str, str]
    ) -> None:
        """
        Replace placeholders marked as ``@@key@@`` with the associated value,
        in the file specified.
        """
        self.info(f"Editing {filename}")
        with open(filename, "r") as f:
            contents = f.read()

        for (search, replace) in replace_dict.items():
            if replace is None:
                self.fail(f"Can't replace '{search}' with None")

            contents = contents.replace(f"@@{search}@@", replace)

        with open(filename, "w") as f:
            f.write(contents)


# =============================================================================
# Installer specializations
# =============================================================================


class Wsl2Installer(Installer):
    pass


class NativeLinuxInstaller(Installer):
    def report_status(self) -> None:
        server_url = self.get_camcops_server_url()
        localhost_url = self.get_camcops_server_localhost_url()
        self.info(
            f"The CamCOPS application is running at {server_url} "
            f"or {localhost_url}"
        )

    def get_camcops_server_url(self) -> str:
        scheme = self.get_camcops_server_scheme()
        ip_address = self.get_camcops_server_ip_from_host()
        port = self.get_camcops_server_port_from_host()

        netloc = f"{ip_address}:{port}"
        path = self.get_camcops_server_path()
        params = query = fragment = None

        return urllib.parse.urlunparse(
            (scheme, netloc, path, params, query, fragment)
        )

    def get_camcops_server_ip_from_host(self) -> str:
        return self.get_camcops_server_ip_address()


class MacOsInstaller(Installer):
    pass


# =============================================================================
# Retrieve an appropriate installer for the host OS
# =============================================================================


def get_installer(verbose: bool) -> Installer:
    sys_info = uname()

    if "microsoft-standard" in sys_info.release:
        return Wsl2Installer(verbose=verbose)

    if sys_info.system == "Linux":
        return NativeLinuxInstaller(verbose=verbose)

    if sys_info.system == "Darwin":
        return MacOsInstaller(verbose=verbose)

    if sys_info.system == "Windows":
        print(
            "The installer cannot be run under native Windows. Please "
            "install Windows Subsystem for Linux 2 (WSL2) and run the "
            "installer from there. Alternatively follow the instructions "
            "to install CamCOPS manually."
        )
        sys.exit(EXIT_FAILURE)

    print(f"Sorry, the installer can't be run under {sys_info.system}.")
    sys.exit(EXIT_FAILURE)


# =============================================================================
# Command-line entry point
# =============================================================================


class Command:
    INSTALL = "install"
    RUN_COMMAND = "run"
    START = "start"
    STOP = "stop"
    SHELL = "shell"


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
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

    shell = subparsers.add_parser(
        Command.SHELL,
        help="Start a shell (command prompt) within a already-running "
        "CamCOPS Docker environment, in the "
        f"{DockerComposeServices.CAMCOPS_SERVER!r} container",
    )
    shell.add_argument(
        "--as_root",
        action="store_true",
        help="Enter as the 'root' user instead of the 'camcops' user",
        default=False,
    )

    args = parser.parse_args()

    installer = get_installer(verbose=args.verbose)

    if args.command == Command.INSTALL:
        installer.install()

    elif args.command == Command.START:
        installer.start()

    elif args.command == Command.STOP:
        installer.stop()

    elif args.command == Command.RUN_COMMAND:
        installer.run_camcops_command(args.camcops_command)

    elif args.command == Command.SHELL:
        installer.run_shell_in_camcops_container(as_root=args.as_root)

    else:
        raise AssertionError("Bug")


if __name__ == "__main__":
    main()
