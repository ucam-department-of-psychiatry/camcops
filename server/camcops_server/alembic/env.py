#!/usr/bin/env python
# camcops_server/alembic/env.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

import logging

from alembic import context
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from sqlalchemy import engine_from_config, pool

# No relative imports from within the Alembic zone.
from camcops_server.cc_modules.cc_sqlalchemy import Base
from starfeeder.settings import get_database_settings

log = logging.getLogger(__name__)
main_only_quicksetup_rootlogger(level=logging.DEBUG)

config = context.config
target_metadata = Base.metadata
settings = get_database_settings()
config.set_main_option('sqlalchemy.url', settings['url'])


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    # RNC
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_as_batch=True,  # for SQLite mode; http://stackoverflow.com/questions/30378233  # noqa
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

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
        )
        with context.begin_transaction():
            context.run_migrations()


# We're in a pseudo-"main" environment.
# We need to reconfigure our logger, but __name__ is not "__main__".
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
