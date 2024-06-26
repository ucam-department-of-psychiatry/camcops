..  docs/source/administrator/linux_flavours.rst

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

.. _linux_flavours:

Linux flavours
==============

..  contents::
    :local:
    :depth: 3


Common administrative commands
------------------------------

.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * -
     - Ubuntu
     - CentOS 6.5

   * - **System**
     -
     -

   * - Heritage
     - Debian
     - Red Hat Enterprise Linux

   * - Package management
     - ``apt-get``, ``dpkg``, and for convenience ``gdebi``
     - ``yum``

   * - General system update
     - ``sudo apt-get update && sudo apt-get dist-upgrade``
     - ``sudo yum update``

   * - Package type
     - ``deb``
     - ``rpm``

   * - Extra security
     - Nothing complex by default
     - SELinux; file permissions must be set with ``chcon``

   * - Autostarting daemons at boot
     - Usually happens automatically
     - Usually need to configure with ``chkconfig``

   * - Which OS version am I running?
     - | ``lsb_release -a``
       | ``uname -a``
     - | ``cat /etc/centos-release``
       | ``uname -a``

   * - **Python**
     -
     -

   * - Default Python versions (CamCOPS requires 3.4)
     - 2.7, 3.4
     - 2.6

   * - **Apache**
     -
     -

   * - Apache main configuration file
     - Usually ``/etc/apache2/apache2.conf``
     - Usually ``/etc/httpd/conf/httpd.conf``

   * - Apache SSL configuration file
     - Usually ``/etc/apache2/sites-available/default-ssl``
     - Usually ``/etc/httpd/conf.d/ssl.conf``

   * - Granting access in Apache config file
     - | **Apache 2.4:**
       | ``Require all granted``
     - | **Apache 2.2:**
       | ``Order allow,deny``
       | ``Allow from all``

   * - Default Apache system user
     - ``www-data``
     - ``apache``

   * - Default SSL certificate location
     - ``/etc/ssl/``
     - ``/etc/pki/tls/``

   * - Default Apache log directory
     - ``/var/log/apache2/``
     - ``/var/log/httpd/``

   * - Restarting Apache
     - - ``sudo service apache2 [start|stop|restart]``
       - ``sudo apache2ctl [start|stop|restart]``
       - ``sudo apachectl [start|stop|restart]``
     - - ``sudo service httpd [start|stop|restart]``
       - ``sudo apachectl [start|stop|restart]``

   * - **supervisord**
     -
     -

   * - supervisord configuration file
     - Usually ``/etc/supervisor/supervisord.conf``
     - Usually ``/etc/supervisord.conf``

   * - Restarting supervisord
     - - ``sudo service supervisor [start|stop|restart]``
       - ``sudo supervisorctl``
     - - ``sudo service supervisord [start|stop|restart]``
       - ``sudo supervisorctl``

   * - **MySQL**
     -
     -

   * - Default MySQL configuration file
     - ``/etc/mysql/my.cnf``
     - ``/etc/my.cnf``

   * - Restarting MySQL
     - ``sudo service mysql [start|stop|restart]``
     - ``sudo service mysqld [start|stop|restart]``

   * - Default MySQL log
     - ``/var/log/mysql.log``
     - ``/var/log/mysqld.log``

   * - **CamCOPS packages**
     -
     -

   * - Installation
     - ``sudo gdebi install camcops_VERSION_all.deb``
     - ``sudo yum install camcops_VERSION.noarch.rpm``

   * - Removal
     - ``sudo dpkg --remove camcops``
     - ``sudo yum remove camcops``


.. _rhel86_prerequisites:

Installing CamCOPS prerequisites under RHEL 8.6
-----------------------------------------------

Probably also applicable to CentOS 8.x.

Ensure additional repositories are in use:

* EPEL: see e.g. http://fedoraproject.org/wiki/EPEL
* Erlang: see e.g. https://computingforgeeks.com/how-to-install-latest-erlang-on-rhel-8/
* RabbitMQ: see e.g. https://computingforgeeks.com/how-to-install-rabbitmq-on-rhel-8/

If accessing the internet through a proxy, where the ``https_proxy`` environment variable is defined, use: ``sudo -E`` to pass the environment to the superuser.

If ``/tmp`` has been securely mounted as ``noexec`` you will need to remount it
as ``exec``. Remove the ``noexec`` option from ``/etc/fstab`` and ``sudo
mount -o remount /tmp``. This will allow ``alien`` to execute scripts under
``/tmp``. Otherwise you will get errors like ``/var/tmp/rpm-tmp.AbCDef: line 96:
/tmp/alien.nnnnnnn/script: Permission denied`` when installing the package. You
can remount ``/tmp``as ``noexec`` again after installation.


Potential prerequisites for what follows:

.. code-block:: bash

    sudo dnf -y install python38 python38-devel python3-pip httpd mariadb-devel mod_ssl
    sudo update-alternatives --config python3


.. _linux_mysql_setup:

Setting up MySQL under Linux
----------------------------

#. **Under Ubuntu, if you are happy to leave the data files at their default
   location, skip this step.** Check/edit the MySQL configuration (see table
   above for filenames). See `Getting Started with MySQL
   <http://dev.mysql.com/tech-resources/articles/mysql_intro.html>`_. In
   particular:

   - `datadir` should point to your database files (default often
     `/var/lib/mysql`, but `/srv/mysql` is one alternative).

   - Other options are explained `here
     <http://dev.mysql.com/doc/mysql/en/server-system-variables.html>`_.

   - If you create a blank directory (such as `/srv/mysql`), you will need to
     use the `mysql_install_db` tool; see `Postinstallation Setup and Testing
     <http://dev.mysql.com/doc/refman/5.7/en/postinstallation.html>`_; an
     example command is

     .. code-block:: bash

        sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/srv/mysql

   - Manual start: `sudo /usr/bin/mysqld_safe --user=mysql &`. Manual stop:
     `sudo mysqladmin shutdown`.

   - Service start/stop: see table above.

   - If it starts manually but not as a service (in a manner that depends on
     your data directory), you have a challenging problem; an option is to
     return to the default data directory!

   - To log in prior to securing the database: mysql.

   - See also the `CentOS MySQL installation guide
     <http://centoshelp.org/servers/database/installing-configuring-mysql-server/>`_.

   - Default logfile: `/var/log/mysqld.log` or `/var/log/mysql/...`

#. Secure your MySQL installation by running `mysql_secure_installation`.

   - Login after securing: `mysql -u root -p`.

   - Similar username/password requirements now apply to manual shutdowns.

#. **Ensure that the max_allowed_packet parameter is large enough.**

   - This parameter needs to be set large enough that the largest binary large
     objects (BLOBs) can be uploaded. CamCOPS BLOBs are mostly photographs from
     tablets. A high-end tablet in 2014 might have an 8 megapixel (MP) camera,
     with each pixel taking 3 bytes, i.e. 24 Mb. Furthermore, the transfer
     takes more space thanks to somewhat inefficient encoding. The MySQL
     server default value is just 1 Mb [#mysqlmaxallowedpacket]_.

   - You must set this parameter for the server, and for the `mysqldump` tool.

   - A suggested value is 32 Mb. Edit `my.cnf` to include `max_allowed_packet`
     values in the `[mysqld]` and `[mysqldump]` sections (creating them if
     necessary).

   - Similar editing of the `[client]` section of `my.cnf` is unnecessary,
     firstly because some other MySQL clients may not recognize the option and
     might choke on it, and secondly because CamCOPS uses `MySQLdb <http://mysql-python.sourceforge.net/>`_
     (`MySQL-Python <http://mysql-python.sourceforge.net/>`_), which uses the MySQL C API, which has a default limit of 1
     Gb [#mysqlcapilimits]_.

#. Set some other MySQL parameters for TEXT-heavy tables; see
   :ref:`Troubleshooting: Row size too large <mysql_row_size_too_large>`.

#. Thus, edit `my.cnf` to include the following:

   .. code-block:: ini

        [mysqld]
        max_allowed_packet = 32M

        innodb_strict_mode = 1
        innodb_file_per_table = 1
        innodb_file_format = Barracuda

        # Only for MySQL prior to 5.7.5 (http://dev.mysql.com/doc/relnotes/mysql/5.6/en/news-5-6-20.html):
        # innodb_log_file_size = 512M

        [mysqldump]
        max_allowed_packet = 32M

#. Ensure MySQL is running as a service (as above).

#. **Create the CamCOPS database.** See :ref:`create a database
   <create_database>`.


===============================================================================

.. rubric:: Footnotes

.. [#mysqlmaxallowedpacket]
    http://dev.mysql.com/doc/refman/5.7/en/packet-too-large.html

.. [#mysqlcapilimits]
    http://dev.mysql.com/doc/refman/5.7/en/c-api.html
