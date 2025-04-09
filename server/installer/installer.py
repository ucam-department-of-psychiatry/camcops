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
Bootstrapped from ``installer.sh``. Note that the full CamCOPS Python
environment is NOT available.

"""

from argparse import ArgumentParser
from datetime import datetime, timedelta
import os
from pathlib import Path
from platform import uname
import re
import shutil
import sys
from tempfile import NamedTemporaryFile
import textwrap
from typing import Any, Callable, Dict, IO, Iterable, NoReturn, Type, Union
import urllib.parse

# See installer-requirements.txt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from prompt_toolkit import HTML, print_formatted_text, prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

# noinspection PyUnresolvedReferences
from python_on_whales import docker, DockerClient, DockerException
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
        VENV_DIR, "lib", "python3.9", "site-packages"
    )


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


class DockerEnvVar(EnvVar):
    """
    Environment variables governing the Docker setup.
    See: server/docker/dockerfiles/docker-compose.yaml
         server/docker/dockerfiles/docker-compose-mysql.yaml
         server/docker/dockerfiles/.env

    Any others go in InstallerEnvVar
    """

    PREFIX = "CAMCOPS_DOCKER"

    CAMCOPS_CONFIG_FILENAME = f"{PREFIX}_CAMCOPS_CONFIG_FILENAME"
    CAMCOPS_HOST_PORT = f"{PREFIX}_CAMCOPS_HOST_PORT"
    CAMCOPS_INTERNAL_PORT = f"{PREFIX}_CAMCOPS_INTERNAL_PORT"
    CONFIG_HOST_DIR = f"{PREFIX}_CONFIG_HOST_DIR"
    FLOWER_HOST_PORT = f"{PREFIX}_FLOWER_HOST_PORT"
    INSTALL_USER_ID = f"{PREFIX}_INSTALL_USER_ID"
    MYSQL_DATABASE_NAME = f"{PREFIX}_MYSQL_DATABASE_NAME"
    MYSQL_USER_NAME = f"{PREFIX}_MYSQL_USER_NAME"
    MYSQL_HOST_PORT = f"{PREFIX}_MYSQL_HOST_PORT"
    MYSQL_ROOT_PASSWORD = f"{PREFIX}_MYSQL_ROOT_{EnvVar.PASSWORD_SUFFIX}"
    MYSQL_USER_PASSWORD = f"{PREFIX}_MYSQL_USER_{EnvVar.PASSWORD_SUFFIX}"


class InstallerEnvVar(EnvVar):
    PREFIX = "CAMCOPS_INSTALLER"

    CREATE_MYSQL_CONTAINER = f"{PREFIX}_CREATE_MYSQL_CONTAINER"
    CREATE_SELF_SIGNED_CERTIFICATE = f"{PREFIX}_CREATE_SELF_SIGNED_CERTIFICATE"
    SSL_CERTIFICATE = f"{PREFIX}_SSL_CERTIFICATE"
    SSL_PRIVATE_KEY = f"{PREFIX}_SSL_PRIVATE_KEY"
    SUPERUSER_USERNAME = f"{PREFIX}_SUPERUSER_USERNAME"
    SUPERUSER_PASSWORD = f"{PREFIX}_SUPERUSER_{EnvVar.PASSWORD_SUFFIX}"
    USE_HTTPS = f"{PREFIX}_USE_HTTPS"

    MYSQL_SERVER = f"{PREFIX}_MYSQL_SERVER"
    MYSQL_PORT = f"{PREFIX}_MYSQL_PORT"
    X509_COUNTRY_NAME = f"{PREFIX}_X509_COUNTRY_NAME"
    X509_DNS_NAME = f"{PREFIX}_X509_DNS_NAME"
    X509_LOCALITY_NAME = f"{PREFIX}_X509_LOCALITY_NAME"
    X509_ORGANIZATION_NAME = f"{PREFIX}_X509_ORGANIZATION_NAME"
    X509_STATE_OR_PROVINCE_NAME = f"{PREFIX}_X509_STATE_OR_PROVINCE_NAME"


# =============================================================================
# Validators
# =============================================================================


class NotEmptyValidator(Validator):
    def validate(self, document: Document) -> None:
        if not document.text:
            raise ValidationError(message="Must provide an answer")


class FixedLengthValidator(Validator):
    def __init__(self, length: int) -> None:
        self.length = length

    def validate(self, document: Document) -> None:
        if len(document.text) != self.length:
            raise ValidationError(
                message=f"Must be {self.length} characters long"
            )


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
    def __init__(
        self,
        verbose: bool = False,
        update: bool = False,
    ) -> None:
        self._docker = None
        self.verbose = verbose
        self.update = update

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

    @property
    def docker(self) -> DockerClient:
        if self._docker is None:
            compose_files = ["docker-compose.yaml"]

            create_mysql_container = os.getenv(
                InstallerEnvVar.CREATE_MYSQL_CONTAINER
            )
            if create_mysql_container is None:
                self.fail(
                    "CAMCOPS_INSTALLER_CREATE_MYSQL_CONTAINER "
                    "should be set to 0 or 1"
                )

            if create_mysql_container == "1":
                compose_files.append("docker-compose-mysql.yaml")

            self._docker = DockerClient(compose_files=compose_files)

        return self._docker

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def install(self) -> None:
        self.start_message()
        self.check_setup()

        self.configure()
        self.write_environment_variables()
        if self.use_https():
            self.process_ssl_files()

        if self.update:
            self.rebuild_camcops_image()

        self.create_config()
        self.create_or_update_database()
        self.create_superuser()

        self.start()
        self.report_status()

    def update_installation(self) -> None:
        self.create_or_update_database()

    def rebuild_camcops_image(self) -> None:
        self.info("Updating existing CamCOPS installation")
        os.chdir(HostPath.DOCKERFILES_DIR)
        self.docker.compose.build(
            services=[
                DockerComposeServices.CAMCOPS_SCHEDULER,
                DockerComposeServices.CAMCOPS_SERVER,
                DockerComposeServices.CAMCOPS_WORKERS,
            ],
            cache=False,
        )

    def start(self) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        self.docker.compose.up(detach=True)

    def stop(self) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        self.docker.compose.down()

    def run_shell_in_camcops_container(self, as_root: bool = False) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)

        user = "root" if as_root else None

        self.docker.compose.execute(
            DockerComposeServices.CAMCOPS_SERVER,
            [DockerPath.BASH],
            user=user,
        )

    def run_camcops_command(self, camcops_command: str) -> None:
        self.run_bash_command_inside_docker(
            f"source /camcops/venv/bin/activate; {camcops_command}"
        )

    def run_dbshell_in_db_container(self) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)

        mysql_user = os.getenv(
            DockerEnvVar.MYSQL_USER_NAME,
        )

        db_name = os.getenv(
            DockerEnvVar.MYSQL_DATABASE_NAME,
        )

        command = [
            DockerPath.BASH,
            "-c",
            f"mysql -u {mysql_user} -p {db_name}",
        ]
        self.docker.compose.execute(DockerComposeServices.MYSQL, command)

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
            self.configure_camcops_server_ports()
            self.configure_https()
            self.configure_camcops_db()
            self.configure_superuser()
            self.configure_flower_host_port()
        except (KeyboardInterrupt, EOFError):
            # The user pressed CTRL-C or CTRL-D
            self.error("Installation aborted")
            self.write_environment_variables()
            sys.exit(EXIT_FAILURE)

    def configure_user(self) -> None:
        self.setenv(DockerEnvVar.INSTALL_USER_ID, self.get_install_user_id)

    def configure_config_files(self) -> None:
        self.setenv(DockerEnvVar.CONFIG_HOST_DIR, self.get_config_host_dir)
        self.create_config_directory()
        self.setenv(DockerEnvVar.CAMCOPS_CONFIG_FILENAME, "camcops.conf")

    def configure_camcops_server_ports(self) -> None:
        self.setenv(DockerEnvVar.CAMCOPS_HOST_PORT, self.get_camcops_host_port)
        self.setenv(
            DockerEnvVar.CAMCOPS_INTERNAL_PORT,
            self.get_camcops_internal_port,
        )

    def configure_https(self) -> None:
        self.setenv(InstallerEnvVar.USE_HTTPS, self.get_use_https)
        if self.use_https():
            self.configure_ssl_certificate()

    def configure_ssl_certificate(self) -> None:
        self.setenv(
            InstallerEnvVar.CREATE_SELF_SIGNED_CERTIFICATE,
            self.get_create_self_signed_certificate,
        )
        if self.should_create_self_signed_certificate():
            return self.configure_self_signed_ssl_certificate()

        self.configure_existing_ssl_certificate()

    def configure_self_signed_ssl_certificate(self) -> None:
        self.setenv(
            InstallerEnvVar.X509_COUNTRY_NAME,
            self.get_x509_country_name,
        )
        self.setenv(
            InstallerEnvVar.X509_STATE_OR_PROVINCE_NAME,
            self.get_x509_state_or_province_name,
        )
        self.setenv(
            InstallerEnvVar.X509_LOCALITY_NAME,
            self.get_x509_locality_name,
        )
        self.setenv(
            InstallerEnvVar.X509_ORGANIZATION_NAME,
            self.get_x509_organization_name,
        )
        self.setenv(
            InstallerEnvVar.X509_DNS_NAME,
            self.get_x509_dns_name,
        )

    def configure_existing_ssl_certificate(self) -> None:
        self.setenv(
            InstallerEnvVar.SSL_CERTIFICATE,
            self.get_ssl_certificate,
        )
        self.setenv(
            InstallerEnvVar.SSL_PRIVATE_KEY,
            self.get_ssl_private_key,
        )

    def configure_camcops_db(self) -> None:
        self.setenv(
            InstallerEnvVar.CREATE_MYSQL_CONTAINER,
            self.get_create_mysql_container,
        )

        if self.should_create_mysql_container():
            return self.configure_mysql_container()

        self.configure_external_db()

    def configure_mysql_container(self) -> None:
        self.setenv(
            DockerEnvVar.MYSQL_ROOT_PASSWORD,
            self.get_mysql_root_password,
            obscure=True,
        )
        self.setenv(InstallerEnvVar.MYSQL_SERVER, "mysql")
        self.setenv(InstallerEnvVar.MYSQL_PORT, "3306")
        self.setenv(DockerEnvVar.MYSQL_DATABASE_NAME, "camcops")
        self.setenv(DockerEnvVar.MYSQL_USER_NAME, "camcops")
        self.setenv(
            DockerEnvVar.MYSQL_USER_PASSWORD,
            self.get_mysql_user_password,
            obscure=True,
        )
        self.setenv(
            DockerEnvVar.MYSQL_HOST_PORT,
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
        self.setenv(
            InstallerEnvVar.MYSQL_SERVER,
            self.get_external_mysql_server,
        )
        self.setenv(
            InstallerEnvVar.MYSQL_PORT,
            self.get_external_mysql_port,
        )
        self.setenv(
            DockerEnvVar.MYSQL_DATABASE_NAME,
            self.get_external_mysql_database_name,
        )
        self.setenv(
            DockerEnvVar.MYSQL_USER_NAME,
            self.get_external_mysql_user_name,
        )
        self.setenv(
            DockerEnvVar.MYSQL_USER_PASSWORD,
            self.get_external_mysql_user_password,
            obscure=True,
        )

    def configure_superuser(self) -> None:
        self.setenv(
            InstallerEnvVar.SUPERUSER_USERNAME,
            self.get_superuser_username,
        )
        self.setenv(
            InstallerEnvVar.SUPERUSER_PASSWORD,
            self.get_superuser_password,
            obscure=True,
        )

    def configure_flower_host_port(self) -> None:
        self.setenv(DockerEnvVar.FLOWER_HOST_PORT, self.get_flower_host_port)

    @staticmethod
    def create_config_directory() -> None:
        camcops_config_dir = os.environ.get(DockerEnvVar.CONFIG_HOST_DIR)
        Path(camcops_config_dir).mkdir(parents=True, exist_ok=True)

    def create_config(self) -> None:
        config = self.config_full_path()

        if os.path.exists(config):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_filename = f"{config}.saved.{timestamp}"
            self.info(
                "Your existing config file has been renamed as "
                f"{backup_filename}"
            )
            os.rename(config, backup_filename)

        self.info(f"Creating {config}")
        Path(config).touch()
        self.run_camcops_command("env")
        self.run_camcops_command(
            "camcops_server demo_camcops_config --docker > "
            "$CAMCOPS_CONFIG_FILE"
        )
        self.configure_config()

    def configure_config(self) -> None:
        ssl_certificate = ""
        ssl_private_key = ""

        if self.use_https():
            ssl_certificate = os.path.join(
                DockerPath.CONFIG_DIR, "camcops.crt"
            )
            ssl_private_key = os.path.join(
                DockerPath.CONFIG_DIR, "camcops.key"
            )

        replace_dict = {
            "db_server": os.getenv(
                InstallerEnvVar.MYSQL_SERVER,
            ),
            "db_port": os.getenv(
                InstallerEnvVar.MYSQL_PORT,
            ),
            "db_user": os.getenv(
                DockerEnvVar.MYSQL_USER_NAME,
            ),
            "db_password": os.getenv(
                DockerEnvVar.MYSQL_USER_PASSWORD,
            ),
            "db_database": os.getenv(
                DockerEnvVar.MYSQL_DATABASE_NAME,
            ),
            "host": "0.0.0.0",
            "ssl_certificate": ssl_certificate,
            "ssl_private_key": ssl_private_key,
        }

        self.search_replace_file(self.config_full_path(), replace_dict)

    def process_ssl_files(self) -> None:
        if self.should_create_self_signed_certificate():
            self.create_self_signed_certificate()

        self.copy_ssl_files()

    def create_self_signed_certificate(self) -> None:
        # https://www.misterpki.com/python-self-signed-certificate/
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COUNTRY_NAME,
                    os.getenv(InstallerEnvVar.X509_COUNTRY_NAME),
                ),
                x509.NameAttribute(
                    NameOID.STATE_OR_PROVINCE_NAME,
                    os.getenv(InstallerEnvVar.X509_STATE_OR_PROVINCE_NAME),
                ),
                x509.NameAttribute(
                    NameOID.LOCALITY_NAME,
                    os.getenv(InstallerEnvVar.X509_LOCALITY_NAME),
                ),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME,
                    os.getenv(InstallerEnvVar.X509_ORGANIZATION_NAME),
                ),
                # It looks like the Common Name can be the same as the DNS name
                # and some browsers will ignore it if the DNS name is present.
                x509.NameAttribute(
                    NameOID.COMMON_NAME,
                    os.getenv(InstallerEnvVar.X509_DNS_NAME),
                ),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName(os.getenv(InstallerEnvVar.X509_DNS_NAME))]
                ),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        with NamedTemporaryFile(delete=False, mode="wb") as f:
            key_filename = f.name
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        with NamedTemporaryFile(delete=False, mode="wb") as f:
            cert_filename = f.name
            f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))

        self.setenv(
            InstallerEnvVar.SSL_PRIVATE_KEY,
            key_filename,
        )

        self.setenv(
            InstallerEnvVar.SSL_CERTIFICATE,
            cert_filename,
        )

    @staticmethod
    def copy_ssl_files() -> None:
        config_dir = os.getenv(DockerEnvVar.CONFIG_HOST_DIR)

        cert_dest = os.path.join(config_dir, "camcops.crt")
        key_dest = os.path.join(config_dir, "camcops.key")

        shutil.copy(os.getenv(InstallerEnvVar.SSL_CERTIFICATE), cert_dest)
        shutil.copy(os.getenv(InstallerEnvVar.SSL_PRIVATE_KEY), key_dest)

    def create_or_update_database(self) -> None:
        self.run_camcops_command(
            "camcops_server upgrade_db --config $CAMCOPS_CONFIG_FILE"
        )

    def create_superuser(self) -> None:
        # Will either create a superuser or update an existing one
        # with the given username
        username = os.getenv(InstallerEnvVar.SUPERUSER_USERNAME)
        password = os.getenv(InstallerEnvVar.SUPERUSER_PASSWORD)
        self.run_camcops_command(
            "camcops_server make_superuser "
            f"--username {username} --password {password}"
        )

    def report_status(self) -> None:
        localhost_url = self.get_camcops_server_localhost_url()
        self.info(f"The CamCOPS application is running at {localhost_url}")

    # -------------------------------------------------------------------------
    # Fetching information from environment variables or statically
    # -------------------------------------------------------------------------

    @staticmethod
    def get_install_user_id() -> str:
        return str(os.geteuid())

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
        return os.getenv(InstallerEnvVar.USE_HTTPS) == "1"

    @staticmethod
    def should_create_self_signed_certificate() -> bool:
        return os.getenv(InstallerEnvVar.CREATE_SELF_SIGNED_CERTIFICATE) == "1"

    @staticmethod
    def should_create_mysql_container() -> bool:
        return os.getenv(InstallerEnvVar.CREATE_MYSQL_CONTAINER) == "1"

    @staticmethod
    def get_camcops_server_path() -> str:
        return "/"

    @staticmethod
    def get_camcops_server_ip_address() -> str:
        container = docker.container.inspect("camcops_camcops_server")
        network_settings = container.network_settings

        return network_settings.networks["camcops_camcops_network"].ip_address

    @staticmethod
    def get_camcops_server_port() -> str:
        return os.getenv(DockerEnvVar.CAMCOPS_INTERNAL_PORT)

    @staticmethod
    def get_camcops_server_port_from_host() -> str:
        return os.getenv(DockerEnvVar.CAMCOPS_HOST_PORT)

    # -------------------------------------------------------------------------
    # Fetching information from the user
    # -------------------------------------------------------------------------

    def get_config_host_dir(self) -> str:
        return self.get_user_dir(
            "Select the host directory where CamCOPS will store its "
            "configuration:",
            default=HostPath.DEFAULT_HOST_CAMCOPS_CONFIG_DIR,
        )

    def get_camcops_host_port(self) -> str:
        return self.get_user_input(
            ("Enter the port where CamCOPS will appear on the host:"),
            default="443",
        )

    def get_camcops_internal_port(self) -> str:
        return "8000"  # Matches PORT in camcops.conf

    def get_use_https(self) -> str:
        return self.get_user_boolean(
            "Access CamCOPS directly over HTTPS? (y/n)"
        )

    def get_create_self_signed_certificate(self) -> str:
        return self.get_user_boolean(
            "The CamCOPS installer can create a self-signed SSL certificate "
            "for you. This is for testing only and should not be used in a "
            "secure production environment. Alternatively you can select the "
            "location of an existing SSL certificate and private key. "
            "Create a self-signed certificate? (y/n)"
        )

    def get_ssl_certificate(self) -> str:
        return self.get_user_file("Select the SSL certificate file:")

    def get_ssl_private_key(self) -> str:
        return self.get_user_file("Select the SSL private key file:")

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
        username = os.environ[DockerEnvVar.MYSQL_USER_NAME]
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

    def get_x509_country_name(self) -> str:
        return self.get_user_input(
            "Enter the 2-letter country code (e.g. GB):",
            validator=FixedLengthValidator(2),
        )

    def get_x509_state_or_province_name(self) -> str:
        return self.get_user_input(
            "Enter the state or province name (e.g. Cambridgeshire):"
        )

    def get_x509_locality_name(self) -> str:
        return self.get_user_input("Enter the locality name (e.g. Cambridge):")

    def get_x509_organization_name(self) -> str:
        return self.get_user_input(
            "Enter the organization name (e.g. University of Cambridge):"
        )

    def get_x509_dns_name(self) -> str:
        return self.get_user_input(
            "Enter the DNS name. This should match the server name where the "
            "certificate is installed (e.g. camcops.example.com or "
            "localhost):",
            "localhost",
        )

    def get_flower_host_port(self) -> str:
        return self.get_user_input(
            (
                "Enter the port where the Flower event monitoring tool "
                "will appear on the host:"
            ),
            default="5555",
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

    def get_user_input(
        self,
        text: str,
        default: str = "",
        validator: Validator = NotEmptyValidator(),
    ) -> str:
        return self.prompt(text, default=default, validator=validator)

    def prompt(self, text: str, *args: Any, **kwargs: Any) -> str:
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
        f: IO[str], include_passwords: bool = False
    ) -> None:
        """
        We typically avoid saving passwords. Note that some of the config files
        do contain passwords.
        """
        for key, value in os.environ.items():
            if not (
                key.startswith(DockerEnvVar.PREFIX)
                or key.startswith(InstallerEnvVar.PREFIX)
            ):
                continue
            if not include_passwords and key.endswith(EnvVar.PASSWORD_SUFFIX):
                continue
            f.write(f'export {key}="{value}"\n')

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

    def run_bash_command_inside_docker(self, bash_command: str) -> None:
        os.chdir(HostPath.DOCKERFILES_DIR)
        self.docker.compose.run(
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

        for search, replace in replace_dict.items():
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
        ip_address = self.get_camcops_server_ip_address()
        port = self.get_camcops_server_port()

        netloc = f"{ip_address}:{port}"
        path = self.get_camcops_server_path()
        params = query = fragment = None

        return urllib.parse.urlunparse(
            (scheme, netloc, path, params, query, fragment)
        )


class MacOsInstaller(Installer):
    pass


# =============================================================================
# Retrieve an appropriate installer for the host OS
# =============================================================================


def get_installer_class() -> Type[Installer]:
    sys_info = uname()

    if "microsoft-standard" in sys_info.release:
        return Wsl2Installer

    if sys_info.system == "Linux":
        return NativeLinuxInstaller

    if sys_info.system == "Darwin":
        return MacOsInstaller

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
    DBSHELL = "dbshell"
    INSTALL = "install"
    RUN_COMMAND = "run"
    START = "start"
    STOP = "stop"
    SHELL = "shell"


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
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

    installer = get_installer_class()(
        verbose=args.verbose,
        update=args.update,
    )

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

    elif args.command == Command.DBSHELL:
        installer.run_dbshell_in_db_container()

    else:
        raise AssertionError("Bug")


if __name__ == "__main__":
    main()
