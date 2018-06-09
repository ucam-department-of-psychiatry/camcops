..  documentation/source/server/server_command_line.rst

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

.. _server_command_line_tools:

CamCOPS command-line tools
==========================

.. _camcops_cli:

camcops
-------

The ``camcops`` command is the main interface to the CamCOPS server.
Options as of 2018-04-06 (output from ``camcops --allhelp``):

.. code-block:: none

    usage: camcops [-h] [--allhelp] [--version]
                   {docs,demo_camcops_config,demo_supervisor_config,demo_apache_config,demo_mysql_create_db,demo_mysql_dump_script,upgrade_db,show_db_title,merge_db,create_db,make_superuser,reset_password,enable_user,ddl,hl7,show_hl7_queue,show_tests,self_test,serve_pyramid,serve_cherrypy,serve_gunicorn}
                   ...

    CamCOPS server version 2.2.0, by Rudolf Cardinal.
    Use 'camcops <COMMAND> --help' for more detail on each command.

    optional arguments:
      -h, --help            show this help message and exit
      --allhelp             show help for all commands and exit
      --version             show program's version number and exit

    commands:
      Valid CamCOPS commands are as follows.

      {docs,demo_camcops_config,demo_supervisor_config,demo_apache_config,demo_mysql_create_db,demo_mysql_dump_script,upgrade_db,show_db_title,merge_db,create_db,make_superuser,reset_password,enable_user,ddl,hl7,show_hl7_queue,show_tests,self_test,serve_pyramid,serve_cherrypy,serve_gunicorn}
                            Specify one command.
        docs                Launch the main documentation (CamCOPS manual)
        demo_camcops_config
                            Print a demo CamCOPS config file
        demo_supervisor_config
                            Print a demo 'supervisor' config file for CamCOPS
        demo_apache_config  Print a demo Apache config file section for CamCOPS
        demo_mysql_create_db
                            Print demo instructions to create a MySQL database for
                            CamCOPS
        demo_mysql_dump_script
                            Print demo instructions to dump all current MySQL
                            databases
        upgrade_db          Upgrade database to most recent version (via Alembic)
        show_db_title       Show database title
        merge_db            Merge in data from an old or recent CamCOPS database
        create_db           Create CamCOPS database from scratch (AVOID; use the
                            upgrade facility instead)
        make_superuser      Make superuser, or give superuser status to an
                            existing user
        reset_password      Reset a user's password
        enable_user         Re-enable a locked user account
        ddl                 Print database schema (data definition language; DDL)
        hl7                 Send pending HL7 messages and outbound files
        show_hl7_queue      View outbound HL7/file queue (without sending)
        show_tests          Show available self-tests
        self_test           Test internal code
        serve_pyramid       Test web server (single-thread, single-process, HTTP-
                            only, Pyramid; for development use only
        serve_cherrypy      Start web server (via CherryPy)
        serve_gunicorn      Start web server (via Gunicorn) (not available under
                            Windows)

    ===============================================================================
    Help for command 'docs'
    ===============================================================================
    usage: camcops docs [-h] [-v]

    Launch the main documentation (CamCOPS manual)

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_camcops_config'
    ===============================================================================
    usage: camcops demo_camcops_config [-h] [-v]

    Print a demo CamCOPS config file

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_supervisor_config'
    ===============================================================================
    usage: camcops demo_supervisor_config [-h] [-v]

    Print a demo 'supervisor' config file for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_apache_config'
    ===============================================================================
    usage: camcops demo_apache_config [-h] [-v]

    Print a demo Apache config file section for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_mysql_create_db'
    ===============================================================================
    usage: camcops demo_mysql_create_db [-h] [-v]

    Print demo instructions to create a MySQL database for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_mysql_dump_script'
    ===============================================================================
    usage: camcops demo_mysql_dump_script [-h] [-v]

    Print demo instructions to dump all current MySQL databases

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'upgrade_db'
    ===============================================================================
    usage: camcops upgrade_db [-h] [-v] --config CONFIG

    Upgrade database to most recent version (via Alembic)

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)

    required named arguments:
      --config CONFIG  Configuration file (default: None)

    ===============================================================================
    Help for command 'show_db_title'
    ===============================================================================
    usage: camcops show_db_title [-h] [-v] [--config CONFIG]

    Show database title

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'merge_db'
    ===============================================================================
    usage: camcops merge_db [-h] [-v] --config CONFIG
                            [--report_every REPORT_EVERY] [--echo] [--dummy_run]
                            [--info_only] [--skip_hl7_logs] [--skip_audit_logs]
                            [--default_group_id DEFAULT_GROUP_ID]
                            [--default_group_name DEFAULT_GROUP_NAME] --src SRC

    Merge in data from an old or recent CamCOPS database

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --report_every REPORT_EVERY
                            Report progress every n rows (default: 10000)
      --echo                Echo SQL to source database (default: False)
      --dummy_run           Perform a dummy run only; do not alter destination
                            database (default: False)
      --info_only           Show table information only; don't do any work
                            (default: False)
      --skip_hl7_logs       Skip the HL7 message log table (default: False)
      --skip_audit_logs     Skip the audit log table (default: False)
      --default_group_id DEFAULT_GROUP_ID
                            Default group ID (integer) to apply to old records
                            without one. If none is specified, a new group will be
                            created for such records. (default: None)
      --default_group_name DEFAULT_GROUP_NAME
                            If default_group_id is not specified, use this group
                            name. The group will be looked up if it exists, and
                            created if not. (default: None)

    required named arguments:
      --config CONFIG       Configuration file (default: None)
      --src SRC             Source database (specified as an SQLAlchemy URL). The
                            contents of this database will be merged into the
                            database specified in the config file. (default: None)

    ===============================================================================
    Help for command 'create_db'
    ===============================================================================
    usage: camcops create_db [-h] [-v] --config CONFIG --confirm_create_db

    Create CamCOPS database from scratch (AVOID; use the upgrade facility instead)

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)

    required named arguments:
      --config CONFIG      Configuration file (default: None)
      --confirm_create_db  Must specify this too, as a safety measure (default:
                           False)

    ===============================================================================
    Help for command 'make_superuser'
    ===============================================================================
    usage: camcops make_superuser [-h] [-v] [--config CONFIG]
                                  [--username USERNAME]

    Make superuser, or give superuser status to an existing user

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username of superuser to create/promote (if omitted,
                           you will be asked to type it in) (default: None)

    ===============================================================================
    Help for command 'reset_password'
    ===============================================================================
    usage: camcops reset_password [-h] [-v] [--config CONFIG]
                                  [--username USERNAME]

    Reset a user's password

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username to change password for (if omitted, you will
                           be asked to type it in) (default: None)

    ===============================================================================
    Help for command 'enable_user'
    ===============================================================================
    usage: camcops enable_user [-h] [-v] [--config CONFIG] [--username USERNAME]

    Re-enable a locked user account

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username to enable (if omitted, you will be asked to
                           type it in) (default: None)

    ===============================================================================
    Help for command 'ddl'
    ===============================================================================
    usage: camcops ddl [-h] [-v] [--config CONFIG] [--dialect DIALECT]

    Print database schema (data definition language; DDL)

    optional arguments:
      -h, --help         show this help message and exit
      -v, --verbose      Be verbose (default: False)
      --config CONFIG    Configuration file (if not specified, the environment
                         variable CAMCOPS_CONFIG_FILE is checked) (default: None)
      --dialect DIALECT  SQL dialect (options: sybase, postgresql, sqlite, mysql,
                         oracle, mssql, firebird) (default: mysql)

    ===============================================================================
    Help for command 'hl7'
    ===============================================================================
    usage: camcops hl7 [-h] [-v] [--config CONFIG]

    Send pending HL7 messages and outbound files

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'show_hl7_queue'
    ===============================================================================
    usage: camcops show_hl7_queue [-h] [-v] [--config CONFIG]

    View outbound HL7/file queue (without sending)

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'show_tests'
    ===============================================================================
    usage: camcops show_tests [-h] [-v]

    Show available self-tests

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'self_test'
    ===============================================================================
    usage: camcops self_test [-h] [-v]

    Test internal code

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'serve_pyramid'
    ===============================================================================
    usage: camcops serve_pyramid [-h] [-v] [--config CONFIG] [--host HOST]
                                 [--port PORT]
                                 [--trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]]
                                 [--proxy_http_host PROXY_HTTP_HOST]
                                 [--proxy_remote_addr PROXY_REMOTE_ADDR]
                                 [--proxy_script_name PROXY_SCRIPT_NAME]
                                 [--proxy_server_port PROXY_SERVER_PORT]
                                 [--proxy_server_name PROXY_SERVER_NAME]
                                 [--proxy_url_scheme PROXY_URL_SCHEME]
                                 [--proxy_rewrite_path_info]
                                 [--debug_reverse_proxy] [--debug_toolbar]

    Test web server (single-thread, single-process, HTTP-only, Pyramid; for
    development use only

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --host HOST           Hostname to listen on (default: 127.0.0.1)
      --port PORT           Port to listen on (default: 8000)
      --trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]
                            Trust these WSGI environment variables for when the
                            server is behind a reverse proxy (e.g. an Apache
                            front-end web server). Options: ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
                            'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP',
                            'HTTP_X_FORWARDED_PROTO', 'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS', 'HTTP_X_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SERVER'] (default: None)
      --proxy_http_host PROXY_HTTP_HOST
                            Option to set the WSGI HTTP host directly. This
                            affects the WSGI variable HTTP_HOST. If not specified,
                            trusted variables within ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST'] will be used. (default: None)
      --proxy_remote_addr PROXY_REMOTE_ADDR
                            Option to set the WSGI remote address directly. This
                            affects the WSGI variable REMOTE_ADDR. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP'] will be
                            used. (default: None)
      --proxy_script_name PROXY_SCRIPT_NAME
                            Path at which this script is mounted. Set this if you
                            are hosting this CamCOPS instance at a non-root path,
                            unless you set trusted WSGI headers instead. For
                            example, if you are running an Apache server and want
                            this instance of CamCOPS to appear at
                            /somewhere/camcops, then (a) configure your Apache
                            instance to proxy requests to /somewhere/camcops/...
                            to this server (e.g. via an internal TCP/IP port or
                            UNIX socket) and specify this option. If this option
                            is not set, then the OS environment variable
                            SCRIPT_NAME will be checked as well, and if that is
                            not set, trusted variables within
                            ['HTTP_X_SCRIPT_NAME', 'HTTP_X_FORWARDED_SCRIPT_NAME']
                            will be used. This option affects the WSGI variables
                            SCRIPT_NAME and PATH_INFO. (default: None)
      --proxy_server_port PROXY_SERVER_PORT
                            Option to set the WSGI server port directly. This
                            affects the WSGI variable SERVER_PORT. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_PORT'] will be used. (default:
                            None)
      --proxy_server_name PROXY_SERVER_NAME
                            Option to set the WSGI server name directly. This
                            affects the WSGI variable SERVER_NAME. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_SERVER'] will be used. (default:
                            None)
      --proxy_url_scheme PROXY_URL_SCHEME
                            Option to set the WSGI scheme (e.g. http, https)
                            directly. This affects the WSGI variable
                            wsgi.url_scheme. If not specified, trusted variables
                            within ['HTTP_X_FORWARDED_PROTO',
                            'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS'] will be used. (default: None)
      --proxy_rewrite_path_info
                            If SCRIPT_NAME is rewritten, this option causes
                            PATH_INFO to be rewritten, if it starts with
                            SCRIPT_NAME, to strip off SCRIPT_NAME. Appropriate for
                            some front-end web browsers with limited reverse
                            proxying support (but do not use for Apache with
                            ProxyPass, because that rewrites incoming URLs
                            properly). (default: False)
      --debug_reverse_proxy
                            For --behind_reverse_proxy: show debugging information
                            as WSGI variables are rewritten. (default: False)
      --debug_toolbar       Enable the Pyramid debug toolbar (default: False)

    ===============================================================================
    Help for command 'serve_cherrypy'
    ===============================================================================
    usage: camcops serve_cherrypy [-h] [-v] [--config CONFIG] [--serve]
                                  [--host HOST] [--port PORT]
                                  [--unix_domain_socket UNIX_DOMAIN_SOCKET]
                                  [--server_name SERVER_NAME]
                                  [--threads_start THREADS_START]
                                  [--threads_max THREADS_MAX]
                                  [--ssl_certificate SSL_CERTIFICATE]
                                  [--ssl_private_key SSL_PRIVATE_KEY]
                                  [--log_screen] [--no_log_screen]
                                  [--root_path ROOT_PATH]
                                  [--trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]]
                                  [--proxy_http_host PROXY_HTTP_HOST]
                                  [--proxy_remote_addr PROXY_REMOTE_ADDR]
                                  [--proxy_script_name PROXY_SCRIPT_NAME]
                                  [--proxy_server_port PROXY_SERVER_PORT]
                                  [--proxy_server_name PROXY_SERVER_NAME]
                                  [--proxy_url_scheme PROXY_URL_SCHEME]
                                  [--proxy_rewrite_path_info]
                                  [--debug_reverse_proxy] [--debug_toolbar]

    Start web server (via CherryPy)

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --serve
      --host HOST           hostname to listen on (default: 127.0.0.1)
      --port PORT           port to listen on (default: 8000)
      --unix_domain_socket UNIX_DOMAIN_SOCKET
                            UNIX domain socket to listen on (overrides host/port
                            if specified) (default: )
      --server_name SERVER_NAME
                            CherryPy's SERVER_NAME environ entry (default:
                            localhost)
      --threads_start THREADS_START
                            Number of threads for server to start with (default:
                            10)
      --threads_max THREADS_MAX
                            Maximum number of threads for server to use (-1 for no
                            limit) (BEWARE exceeding the permitted number of
                            database connections) (default: 100)
      --ssl_certificate SSL_CERTIFICATE
                            SSL certificate file (e.g. /etc/ssl/certs/ssl-cert-
                            snakeoil.pem) (default: None)
      --ssl_private_key SSL_PRIVATE_KEY
                            SSL private key file (e.g. /etc/ssl/private/ssl-cert-
                            snakeoil.key) (default: None)
      --log_screen          Log access requests etc. to terminal (default)
                            (default: True)
      --no_log_screen       Don't log access requests etc. to terminal (default:
                            True)
      --root_path ROOT_PATH
                            Root path to serve CRATE at, WITHIN this CherryPy web
                            server instance. (There is unlikely to be a reason to
                            use something other than '/'; do not confuse this with
                            the mount point within a wider, e.g. Apache,
                            configuration, which is set instead by the WSGI
                            variable SCRIPT_NAME; see the --trusted_proxy_headers
                            and --proxy_script_name options.) (default: /)
      --trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]
                            Trust these WSGI environment variables for when the
                            server is behind a reverse proxy (e.g. an Apache
                            front-end web server). Options: ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
                            'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP',
                            'HTTP_X_FORWARDED_PROTO', 'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS', 'HTTP_X_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SERVER'] (default: None)
      --proxy_http_host PROXY_HTTP_HOST
                            Option to set the WSGI HTTP host directly. This
                            affects the WSGI variable HTTP_HOST. If not specified,
                            trusted variables within ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST'] will be used. (default: None)
      --proxy_remote_addr PROXY_REMOTE_ADDR
                            Option to set the WSGI remote address directly. This
                            affects the WSGI variable REMOTE_ADDR. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP'] will be
                            used. (default: None)
      --proxy_script_name PROXY_SCRIPT_NAME
                            Path at which this script is mounted. Set this if you
                            are hosting this CamCOPS instance at a non-root path,
                            unless you set trusted WSGI headers instead. For
                            example, if you are running an Apache server and want
                            this instance of CamCOPS to appear at
                            /somewhere/camcops, then (a) configure your Apache
                            instance to proxy requests to /somewhere/camcops/...
                            to this server (e.g. via an internal TCP/IP port or
                            UNIX socket) and specify this option. If this option
                            is not set, then the OS environment variable
                            SCRIPT_NAME will be checked as well, and if that is
                            not set, trusted variables within
                            ['HTTP_X_SCRIPT_NAME', 'HTTP_X_FORWARDED_SCRIPT_NAME']
                            will be used. This option affects the WSGI variables
                            SCRIPT_NAME and PATH_INFO. (default: None)
      --proxy_server_port PROXY_SERVER_PORT
                            Option to set the WSGI server port directly. This
                            affects the WSGI variable SERVER_PORT. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_PORT'] will be used. (default:
                            None)
      --proxy_server_name PROXY_SERVER_NAME
                            Option to set the WSGI server name directly. This
                            affects the WSGI variable SERVER_NAME. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_SERVER'] will be used. (default:
                            None)
      --proxy_url_scheme PROXY_URL_SCHEME
                            Option to set the WSGI scheme (e.g. http, https)
                            directly. This affects the WSGI variable
                            wsgi.url_scheme. If not specified, trusted variables
                            within ['HTTP_X_FORWARDED_PROTO',
                            'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS'] will be used. (default: None)
      --proxy_rewrite_path_info
                            If SCRIPT_NAME is rewritten, this option causes
                            PATH_INFO to be rewritten, if it starts with
                            SCRIPT_NAME, to strip off SCRIPT_NAME. Appropriate for
                            some front-end web browsers with limited reverse
                            proxying support (but do not use for Apache with
                            ProxyPass, because that rewrites incoming URLs
                            properly). (default: False)
      --debug_reverse_proxy
                            For --behind_reverse_proxy: show debugging information
                            as WSGI variables are rewritten. (default: False)
      --debug_toolbar       Enable the Pyramid debug toolbar (default: False)

    ===============================================================================
    Help for command 'serve_gunicorn'
    ===============================================================================
    usage: camcops serve_gunicorn [-h] [-v] [--config CONFIG] [--serve]
                                  [--host HOST] [--port PORT]
                                  [--unix_domain_socket UNIX_DOMAIN_SOCKET]
                                  [--num_workers NUM_WORKERS] [--debug_reload]
                                  [--ssl_certificate SSL_CERTIFICATE]
                                  [--ssl_private_key SSL_PRIVATE_KEY]
                                  [--timeout TIMEOUT]
                                  [--debug_show_gunicorn_options]
                                  [--trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]]
                                  [--proxy_http_host PROXY_HTTP_HOST]
                                  [--proxy_remote_addr PROXY_REMOTE_ADDR]
                                  [--proxy_script_name PROXY_SCRIPT_NAME]
                                  [--proxy_server_port PROXY_SERVER_PORT]
                                  [--proxy_server_name PROXY_SERVER_NAME]
                                  [--proxy_url_scheme PROXY_URL_SCHEME]
                                  [--proxy_rewrite_path_info]
                                  [--debug_reverse_proxy] [--debug_toolbar]

    Start web server (via Gunicorn) (not available under Windows)

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --serve
      --host HOST           hostname to listen on (default: 127.0.0.1)
      --port PORT           port to listen on (default: 8000)
      --unix_domain_socket UNIX_DOMAIN_SOCKET
                            UNIX domain socket to listen on (overrides host/port
                            if specified) (default: )
      --num_workers NUM_WORKERS
                            Number of worker processes for server to use (default:
                            16)
      --debug_reload        Debugging option: reload Gunicorn upon code change
                            (default: False)
      --ssl_certificate SSL_CERTIFICATE
                            SSL certificate file (e.g. /etc/ssl/certs/ssl-cert-
                            snakeoil.pem) (default: None)
      --ssl_private_key SSL_PRIVATE_KEY
                            SSL private key file (e.g. /etc/ssl/private/ssl-cert-
                            snakeoil.key) (default: None)
      --timeout TIMEOUT     Gunicorn worker timeout (s) (default: 30)
      --debug_show_gunicorn_options
                            Debugging option: show possible Gunicorn settings
                            (default: False)
      --trusted_proxy_headers [TRUSTED_PROXY_HEADERS [TRUSTED_PROXY_HEADERS ...]]
                            Trust these WSGI environment variables for when the
                            server is behind a reverse proxy (e.g. an Apache
                            front-end web server). Options: ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
                            'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP',
                            'HTTP_X_FORWARDED_PROTO', 'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS', 'HTTP_X_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SCRIPT_NAME',
                            'HTTP_X_FORWARDED_SERVER'] (default: None)
      --proxy_http_host PROXY_HTTP_HOST
                            Option to set the WSGI HTTP host directly. This
                            affects the WSGI variable HTTP_HOST. If not specified,
                            trusted variables within ['HTTP_X_HOST',
                            'HTTP_X_FORWARDED_HOST'] will be used. (default: None)
      --proxy_remote_addr PROXY_REMOTE_ADDR
                            Option to set the WSGI remote address directly. This
                            affects the WSGI variable REMOTE_ADDR. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP'] will be
                            used. (default: None)
      --proxy_script_name PROXY_SCRIPT_NAME
                            Path at which this script is mounted. Set this if you
                            are hosting this CamCOPS instance at a non-root path,
                            unless you set trusted WSGI headers instead. For
                            example, if you are running an Apache server and want
                            this instance of CamCOPS to appear at
                            /somewhere/camcops, then (a) configure your Apache
                            instance to proxy requests to /somewhere/camcops/...
                            to this server (e.g. via an internal TCP/IP port or
                            UNIX socket) and specify this option. If this option
                            is not set, then the OS environment variable
                            SCRIPT_NAME will be checked as well, and if that is
                            not set, trusted variables within
                            ['HTTP_X_SCRIPT_NAME', 'HTTP_X_FORWARDED_SCRIPT_NAME']
                            will be used. This option affects the WSGI variables
                            SCRIPT_NAME and PATH_INFO. (default: None)
      --proxy_server_port PROXY_SERVER_PORT
                            Option to set the WSGI server port directly. This
                            affects the WSGI variable SERVER_PORT. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_PORT'] will be used. (default:
                            None)
      --proxy_server_name PROXY_SERVER_NAME
                            Option to set the WSGI server name directly. This
                            affects the WSGI variable SERVER_NAME. If not
                            specified, trusted variables within
                            ['HTTP_X_FORWARDED_SERVER'] will be used. (default:
                            None)
      --proxy_url_scheme PROXY_URL_SCHEME
                            Option to set the WSGI scheme (e.g. http, https)
                            directly. This affects the WSGI variable
                            wsgi.url_scheme. If not specified, trusted variables
                            within ['HTTP_X_FORWARDED_PROTO',
                            'HTTP_X_FORWARDED_PROTOCOL',
                            'HTTP_X_FORWARDED_SCHEME', 'HTTP_X_SCHEME',
                            'HTTP_X_FORWARDED_HTTPS', 'HTTP_X_FORWARDED_SSL',
                            'HTTP_X_HTTPS'] will be used. (default: None)
      --proxy_rewrite_path_info
                            If SCRIPT_NAME is rewritten, this option causes
                            PATH_INFO to be rewritten, if it starts with
                            SCRIPT_NAME, to strip off SCRIPT_NAME. Appropriate for
                            some front-end web browsers with limited reverse
                            proxying support (but do not use for Apache with
                            ProxyPass, because that rewrites incoming URLs
                            properly). (default: False)
      --debug_reverse_proxy
                            For --behind_reverse_proxy: show debugging information
                            as WSGI variables are rewritten. (default: False)
      --debug_toolbar       Enable the Pyramid debug toolbar (default: False)


.. _camcops_meta:

camcops_meta
------------

The ``camcops_meta`` tool allows you to run CamCOPS over multiple CamCOPS
configuration files/databases. It’s less useful than it was, because the
dominant mode of “one database per research group” has been replaced by the
concept of “a single database with group-level security”.

Options as of 2017-10-23:

.. code-block:: none

    usage: camcops_meta [-h] --filespecs FILESPECS [FILESPECS ...]
                        [--ccargs [CCARGS [CCARGS ...]]] [--python PYTHON]
                        [--camcops CAMCOPS] [-d] [-v]
                        cc_command

    Run commands across multiple CamCOPS databases

    positional arguments:
      cc_command            Main command to pass to CamCOPS

    optional arguments:
      -h, --help            show this help message and exit
      --filespecs FILESPECS [FILESPECS ...]
                            List of CamCOPS config files (wildcards OK)
      --ccargs [CCARGS [CCARGS ...]]
                            List of CamCOPS arguments, to which '--' will be
                            prefixed
      --python PYTHON       Python interpreter (default:
                            /home/rudolf/dev/venvs/camcops/bin/python3)
      --camcops CAMCOPS     CamCOPS executable (default:
                            /home/rudolf/Documents/code/camcops/server/camcops.py)
      -d, --dummyrun        Dummy run (show filenames only)
      -v, --verbose         Verbose


camcops_backup_mysql_database
-----------------------------

This simple tool uses MySQL to dump a MySQL database to a .SQL file (from which
you can restore it), and names the file according to the name of the database
plus a timestamp.

Options as of 2017-10-23:

.. code-block:: none

    usage: camcops_backup_mysql_database [-h]
                                         [--max_allowed_packet MAX_ALLOWED_PACKET]
                                         [--mysqldump MYSQLDUMP]
                                         [--username USERNAME]
                                         [--password PASSWORD]
                                         [--with_drop_create_database] [--verbose]
                                         databases [databases ...]

    Back up a specific MySQL database

    positional arguments:
      databases             Database(s) to back up

    optional arguments:
      -h, --help            show this help message and exit
      --max_allowed_packet MAX_ALLOWED_PACKET
                            Maximum size of buffer (default: 1GB)
      --mysqldump MYSQLDUMP
                            mysqldump executable (default: mysqldump)
      --username USERNAME   MySQL user (default: root)
      --password PASSWORD   MySQL password (AVOID THIS OPTION IF POSSIBLE; VERY
                            INSECURE; VISIBLE TO OTHER PROCESSES; if you don't use
                            it, you'll be prompted for the password) (default:
                            root)
      --with_drop_create_database
                            Include DROP DATABASE and CREATE DATABASE commands
                            (default: False)
      --verbose             Verbose output (default: False)
