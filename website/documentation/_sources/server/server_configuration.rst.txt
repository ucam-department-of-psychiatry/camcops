..  documentation/source/server/server_configuration.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
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

.. _Apache: http://httpd.apache.org/
.. _CherryPy: https://cherrypy.org/
.. _Gunicorn: http://gunicorn.org/
.. _HTTPS: http://en.wikipedia.org/wiki/HTTP_Secure
.. _Linux: http://en.wikipedia.org/wiki/Linux
.. _MySQL: http://www.mysql.com/
.. _Pyramid: https://trypyramid.com/
.. _Python: https://www.python.org/
.. _Supervisor: http://supervisord.org/
.. _Ubuntu: http://www.ubuntu.com/

.. _server_configuration:

Configuring the server
======================

The majority of CamCOPS configuration takes place via the :ref:`server
configuration file <server_config_file>`. Here, we deal with everything else.


Overview
--------

- CamCOPS will operate offline on your tablet, and you can view simple
  summaries of your tasks there.

- You should set up a server to receive data from your CamCOPS tablet(s).

  - The simplest way (involving only free software) is to set up a Linux_
    (e.g. Ubuntu_) computer with an Apache_ web server and a MySQL_ database
    (plus the Python_ interpreter, which comes with most Linux
    distributions) – collectively known as a LAMP stack [#lamp]_. Alternative
    (e.g. Windows) configurations are possible, but we’ve not used them so do
    not provide details here.

  - You must also obtain an HTTPS_ certificate (or create one for free
    [#snakeoil]_ – not recommended), and configure your web server to do all
    its CamCOPS work via HTTPS only (not HTTP), so that your information is
    always encrypted in transit from the tablets to your server. The CamCOPS
    tablet app will not use unencrypted links. (Where do certificates live on
    disk? See [#linuxflavours]_.)

  - Then, CamCOPS provides software so your web server can receive data from
    your tablets, and offers a :ref:`web front end <website_general>` so you
    can view your tasks in HTML and PDF format, and download data in various
    formats.

  - For very advanced analysis, you can use the MySQL database directly.

  - You must also consider the server’s security carefully; see :ref:`Security
    <security_design>`.

- Having set up your server, you should point your tablet(s) to it (see
  :ref:`configuring the tablet application <configure_client>`).


Data flow
---------

A generic CamCOPS server is arranged like this:

.. image:: images/server_diagram.png

Most servers will use a single database and a single CamCOPS instance, because
this is simpler and more powerful. In that simpler case, ignore all reference
to “instances” in the figure above.

There are two web servers in this diagram.

- The **front-end web server** talks to the “world”. Users connect to it.
  Choose a high-performance web server capable of serving static files.

  - A good choice, regardless of OS, is Apache_.

- The **back-end web server** is bundled with CamCOPS. Its code lives in the
  CamCOPS Python virtual environment. Its job is to serve CamCOPS, and only
  CamCOPS, to an internal TCP/IP port (or UNIX socket). The front-end web
  server then routes appropriate requests through to it. CamCOPS offers a
  choice:

  - Gunicorn_ is probably the best choice for deployment under Linux/UNIX. It’s
    pretty quick. It relies on the UNIX `fork()` function [#fork]_, so it
    doesn’t run under Windows.

  - CherryPy_ is a good cross-platform choice, and definitely the best choice
    under Windows.

  - Pyramid_ is the web framework that CamCOPS uses, and it comes with its own
    demonstration server. This is handy for running the very helpful Pyramid
    debug toolbar [#pyramiddebugtoolbar]_ during testing, but it is definitely
    not a good choice for deployment.


Configure your firewall
-----------------------

Ensure your firewall is configured properly:

- You’ll need to allow HTTPS through, for tablet communications and the web
  viewer. (The default port is 443; see :ref:`TCP/IP ports <tcpip_ports>`. It’s
  possible to use another, but it will confuse users.)

- You’ll probably want remote SSH access, either through the default port (22),
  or a secret port known only to you.

- Other ports are up to you. If you want to run a plain web server as well,
  that’ll normally be on port 80. Access to CamCOPS should only be via HTTPS,
  not plain HTTP.

- Disable access to everything you don’t need.


.. _create_database:


Create a database
-----------------

The method to create a database depends on the database engine you plan to use.
Here’s a method for MySQL to create a database named `camcops`.

First, from the Linux command line, log in to MySQL as root:

.. code-block:: bash

    mysql --host=127.0.0.1 --port=3306 --user=root --password
    # ... or the usual short form: mysql -u root -p

Then in MySQL:

.. code-block:: mysql

    # Create the database:

    CREATE DATABASE camcops;

    # Ideally, create another user that only has access to the CamCOPS database.
    # You should do this, so that you don’t use the root account unnecessarily.

    GRANT ALL PRIVILEGES ON camcops.* TO 'YYYYYY_REPLACE_ME'@'localhost' IDENTIFIED BY 'ZZZZZZ_REPLACE_ME';

    # For future use: if you plan to explore your database directly for analysis,
    # you may want to create a read-only user. Though it may not be ideal (check:
    # are you happy the user can see the audit trail?), you can create a user with
    # read-only access to the entire database like this:

    GRANT SELECT camcops.* TO 'QQQQQQ_REPLACE_ME'@'localhost' IDENTIFIED BY 'PPPPPP_REPLACE_ME';

    # All done. Quit MySQL:

    exit


Create/edit a CamCOPS config file
---------------------------------

See :ref:`“The CamCOPS server configuration file” <server_config_file>`.

The file is typically called `/etc/camcops/camcops.conf` and should be readable
by the web server user, such as `www-data` under Ubuntu [#linuxflavours]_.


Create the database structure
-----------------------------

To create tables and indices, use the command:

.. code-block:: bash

    camcops upgrade_db --config CONFIG

where CONFIG is the filename of your configuration file. If your configuration
file is only readable as `www-data`, you will need to run this with ``sudo``:

.. code-block:: bash

    sudo -u www-data camcops upgrade_db --config CONFIG


Create a superuser
------------------

Use the command:

.. code-block:: bash

    camcops make_superuser --config CONFIG

where CONFIG is the filename of your configuration file. (Again, use ``sudo``
as above if your configuration file requires privileged access to read.)


Start CamCOPS
-------------

Under Linux, this is best done via Supervisor_, which launches programs, keeps
log files for them, and restarts them when the computer is rebooted.

To generate a specimen Supervisor configuration file for CamCOPS, run the
command

.. code-block:: bash

    camcops demo_supervisor_config > my_demo_camcops_supervisor_config.conf

Here's an example, which you would typically save as
`/etc/supervisor/conf.d/camcops.conf`:

.. code-block:: ini

    # =============================================================================
    # Demonstration 'supervisor' config file for CamCOPS.
    # Created by CamCOPS version 2.2.1 at 2018-06-08T18:03:08.640489+01:00.
    # =============================================================================
    # - Supervisor is a system for controlling background processes running on
    #   UNIX-like operating systems. See:
    #       http://supervisord.org
    # - On Ubuntu systems, you would typically install supervisor with
    #       sudo apt install supervisor
    #   and then save this file as
    #       /etc/supervisor/conf.d/camcops.conf
    #
    # - IF YOU EDIT THIS FILE, run:
    #       sudo service supervisor restart
    # - TO MONITOR SUPERVISOR, run:
    #       sudo supervisorctl status
    #   ... or just "sudo supervisorctl" for an interactive prompt.
    #
    # - TO ADD MORE CAMCOPS INSTANCES, first consider whether you wouldn't be
    #   better off just adding groups. If you decide you want a completely new
    #   instance, make a copy of the [program:camcops] section, renaming the copy,
    #   and change the following:
    #   - the --config switch;
    #   - the port or socket;
    #   - the log files.
    #   Then make the main web server point to the copy as well.
    #
    # NOTES ON THE SUPERVISOR CONFIG FILE AND ENVIRONMENT:
    # - Indented lines are treated as continuation (even in commands; no need for
    #   end-of-line backslashes or similar).
    # - The downside of that is that indented comment blocks can join onto your
    #   commands! Beware that.
    # - You can't put quotes around the directory variable
    #   http://stackoverflow.com/questions/10653590
    # - Python programs that are installed within a Python virtual environment
    #   automatically use the virtualenv's copy of Python via their shebang; you do
    #   not need to specify that by hand, nor the PYTHONPATH.
    # - The "environment" setting sets the OS environment. The "--env" parameter
    #   to gunicorn, if you use it, sets the WSGI environment.

    [program:camcops]

    command = /home/rudolf/dev/venvs/camcops/bin/camcops
        serve_gunicorn
        --config /etc/camcops/camcops.conf
        --unix_domain_socket /tmp/.camcops.sock
        --trusted_proxy_headers
            HTTP_X_FORWARDED_HOST
            HTTP_X_FORWARDED_SERVER
            HTTP_X_FORWARDED_PORT
            HTTP_X_FORWARDED_PROTO
            HTTP_X_SCRIPT_NAME

    # To run via a TCP socket, use e.g.:
    #   --host 127.0.0.1 --port 8000
    # To run via a UNIX domain socket, use e.g.
    #   --unix_domain_socket /tmp/.camcops.sock

    directory = /home/rudolf/Documents/code/camcops/server/camcops_server

    environment = MPLCONFIGDIR="/var/cache/camcops/matplotlib"

    # MPLCONFIGDIR specifies a cache directory for matplotlib, which greatly
    # speeds up its subsequent loading.

    user = www-data

    # ... Ubuntu: typically www-data
    # ... CentOS: typically apache

    stdout_logfile = /var/log/supervisor/camcops_out.log
    stderr_logfile = /var/log/supervisor/camcops_err.log

    autostart = true
    autorestart = true
    startsecs = 30
    stopwaitsecs = 60

This is where you choose which back-end web server CamCOPS should use (see
above), by choosing the command you pass to `camcops`. For high-performance
work under Linux, use Gunicorn, with the `serve_gunicorn` command; see the
:ref:`options for the camcops command <camcops_cli>`.

.. _configure_apache:

Point the front-end web server to CamCOPS
-----------------------------------------

Under Linux, a typicaly front-end web server is Apache_.

To generate a specimen Apache configuration file for CamCOPS, run the command

.. code-block:: bash

    camcops demo_apache_config > demo_apache_config_chunk.txt

Here's an example to mount CamCOPS at the URL path `/camcops`, which you would
edit into the Apache config file [#linuxflavours]_:

.. If you re-paste the demo below, make sure you do it from a copy installed
   to /usr/share/camcops, not your user's home directory, otherwise the paths
   will be silly.

.. code-block:: apacheconf

        # Demonstration Apache config file section for CamCOPS.
        # Created by CamCOPS version 2.2.0 at 2018-06-08T19:52:03.221011+01:00.
        #
        # Under Ubuntu, the Apache config will be somewhere in /etc/apache2/
        # Under CentOS, the Apache config will be somewhere in /etc/httpd/
        #
        # This section should go within the <VirtualHost> directive for the secure
        # (SSL, HTTPS) part of the web site.

    <VirtualHost *:443>
        # ...

        # =========================================================================
        # CamCOPS
        # =========================================================================
        # Apache operates on the principle that the first match wins. So, if we
        # want to serve CamCOPS but then override some of its URLs to serve static
        # files faster, we define the static stuff first.

            # ---------------------------------------------------------------------
            # 1. Serve static files
            # ---------------------------------------------------------------------
            # a) offer them at the appropriate URL
            # b) provide permission
            # c) disable ProxyPass for static files

            # Change this: aim the alias at your own institutional logo.

        Alias /camcops/static/logo_local.png /usr/share/camcops/venv/lib/python3.5/site-packages/camcops_server/static/logo_local.png

            # We move from more specific to less specific aliases; the first match
            # takes precedence. (Apache will warn about conflicting aliases if
            # specified in a wrong, less-to-more-specific, order.)

        Alias /camcops/static/ /usr/share/camcops/venv/lib/python3.5/site-packages/camcops_server/static/

        <Directory /usr/share/camcops/venv/lib/python3.5/site-packages/camcops_server/static>
            Require all granted

            # ... for old Apache version (e.g. 2.2), use instead:
            # Order allow,deny
            # Allow from all
        </Directory>

            # Don't ProxyPass the static files; we'll serve them via Apache.

        ProxyPassMatch ^/camcops/static/ !

            # ---------------------------------------------------------------------
            # 2. Proxy requests to the CamCOPS web server and back; allow access
            # ---------------------------------------------------------------------
            # ... either via an internal TCP/IP port (e.g. 1024 or higher, and NOT
            #     accessible to users);
            # ... or, better, via a Unix socket, e.g. /tmp/.camcops.sock
            #
            # NOTES
            # - When you ProxyPass /camcops, you should browse to
            #       https://YOURSITE/camcops
            #   and point your tablet devices to
            #       https://YOURSITE/camcops/database
            # - Don't specify trailing slashes for the ProxyPass and
            #   ProxyPassReverse directives.
            #   If you do, http://host/camcops will fail though
            #              http://host/camcops/ will succeed.
            # - Ensure that you put the CORRECT PROTOCOL (http, https) in the rules
            #   below.
            # - For ProxyPass options, see https://httpd.apache.org/docs/2.2/mod/mod_proxy.html#proxypass
            #   ... including "retry=0" to stop Apache disabling the connection for
            #       a while on failure.
            # - Using a socket
            #   - this requires Apache 2.4.9, and passes after the '|' character a
            #     URL that determines the Host: value of the request; see
            #     https://httpd.apache.org/docs/trunk/mod/mod_proxy.html#proxypass
            # - CamCOPS MUST BE TOLD about its location and protocol, because that
            #   information is critical for synthesizing URLs, but is stripped out
            #   by the reverse proxy system. There are two ways:
            #   (i)  specifying headers or WSGI environment variables, such as
            #        the HTTP(S) headers X-Forwarded-Proto and X-Script-Name below
            #        (CamCOPS is aware of these);
            #   (ii) specifying options to "camcops serve", including
            #           --script_name
            #           --scheme
            #        and optionally
            #           --server
            #
            # So:
            #
            # ~~~~~~~~~~~~~~~~~
            # (a) Reverse proxy
            # ~~~~~~~~~~~~~~~~~
            #
            # PORT METHOD
            # Note the use of "http" (reflecting the backend), not https (like the
            # front end).

        ProxyPass /camcops http://127.0.0.1:8000 retry=0
        ProxyPassReverse /camcops http://127.0.0.1:8000 retry=0

            # UNIX SOCKET METHOD (Apache 2.4.9 and higher)
            #
            # The general syntax is:
            #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|PROTOCOL://HOST/EXTRA_URL_FOR_BACKEND retry=0
            # Note that:
            #   - the protocol should be http, not https (Apache deals with the
            #     HTTPS part and passes HTTP on)
            #   - the EXTRA_URL_FOR_BACKEND needs to be (a) unique for each
            #     instance or Apache will use a single worker for multiple
            #     instances, and (b) blank for the backend's benefit. Since those
            #     two conflict when there's >1 instance, there's a problem.
            #   - Normally, HOST is given as localhost. It may be that this problem
            #     is solved by using a dummy unique value for HOST:
            #     https://bz.apache.org/bugzilla/show_bug.cgi?id=54101#c1
            #
            # If your Apache version is too old, you will get the error
            #   "AH00526: Syntax error on line 56 of /etc/apache2/sites-enabled/SOMETHING:
            #    ProxyPass URL must be absolute!"
            # On Ubuntu, if your Apache is too old, you could use
            #   sudo add-apt-repository ppa:ondrej/apache2
            # ... details at https://launchpad.net/~ondrej/+archive/ubuntu/apache2
            #
            # If you get this error:
            #   AH01146: Ignoring parameter 'retry=0' for worker 'unix:/tmp/.camcops_gunicorn.sock|https://localhost' because of worker sharing
            #   https://wiki.apache.org/httpd/ListOfErrors
            # ... then your URLs are overlapping and should be redone or sorted:
            #   http://httpd.apache.org/docs/2.4/mod/mod_proxy.html#workers
            # The part that must be unique for each instance, with no part a
            # leading substring of any other, is THIS_BIT in:
            #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|https://localhost/THIS_BIT retry=0
            #
            # If you get an error like this:
            #   AH01144: No protocol handler was valid for the URL /SOMEWHERE. If you are using a DSO version of mod_proxy, make sure the proxy submodules are included in the configuration using LoadModule.
            # Then do this:
            #   sudo a2enmod proxy proxy_http
            #   sudo apache2ctl restart
            #
            # If you get an error like this:
            #   ... [proxy_http:error] [pid 32747] (103)Software caused connection abort: [client 109.151.49.173:56898] AH01102: error reading status line from remote server httpd-UDS:0
            #       [proxy:error] [pid 32747] [client 109.151.49.173:56898] AH00898: Error reading from remote server returned by /camcops_bruhl/webview
            # then check you are specifying http://, not https://, in the ProxyPass
            #
            # Other information sources:
            #   https://emptyhammock.com/projects/info/pyweb/webconfig.html

        # ProxyPass /camcops unix:/tmp/.camcops.sock|https://dummy1/ retry=0
        # ProxyPassReverse /camcops unix:/tmp/.camcops.sock|https://dummy1/ retry=0

            # ~~~~~~~~~~~~~~~~~~~~~~~~~
            # (b) Allow proxy over SSL.
            # ~~~~~~~~~~~~~~~~~~~~~~~~~
            # Without this, you will get errors like:
            #   ... SSL Proxy requested for wombat:443 but not enabled [Hint: SSLProxyEngine]
            #   ... failed to enable ssl support for 0.0.0.0:0 (httpd-UDS)

        SSLProxyEngine on

        <Location /camcops>

                # ~~~~~~~~~~~~~~~~
                # (c) Allow access
                # ~~~~~~~~~~~~~~~~

            Require all granted

            # ... for old Apache version (e.g. 2.2), use instead:
            # Order allow,deny
            # Allow from all

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # (d) Tell the proxied application that we are using HTTPS, and
                #     where the application is installed
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #     ... https://stackoverflow.com/questions/16042647
                #
                # EITHER enable mod_headers (e.g. "sudo a2enmod headers") and set:

            RequestHeader set X-Forwarded-Proto https
            RequestHeader set X-Script-Name /camcops

                # and call CamCOPS like:
                #
                # camcops serve_gunicorn \
                #       --config SOMECONFIG \
                #       --trusted_proxy_headers \
                #           HTTP_X_FORWARDED_HOST \
                #           HTTP_X_FORWARDED_SERVER \
                #           HTTP_X_FORWARDED_PORT \
                #           HTTP_X_FORWARDED_PROTO \
                #           HTTP_X_SCRIPT_NAME
                #
                # (X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Server are
                # supplied by Apache automatically)
                #
                # ... OR specify those options by hand in the CamCOPS command.

        </Location>

            # ---------------------------------------------------------------------
            # 3. For additional instances
            # ---------------------------------------------------------------------
            # (a) duplicate section 1 above, editing the base URL and CamCOPS
            #     connection (socket/port);
            # (b) you will also need to create an additional CamCOPS instance,
            #     as above;
            # (c) add additional static aliases (in section 2 above).
            #
            # HOWEVER, consider adding more CamCOPS groups, rather than creating
            # additional instances; the former are *much* easier to administer!


        #==========================================================================
        # SSL security (for HTTPS)
        #==========================================================================

            # You will also need to install your SSL certificate; see the
            # instructions that came with it. You get a certificate by creating a
            # certificate signing request (CSR). You enter some details about your
            # site, and a software tool makes (1) a private key, which you keep
            # utterly private, and (2) a CSR, which you send to a Certificate
            # Authority (CA) for signing. They send back a signed certificate, and
            # a chain of certificates leading from yours to a trusted root CA.
            #
            # You can create your own (a 'snake-oil' certificate), but your tablets
            # and browsers will not trust it, so this is a bad idea.
            #
            # Once you have your certificate: edit and uncomment these lines:

        # SSLEngine on

        # SSLCertificateKeyFile /etc/ssl/private/my.private.key

            # ... a private file that you made before creating the certificate
            # request, and NEVER GAVE TO ANYBODY, and NEVER WILL (or your
            # security is broken and you need a new certificate).

        # SSLCertificateFile /etc/ssl/certs/my.public.cert

            # ... signed and supplied to you by the certificate authority (CA),
            # from the public certificate you sent to them.

        # SSLCertificateChainFile /etc/ssl/certs/my-institution.ca-bundle

            # ... made from additional certificates in a chain, supplied to you by
            # the CA. For example, mine is univcam.ca-bundle, made with the
            # command:
            #
            # cat TERENASSLCA.crt UTNAddTrustServer_CA.crt AddTrustExternalCARoot.crt > univcam.ca-bundle

    </VirtualHost>

Once you are happy with your Apache config file:

- Ensure file ownerships/permissions are correct (including, on CentOS, SELinux
  permissions [#selinux]_).

  - On Ubuntu, if you use `/srv/www` as your `DocumentRoot`, you may need to
    do:

    .. code-block:: bash

        sudo chown -R www-data:www-data /srv/www

  - On CentOS, assuming you use `/var/www` as your `DocumentRoot`, you may need
    to do:

    .. code-block:: bash

        ls -alZ /var/www # shows owners and SELinux security context

        sudo chown -R apache:apache /var/www
        sudo chcon -R -h system_u:object_r:httpd_sys_content_t /var/www
        sudo chown -R apache:apache /etc/camcops
        sudo chcon -R -h system_u:object_r:httpd_sys_content_t /etc/camcops
        sudo chown -R apache:apache /var/cache/camcops
        sudo chcon -R -h system_u:object_r:httpd_sys_content_t /var/cache/camcops
        sudo chown -R apache:apache /usr/share/camcops/server/static
        sudo chcon -R -h system_u:object_r:httpd_sys_content_t /usr/share/camcops/server/static

- Restart Apache: ``sudo apachectl restart``.

- Ensure Apache restarts on boot.

  - On Ubuntu, this should be automatic.
  - On CentOS, run:

    .. code-block:: bash

        sudo chkconfig --level 2345 httpd on

Browse to the web site
-----------------------

If you have configured things correctly, the rest of the configuration should
be possible via the CamCOPS web site.

Assuming you used `/camcops` as the base URL path,

- Browse to `https://YOURHOST/camcops/webview`. This should work.

- Browse to `http://YOURHOST/camcops/webview`. This should *not* work; you
  shouldn’t allow access via plain HTTP.

- Check that a tablet device can register with the server and upload some data
  while using the URL `https://YOURHOST/camcops/database`.


Configure backups
-----------------

Your backup strategy is up to you. However, one option is to use a script to
dump all MySQL databases. A sample script is produced by the command

.. code-block:: bash

    camcops demo_mysql_dump_script

but even better is this tool:

.. code-block:: bash

    camcops_backup_mysql_database

If you use this strategy, you will need to save this script and edit the copy.
Be sure your copy of the script is readable only by root and the backup user,
as it contains a password. You can then run your script regularly from
`/etc/crontab` (see ``man cron``, ``man crontab``).

Obviously, you will also need the dumped files to be backed up to a physically
secure location regularly.

More than one CamCOPS instance
------------------------------

This is simple to set up, but fiddly to maintain. Try to avoid it! Using one
database and :ref:`groups <groups>` is much better. But if you have to:

- Create a second CamCOPS database (from the MySQL command line) as above.

  - **Be careful:** MySQL users are system-wide. So don’t think you can have a
    user named `camcopsmaster` with password X for one database, and a user
    named `camcopsmaster` with password Y for another database; attempting this
    will merely change the password for that (single) user.

- Create a second CamCOPS configuration file, e.g. copying
  `/etc/camcops/camcops.conf` to `/etc/camcops/camcops2.conf` and editing it to
  point to the new database.

- Run ``camcops`` from the command line, pointing it to the new configuration
  file, to create the tables and a superuser (as above).

- Add a second instance to the Apache configuration file and restart Apache.


Database performance tuning
---------------------------

Ignore this section unless you actually have performance problems.

MySQL/InnoDB commit
~~~~~~~~~~~~~~~~~~~

Network latency can be improved considerably by altering the MySQL/InnoDB
log-on-commit behaviour. This is governed by the
`innodb_flush_log_at_trx_commit` variable. The default is 1, which is the
safest; it is required for ACID compliance. However, setting it to 2 makes
database write operations much faster.

This can by done by editing the MySQL configuration file [#linuxflavours]_ to
add this line:

.. code-block:: ini

    [mysqld]

    innodb_flush_log_at_trx_commit = 2

after which you would need to restart MySQL [#linuxflavours]_. Alternatively
you can change it dynamically at the MySQL command line with:

.. code-block:: mysql

    SET GLOBAL innodb_flush_log_at_trx_commit = 2;

    # Use SHOW VARIABLES; to show the current values.


See also:

- http://stackoverflow.com/questions/14121464/mysql-is-slow-with-innodb-during-insert-compared-to-myisam

- http://dev.mysql.com/doc/refman/5.5/en/innodb-parameters.html

Cosmetics
---------

Your institutional logo
~~~~~~~~~~~~~~~~~~~~~~~

Your logos (see the :ref:`configuration file <server_config_file>`) will be
scaled to 45% of the active page width. You may need to add blank space to the
left if they look funny. See picture below.

.. image:: images/scaling_logos.png


.. rubric:: Footnotes

.. [#linuxflavours]
    See :ref:`Linux flavours <linux_flavours>` for a reminder of some common
    differences between Linux operating systems.

.. [#lamp]
    http://en.wikipedia.org/wiki/LAMP_(software_bundle)

.. [#snakeoil]
    This is referred to as creating a “snake oil” certificate. See e.g.
    https://en.wikipedia.org/wiki/Snake_oil_(cryptography);
    http://www.akadia.com/services/ssh_test_certificate.html

.. [#pyramiddebugtoolbar]
    https://docs.pylonsproject.org/projects/pyramid_debugtoolbar/

.. [#fork]
    https://en.wikipedia.org/wiki/Fork_(system_call)

.. [#selinux]
    See http://wiki.apache.org/httpd/13PermissionDenied and
    https://access.redhat.com/site/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Managing_Confined_Services/chap-Managing_Confined_Services-The_Apache_HTTP_Server.html
