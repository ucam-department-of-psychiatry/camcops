#!/usr/bin/env python
# camcops_server/alembic/env.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================
"""

# =============================================================================
# Imports
# =============================================================================

import logging

from alembic import context
from alembic.config import Config
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_url
from sqlalchemy import engine_from_config, pool
from sqlalchemy.sql.schema import MetaData

# No relative imports from within the Alembic zone.
from camcops_server.cc_modules.cc_baseconstants import ALEMBIC_VERSION_TABLE
from camcops_server.cc_modules.cc_config import get_default_config_from_os_env
from camcops_server.cc_modules.cc_sqlalchemy import Base
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Migration functions
# =============================================================================

def run_migrations_offline(config: Config,
                           target_metadata: MetaData) -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well.  By skipping the Engine creation we
    don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    # RNC
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_as_batch=True,  # for SQLite mode; http://stackoverflow.com/questions/30378233  # noqa
        literal_binds=True,
        version_table=ALEMBIC_VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(config: Config,
                          target_metadata: MetaData) -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # RNC
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # for SQLite mode; http://stackoverflow.com/questions/30378233  # noqa
            version_table=ALEMBIC_VERSION_TABLE,
        )
        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# Main commands
# =============================================================================
# We're in a pseudo-"main" environment.
# We need to reconfigure our logger, but __name__ is not "__main__".

def run_alembic() -> None:
    alembic_config = context.config  # type: Config
    target_metadata = Base.metadata
    camcops_config = get_default_config_from_os_env()
    dburl = camcops_config.db_url
    alembic_config.set_main_option('sqlalchemy.url', dburl)
    log.warning("Applying migrations to database at URL: {}",
                get_safe_url_from_url(dburl))

    if context.is_offline_mode():
        run_migrations_offline(alembic_config, target_metadata)
    else:
        run_migrations_online(alembic_config, target_metadata)


main_only_quicksetup_rootlogger(level=logging.DEBUG)
# log.critical("IN CAMCOPS MIGRATION SCRIPT env.py")
run_alembic()
