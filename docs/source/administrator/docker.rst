..  docs/source/administrator/docker.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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
applications to be set up in standardized and isolated enviroments (including,
effectively, their own operating system). The containers then talk to each
other, and to their "host" computer, to do useful things.

The core of Docker is called Docker Engine. The `Docker Compose`_ tool allows
multiple containers to be "spun up" and connected together automatically.

CamCOPS provides a Docker setup to make installation easy. This uses Docker
Compose to set up several containers, specifically:

- a database system, via MySQL_ on Linux;
- a message queue, via RabbitMQ_ on Linux;
- the CamCOPS web server itself, offering SSL directly via Gunicorn_ on Linux;
- the CamCOPS scheduler;
- CamCOPS workers, to perform background tasks;
- a background task monitor, using Flower_.


Prerequisites
-------------

- You need Docker Engine installed. See
  https://docs.docker.com/engine/install/.

- You need Docker Compose installed. See
  https://docs.docker.com/compose/install/.

- Fetch the CamCOPS source.

  .. todo:: Docker/CamCOPS source: is that the right method?


Environment variables
---------------------

Docker control files are in the ``server/docker/`` directory of the CamCOPS
source tree. Setup is controlled by the ``docker-compose`` application.

Default values are in ``server/docker/.env``. Unfortunately, this name is fixed
by Docker Compose, and this file is hidden under Linux (as are any files
starting with ``.``).


.. CAMCOPS_DOCKER_CONFIG_DIR:

CAMCOPS_DOCKER_CONFIG_DIR
~~~~~~~~~~~~~~~~~~~~~~~~~

**No default. Must be set.**

Path to a directory on the host that contains a file called ``camcops.conf``,
the config file (or, if you have set CAMCOPS_DOCKER_CONFIG_FILENAME_, that
filename!).


.. CAMCOPS_DOCKER_CONFIG_FILENAME:

CAMCOPS_DOCKER_CONFIG_FILENAME
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Default: camcops.conf*

Base name of the CamCOPS config file (see CAMCOPS_DOCKER_CONFIG_DIR_).


CAMCOPS_DOCKER_FLOWER_HOST_PORT
-------------------------------

*Default: 5555*

Host port on which to launch the Flower_ monitor.


CAMCOPS_DOCKER_HTTPS_HOST_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Default: 443*

The TCP/IP port number on the host computer that CamCOPS should provide an
HTTPS (SSL) connection on.


COMPOSE_PROJECT_NAME
~~~~~~~~~~~~~~~~~~~~

*Default: camcops*

This is the Docker Compose project name. It's used as a prefix for all the
containers in this project.


.. CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME:

CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Default: camcops*

Name of the MySQL database to be used for CamCOPS data.


.. _CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_PASSWORD:

CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_PASSWORD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**No default. Must be set.**

MySQL password for the CamCOPS database user (whose name is set by
CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME_).


.. CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME:

CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Default: camcops*

MySQL username for the main CamCOPS user. This user is given full control over
the database named in CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME_. See also
CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_PASSWORD_.


CAMCOPS_DOCKER_MYSQL_HOST_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Default: 3306*

Port published to the host giving access to the CamCOPS MySQL installation. You
can use this to allow other software to connect to the CamCOPS database
directly.

This might include using MySQL tools from the host to perform database backups
(though Docker volumes can also be backed up in their own right).

The default MySQL port is 3306. If you run MySQL on your host computer for
other reasons, this port will be taken, and you should change it to something
else.


.. CAMCOPS_DOCKER_MYSQL_ROOT_PASSWORD:

CAMCOPS_DOCKER_MYSQL_ROOT_PASSWORD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**No default. Must be set.**

MySQL password for the ``root`` user.


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
             |     |         |       |                       |     |       CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME
             |     |         |       |                       |     +- port; don't alter
             |     |         |       |                       +- container name; don't alter
             |     |         |       +- MySQL password; should match CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_PASSWORD
             |     |         +- MySQL username; should match CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME
             |     +- "use mysqldb [mysqlclient] Python driver"
             +- "use MySQL dialect"

  It remains possible to point "CamCOPS inside Docker" to "MySQL outside
  Docker" (rather than the instance of MySQL supplied with CamCOPS via
  Docker). This would be unusual, but it's up to you.

Starting CamCOPS
----------------

- Change to the ``server/docker`` directory within the CamCOPS source tree.

  .. todo:: Docker/CamCOPS source: is that the right method?

- Start the containers with:

  .. code-block:: bash

    docker-compose up

  This gives you an interactive view. Press CTRL-C to stop all the containers.

  This form of the command looks for a Docker Compose configuration file with
  a default filename; one called ``docker-compose.yaml`` is provided.

- When you're satisfied everything is working well, you can instead use

  .. code-block:: bash

    docker-compose up -d
    # -d is short for --detach

  and that will fire up the containers in the background.

.. notes:

    # - Use "camcops_server demo_camcops_config --docker" to generate a starting
    #   point config.
    #
    #   *** SSL certificate

    # =============================================================================
    # TO DO:
    # =============================================================================

    # *** ... and when to build database structure/create superuser?
    # *** TCP or Unix socket for the MySQL connection?
    # *** web setup
    # *** ... Gunicorn SSL config


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
  Docker "secrets" require Docker Swarm (not just plain Docker Compose).

- **Data storage.**
  Should data (e.g. MySQL databases) be stored on the host, or in volumes?
  Docker says clearly: volumes. See https://docs.docker.com/storage/volumes/.

- **TCP versus UDS.**
  Currently the connection between CamCOPS and MySQL is via TCP/IP. It would be
  possible to use Unix domain sockets instead. This would be a bit trickier.
  Ordinarily, it would bring some speed advantages; I'm not sure if that
  remains the case between Docker containers.
  The method is to mount a host directory; see
  https://superuser.com/questions/1411402/how-to-expose-linux-socket-file-from-docker-container-mysql-mariadb-etc-to.
  It would add complexity.
