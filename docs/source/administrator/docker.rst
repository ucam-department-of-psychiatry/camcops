..  docs/source/administrator/docker.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

.. _AMQP: https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol
.. _CherryPy: https://cherrypy.org/
.. _Docker: https://www.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/
.. _Flower: https://flower.readthedocs.io/
.. _Gunicorn: https://gunicorn.org/
.. _MySQL: https://www.mysql.com/
.. _mysqlclient: https://pypi.org/project/mysqlclient/
.. _RabbitMQ: https://www.rabbitmq.com/


.. _server_docker:

Installing and running the CamCOPS server via Docker
====================================================

..  contents::
    :local:
    :depth: 3


Overview
--------

Docker_ is a cross-platform system for running applications in "containers". A
computer (or computing cluster) can run lots of containers. They allow
applications to be set up in standardized and isolated enviroments, which
include their own operating system). The containers then talk to each other,
and to their "host" computer, to do useful things.

The core of Docker is called Docker Engine. The `Docker Compose`_ tool allows
multiple containers to be created, started, and connected together
automatically.

CamCOPS provides a Docker setup to make installation easy. This uses Docker
Compose to set up several containers, specifically:

- an optional database system, via MySQL_ on Linux (internal container name ``mysql``);
- a message queue, via RabbitMQ_ on Linux (``rabbitmq``);
- the CamCOPS web server itself, offering SSL directly via CherryPy_ on Linux
  (``camcops_server``);
- the CamCOPS scheduler (``camcops_scheduler``);
- CamCOPS workers, to perform background tasks (``camcops_workers``);
- a background task monitor, using Flower_ (``camcops_monitor``).

We provide an installer script as a wrapper to Docker Compose.

.. _quick_start:

Quick start
-----------

Windows
^^^^^^^

- Install Windows Subsystem for Linux 2 (WSL2):
  https://docs.microsoft.com/en-us/windows/wsl/install.
- Install Docker Desktop: https://docs.docker.com/desktop/
- Enable WSL2 in Docker Desktop: https://docs.docker.com/desktop/windows/wsl/
- From the Linux terminal install python3-virtualenv:
  Ubuntu: ``sudo apt -y install python3-virtualenv python3-venv``
- See :ref:`All platforms <all_platforms>` below.


Linux
^^^^^

- Install Docker Engine: https://docs.docker.com/engine/install/
- Install Docker Compose v2 or greater:
  https://docs.docker.com/compose/cli-command/#install-on-linux
- Install python3-virtualenv:

  - Ubuntu: ``sudo apt -y install python3-virtualenv python3-venv``

- See :ref:`All platforms <all_platforms>` below.


MacOS
^^^^^

- Install Docker Desktop: https://docs.docker.com/desktop/
- Install python3 and python3-virtualenv
- See :ref:`All platforms <all_platforms>` below.


.. _all_platforms:

All platforms
^^^^^^^^^^^^^

The installer can be run interactively, where you will be prompted to enter
settings specific to your CamCOPS installation. Alternatively you can supply
this information by setting environment variables. This is best done by putting
the settings in a file and executing them before running the installer (e.g.
``source ~/my_camcops_settings``). The installer will save to a
file any non-password environment variables that you've entered
interactively. The file can then be executed should you need to run the
installer a second time.

Here is an example settings file. See :ref:`Docker Environment Variables
<docker_environment_variables>` and :ref:`Installer Environment Variables
<installer_environment_variables>` for a description of each setting.

    .. code-block:: bash

        export CAMCOPS_DOCKER_CAMCOPS_CONFIG_FILENAME="camcops.conf"
        export CAMCOPS_DOCKER_CAMCOPS_HOST_PORT="443"
        export CAMCOPS_DOCKER_CAMCOPS_INTERNAL_PORT="8000"
        export CAMCOPS_DOCKER_CONFIG_HOST_DIR="${HOME}/camcops_config"
        export CAMCOPS_DOCKER_FLOWER_HOST_PORT="5556"
        export CAMCOPS_DOCKER_INSTALL_USER_ID="1000"
        export CAMCOPS_DOCKER_MYSQL_DATABASE_NAME="camcops"
        export CAMCOPS_DOCKER_MYSQL_HOST_PORT="43306"
        export CAMCOPS_DOCKER_MYSQL_USER_NAME="camcops"
        export CAMCOPS_INSTALLER_CREATE_MYSQL_CONTAINER="1"
        export CAMCOPS_INSTALLER_CREATE_SELF_SIGNED_CERTIFICATE="1"
        export CAMCOPS_INSTALLER_MYSQL_PORT="3306"
        export CAMCOPS_INSTALLER_MYSQL_SERVER="mysql"
        export CAMCOPS_INSTALLER_SUPERUSER_USERNAME="admin"
        export CAMCOPS_INSTALLER_USE_HTTPS="1"
        export CAMCOPS_INSTALLER_X509_COUNTRY_NAME="GB"
        export CAMCOPS_INSTALLER_X509_DNS_NAME="localhost"
        export CAMCOPS_INSTALLER_X509_LOCALITY_NAME="Cambridge"
        export CAMCOPS_INSTALLER_X509_ORGANIZATION_NAME="University of Cambridge"
        export CAMCOPS_INSTALLER_X509_STATE_OR_PROVINCE_NAME="Cambridgeshire"


To install CamCOPS from scratch:

    .. code-block:: bash

        curl --location https://github.com/ucam-department-of-psychiatry/camcops/releases/latest/download/installer.sh --fail --output camcops_docker_installer.sh && chmod u+x camcops_docker_installer.sh && ./camcops_docker_installer.sh

Enter any required information and after several minutes, you should see the
message ``The CamCOPS application is running at ...`` and everything will be
operational. Using any web browser, you should be able to browse to the CamCOPS
site at your chosen host port and protocol, and log in using the superuser
account you have just created.

To update an existing installation to a newer version of CamCOPS, set the above
environment variables with the existing settings (otherwise you will be prompted
to enter them again) and run:

    .. code-block:: bash

        ./camcops_docker_installer.sh -u


.. _docker_environment_variables:

Docker Environment variables
----------------------------

Docker control files are in the ``server/docker`` directory of the CamCOPS
source tree. Setup is controlled by the ``docker compose`` application.

.. note::

    Default values are taken from ``server/docker/.env``. Unfortunately, this
    name is fixed by Docker Compose, and this file is hidden under Linux (as
    are any files starting with ``.``).


.. _CAMCOPS_DOCKER_CONFIG_HOST_DIR:

CAMCOPS_DOCKER_CONFIG_HOST_DIR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**No default. Must be set.**

Path to a directory on the host that contains key configuration files. Don't
use a trailing slash.

In this directory, the installer will create a file called ``camcops.conf``, the config
file (or, if you have set CAMCOPS_DOCKER_CAMCOPS_CONFIG_FILENAME_, that
filename!).

.. note::
    **Under Windows,** don't use Windows paths like
    ``C:\Users\myuser\my_camcops_dir``. Translate this to Docker notation as
    ``/host_mnt/c/Users/myuser/my_camcops_dir``. As of 2020-07-21, this doesn't
    seem easy to find in the Docker docs!


.. _CAMCOPS_DOCKER_CAMCOPS_CONFIG_FILENAME:

CAMCOPS_DOCKER_CAMCOPS_CONFIG_FILENAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: camcops.conf*

Base name of the CamCOPS config file (see CAMCOPS_DOCKER_CONFIG_HOST_DIR_).


CAMCOPS_DOCKER_FLOWER_HOST_PORT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: 5555*

Host port on which to launch the Flower_ monitor.

CAMCOPS_DOCKER_INSTALL_USER_ID
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**No default.**

Set to the the ID of the user running the installer. A ``camcops`` user will be
created in the CamCOPS server Docker Image with this ID. This means that file
permissons for the CamCOPS config volume will be the same both in and outside
the container. You can enter the Docker container as this user or the root one.


CAMCOPS_DOCKER_CAMCOPS_HOST_PORT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: 443*

The TCP/IP port number on the host computer that CamCOPS should provide an
HTTP or HTTPS (SSL) connection on.

It is strongly recommended that you run CamCOPS over HTTPS. The two ways of
doing this are:

- Have CamCOPS run plain HTTP, and connect it to another web server (e.g.
  Apache) that provides the HTTPS component.

  - If you do this, you should **not** expose this port to the "world", since
    it offers insecure HTTP.

  - The motivation for this method is usually that you are running multiple web
    services, of which CamCOPS is one.

  - We don't provide Apache within Docker, because the Apache-inside-Docker
    would only see CamCOPS, so there's not much point -- you might as well
    use the next option...

- Have CamCOPS run HTTPS directly, by specifying the :ref:`SSL_CERTIFICATE
  <SSL_CERTIFICATE>` and :ref:`SSL_PRIVATE_KEY <SSL_PRIVATE_KEY>` options.

  - This is simpler if CamCOPS is the only web service you are running on this
    machine. Use the standard HTTPS port, 443, and expose it to the outside
    through your server's firewall. (You are running a firewall, right?)


CAMCOPS_DOCKER_CAMCOPS_INTERNAL_PORT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: 8000*

The TCP/IP port number used by CamCOPS internally. Must match the :ref:`PORT
<PORT>` option in the CamCOPS config file.


.. _CAMCOPS_DOCKER_MYSQL_DATABASE_NAME:

CAMCOPS_DOCKER_MYSQL_DATABASE_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: camcops*

Name of the MySQL database to be used for CamCOPS data.


.. _CAMCOPS_DOCKER_MYSQL_USER_PASSWORD:

CAMCOPS_DOCKER_MYSQL_USER_PASSWORD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**No default. Must be set during MySQL container creation.**

MySQL password for the CamCOPS database user (whose name is set by
CAMCOPS_DOCKER_MYSQL_USER_NAME_).

.. note::
    This only needs to be set when Docker Compose is creating the MySQL
    container for the first time. After that, it doesn't have to be set (and is
    probably best not set for security reasons!).


.. _CAMCOPS_DOCKER_MYSQL_USER_NAME:

CAMCOPS_DOCKER_MYSQL_USER_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: camcops*

MySQL username for the main CamCOPS user. This user is given full control over
the database named in CAMCOPS_DOCKER_MYSQL_DATABASE_NAME_. See also
CAMCOPS_DOCKER_MYSQL_USER_PASSWORD_.


CAMCOPS_DOCKER_MYSQL_HOST_PORT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default: 3306*

Port published to the host, giving access to the CamCOPS MySQL installation.
You can use this to allow other software to connect to the CamCOPS database
directly.

This might include using MySQL tools from the host to perform database backups
(though Docker volumes can also be backed up in their own right).

The default MySQL port is 3306. If you run MySQL on your host computer for
other reasons, this port will be taken, and you should change it to something
else.

You should **not** expose this port to the "outside", beyond your host.


.. _CAMCOPS_DOCKER_MYSQL_ROOT_PASSWORD:

CAMCOPS_DOCKER_MYSQL_ROOT_PASSWORD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**No default. Must be set during MySQL container creation.**

MySQL password for the ``root`` user.

.. note::
    This only needs to be set when Docker Compose is creating the MySQL
    container for the first time. After that, it doesn't have to be set (and is
    probably best not set for security reasons!).


COMPOSE_PROJECT_NAME
^^^^^^^^^^^^^^^^^^^^

*Default: camcops*

This is the Docker Compose project name. It's used as a prefix for all the
containers in this project.


.. _installer_environment_variables:

Installer Environment variables
-------------------------------

The following environment variables are used by the CamCOPS installer to create
the CamCOPS configuration file but are not passed on to Docker Compose:

CAMCOPS_INSTALLER_CREATE_MYSQL_CONTAINER
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set to ``1`` to create a MySQL container for the CamCOPS database. Set to
``0`` to use an external MySQL database.


CAMCOPS_INSTALLER_CREATE_SELF_SIGNED_CERTIFICATE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set to ``1`` to generate a self-signed SSL certificate for CamCOPS. Use only
for testing and not in a secure production environment. Set to ``0`` to use
an existing SSL certificate and private key.


CAMCOPS_INSTALLER_MYSQL_SERVER
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If using a MySQL database server outside of Docker, this should be set to the
host name or IP address of the MySQL server. For the Docker host machine, this
should be ``host.docker.internal``.


CAMCOPS_INSTALLER_MYSQL_PORT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If using a MySQL database server outside of Docker, this should be set to the
port of the MySQL server.


CAMCOPS_INSTALLER_SUPERUSER_USERNAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The username of the CamCOPS superuser to be created.

CAMCOPS_INSTALLER_SUPERUSER_PASSWORD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The password of the CamCOPS superuser to be created.

CAMCOPS_INSTALLER_USE_HTTPS
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Access the CamCOPS over HTTPS? (``0`` = no, ``1`` = yes)
See CAMCOPS_DOCKER_CAMCOPS_HOST_PORT_ above.

CAMCOPS_INSTALLER_X509_COUNTRY_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When generating the self-signed certificate, this is the two-letter country code
where the self-signed certificate is issued e.g. ``GB``.

CAMCOPS_INSTALLER_X509_STATE_OR_PROVINCE_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When generating the self-signed certificate, this is the state or province where
the certificate was issued e.g. ``Cambridgeshire``.

CAMCOPS_INSTALLER_X509_LOCALITY_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When generating the self-signed certificate, this is the locality where the
certificate was issued e.g. ``Cambridge``.

CAMCOPS_INSTALLER_X509_ORGANIZATION_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When generating the self-signed certificate, this is the organization where the
certificate was issued e.g. ``University of Cambridge``.

CAMCOPS_INSTALLER_X509_DNS_NAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When generating the self-signed certificate, this should match the server name
where the certificate is installed e.g. ``camcops.example.com``.


.. _camcops_config_file_docker:

The CamCOPS configuration file for Docker
-----------------------------------------

The CamCOPS configuration file is described :ref:`here <server_config_file>`.
There are a few special things to note within the Docker environment.

- **CELERY_BROKER_URL.**
  The RabbitMQ (AMQP_ server) lives in a container named (internally)
  ``rabbitmq`` and uses the default AMQP port of 5672. The
  :ref:`CELERY_BROKER_URL <CELERY_BROKER_URL>` variable should therefore be set
  exactly as follows:

  .. code-block:: none

    CELERY_BROKER_URL = amqp://rabbitmq:5672/
                        ^      ^        ^
                        |      |        |
                        |      |        +- port number
                        |      +- internal name of container running RabbitMQ
                        +- "use AMQP protocol"

- **DB_URL.**
  MySQL runs in a container called (internally) ``mysql`` and the mysqlclient_
  drivers for Python are installed for CamCOPS. (These use C-based MySQL
  drivers for speed). The :ref:`DB_URL <DB_URL>` variable should therefore be
  of the form:

  .. code-block:: none

    DB_URL = mysql+mysqldb://camcops:ZZZ_PASSWORD_REPLACE_ME@mysql:3306/camcops?charset=utf8
             ^     ^         ^       ^                       ^     ^    ^      ^
             |     |         |       |                       |     |    |      |
             |     |         |       |                       |     |    |      +- charset options; don't alter
             |     |         |       |                       |     |    +- database name; should match
             |     |         |       |                       |     |       CAMCOPS_DOCKER_MYSQL_DATABASE_NAME
             |     |         |       |                       |     +- port; don't alter
             |     |         |       |                       +- container name; don't alter
             |     |         |       +- MySQL password; should match CAMCOPS_DOCKER_MYSQL_USER_PASSWORD
             |     |         +- MySQL username; should match CAMCOPS_DOCKER_MYSQL_USER_NAME
             |     +- "use mysqldb [mysqlclient] Python driver"
             +- "use MySQL dialect"

  It remains possible to point "CamCOPS inside Docker" to "MySQL outside
  Docker" (rather than the instance of MySQL supplied with CamCOPS via
  Docker). This would be unusual, but it's up to you.

- **HOST.**
  This should be ``0.0.0.0`` for operation within Docker [#host]_.

- **References to files on disk.**
  CamCOPS mounts a configuration directory from host computer, specified via
  CAMCOPS_DOCKER_CONFIG_HOST_DIR_. From the perspective of the CamCOPS Docker
  containers, this directory is mounted at ``/camcops/cfg``.

  Accordingly, **all user-supplied configuration files should be placed within
  this directory, and referred to via** ``/camcops/cfg``. System-supplied files
  are also permitted within ``/camcops/venv`` (and the demonstration config
  file will set this up for you).

  For example:

  .. code-block:: none

    Host computer:

        /etc
            /camcops
                extra_strings/
                    phq9.xml
                    ...
                camcops.conf
                ssl_camcops.cert
                ssl_camcops.key

    Environment variables for Docker:

        CAMCOPS_DOCKER_CAMCOPS_CONFIG_FILENAME=camcops.conf
        CAMCOPS_DOCKER_CAMCOPS_HOST_PORT=443
        CAMCOPS_DOCKER_CAMCOPS_INTERNAL_PORT=8000
        CAMCOPS_DOCKER_CONFIG_HOST_DIR=/etc/camcops

    CamCOPS config file:

        [site]

        # ...

        EXTRA_STRING_FILES =
            /camcops/venv/lib/python3.6/site-packages/camcops_server/extra_strings/*.xml
            /camcops/cfg/extra_strings/*.xml

        # ...

        [server]

        HOST = 0.0.0.0
        PORT = 8000
        SSL_CERTIFICATE = /camcops/cfg/ssl_camcops.cert
        SSL_PRIVATE_KEY = /camcops/cfg/ssl_camcops.key

        # ...

  CamCOPS will warn you if you are using Docker but your file references are
  not within the ``/camcops/cfg`` mount point.


Using a database outside the Docker environment
-----------------------------------------------

CamCOPS can optionally create a MySQL system and database inside Docker.  For an
external MySQL system, the installer will set the :ref:`DB_URL <DB_URL>`
parameter to where you want.


Tools
-----

There are a number of tools that can be used once CamCOPS is running under Docker.
To use these, first enter the CamCOPS installer virtual environment:

  .. code-block:: bash

    source ~/.virtualenvs/camcops_installer/bin/activate

Next navigate to the CamCOPS installer directory/

  .. code-block:: bash

    cd ~/camcops/server/installer

Ensure the environment variables set by the installer script are set. e.g.:

  .. code-block:: bash

    source ~/camcops_config/set_camcops_docker_host_envvars

The tools are accessed with ``python installer.py <command>`` where
``<command>`` is one of:


.. _dbshell:

dbshell
^^^^^^^

Start the MySQL command-line client inside the docker container.


.. _shell:

shell
^^^^^

Starts a shell (command prompt) within an already-running CamCOPS Docker
environment.  By default the user will be ``camcops``. Use the ``--as_root``
argument to be the ``root`` user.

.. warning::

    Running a shell within a container as ``root`` allows you to break things!
    Be careful.


.. _start:

start
^^^^^

Shortcut for ``docker compose up -d`` with the appropriate ``docker-compose*.yaml`` files. The ``-d`` switch is short for
``--detach`` (or daemon mode).

.. _stop:

stop
^^^^

Shortcut for ``docker compose down`` with the appropriate ``docker-compose*.yaml``.

.. _run:

run
^^^

This script starts a container with the CamCOPS server image, activates the
CamCOPS virtual environment, and runs a command within it. For example, to
upgrade the CamCOPS database:

    .. code-block:: bash

      python installer.py run "camcops_server upgrade_db --config /camcops/cfg/camcops.conf"


.. _troubleshooting_docker:

Troubleshooting
---------------

Can't start Docker containers on a Linux host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you get an error like:

.. code-block:: none

    ERROR: Couldn't connect to Docker daemon at http+docker://localunixsocket - is it running?

then check:

1. Is Docker running (``ps aux | grep dockerd`` or a service command, such as
   ``service docker status`` under Ubuntu)? If not, start its service (e.g.
   under Ubuntu, ``sudo service docker start``).

2. Is your user in the Docker group (``grep docker /etc/group``)? If not, add
   your user, then log out and log in again for the changes to be picked up.


Explore a running Docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The shortcuts above (e.g. shell_) start a **new container** (via
``docker compose run``). To explore a container that is **already running**,
find the container ID via ``docker container ls`` and use ``docker exec``, e.g.
as ``docker exec -it CONTAINER /bin/bash``.


Warnings from Celery under Docker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This warning:

.. code-block:: none

    camcops_workers_1    | /camcops/venv/lib/python3.6/site-packages/celery/platforms.py:801: RuntimeWarning: You're running the worker with superuser privileges: this is
    camcops_workers_1    | absolutely not recommended!
    camcops_workers_1    |
    camcops_workers_1    | Please specify a different user using the --uid option.
    camcops_workers_1    |
    camcops_workers_1    | User information: uid=0 euid=0 gid=0 egid=0
    camcops_workers_1    |
    camcops_workers_1    |   uid=uid, euid=euid, gid=gid, egid=egid,

... can be ignored.

.. todo::
    Make container apps run as non-root? See
    https://medium.com/redbubble/running-a-docker-container-as-a-non-root-user-7d2e00f8ee15.


Development notes
-----------------

- **Config information.**
  There are several ways, but mounting a host directory containing a config
  file is perfectly reasonable. See
  https://dantehranian.wordpress.com/2015/03/25/how-should-i-get-application-configuration-into-my-docker-containers/.

- **Secrets, such as passwords.**
  This is a little tricky. Environment variables and config files are both
  reasonable options; see e.g.
  https://stackoverflow.com/questions/22651647/docker-and-securing-passwords.
  Environment variables are visible externally (e.g. ``docker exec CONTAINER
  env``) but you have to have Docker privileges (be in the ``docker`` group) to
  do that. Docker "secrets" require Docker Swarm (not just plain Docker
  Compose). We are using a config file for CamCOPS, and environment variables
  for the MySQL container.

- **Data storage.**
  Should data (e.g. MySQL databases) be stored on the host (via a "bind mount"
  of a directory), or in Docker volumes? Docker says clearly: volumes. See
  https://docs.docker.com/storage/volumes/.

- **TCP versus UDS.**
  Currently the connection between CamCOPS and MySQL is via TCP/IP. It would be
  possible to use Unix domain sockets instead. This would be a bit trickier.
  Ordinarily, it would bring some speed advantages; I'm not sure if that
  remains the case between Docker containers. The method is to mount a host
  directory; see
  https://superuser.com/questions/1411402/how-to-expose-linux-socket-file-from-docker-container-mysql-mariadb-etc-to.
  It would add complexity. The other advantage of using TCP is that we can
  expose the MySQL port to the host for administrative use.

- **Database creation.**
  It might be nice to upgrade the database a little more automatically, but
  this is certainly not part of Docker *image* creation (the image is static
  and the data is dynamic) and shouldn't be part of routine container startup,
  so perhaps it's as good as is reasonable.

- **Scaling up.**
  At present we use a fixed number of containers, some with several processes
  running within. There are other load distribution mechanisms possible with
  Docker Compose.


===============================================================================

.. rubric:: Footnotes

.. [#host]
    https://nickjanetakis.com/blog/docker-tip-54-fixing-connection-reset-by-peer-or-similar-errors
