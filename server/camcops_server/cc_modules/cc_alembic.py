#!/usr/bin/env python
# camcops_server/cc_modules/cc_alembic.py

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

Functions to talk to Alembic; specifically, those functions that may be used
by users/administrators, such as to upgrade a database.

If you're a developer and want to create a new database migration, see instead

    tools/create_database_migration.py

"""

import logging
from typing import TYPE_CHECKING
import os

from alembic import command
from alembic.config import Config
from cardinal_pythonlib.fileops import preserve_cwd
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.alembic_func import (
    get_current_and_head_revision,
    upgrade_database,
)

from .cc_baseconstants import ALEMBIC_BASE_DIR, ALEMBIC_CONFIG_FILENAME
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import MetaData
    from .cc_config import CamcopsConfig

log = BraceStyleAdapter(logging.getLogger(__name__))


def import_all_models():
    from .cc_all_models import all_models_no_op
    all_models_no_op()  # to suppress "Unused import statement"


def upgrade_database_to_head() -> None:
    """
    The primary upgrade method.
    """
    import_all_models()  # delayed, for command-line interfaces
    upgrade_database(alembic_base_dir=ALEMBIC_BASE_DIR,
                     alembic_config_filename=ALEMBIC_CONFIG_FILENAME)
    # ... will get its config information from the OS environment; see
    # run_alembic() in alembic/env.py


@preserve_cwd
def create_database_from_scratch(cfg: "CamcopsConfig") -> None:
    """
    Takes the database from nothing to the "head" revision in one step, by
    bypassing Alembic's revisions and taking the state directly from the
    SQLAlchemy ORM metadata.

    See
        http://alembic.zzzcomputing.com/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch  # noqa

    This ASSUMES that the head revision "frozen" into the latest
    alembic/version/XXX.py file MATCHES THE STATE OF THE SQLALCHEMY ORM
    METADATA as judged by Base.metadata. If that's not the case, things will go
    awry later! (Alembic will think the database is at the state of its "head"
    revision, but it won't be.)

    It also ASSUMES (as many things do) that importing .cc_all_models imports
    all the models (or Base.metadata will be incomplete).
    """
    import_all_models()  # delayed, for command-line interfaces

    log.warning("Performing one-step database creation.")
    metadata = Base.metadata  # type: MetaData
    engine = cfg.create_sqla_engine()
    metadata.create_all(engine)

    alembic_cfg = Config(ALEMBIC_CONFIG_FILENAME)
    os.chdir(ALEMBIC_BASE_DIR)
    command.stamp(alembic_cfg, "head")
    log.info("One-step database creation complete.")


@preserve_cwd
def assert_database_is_at_head(cfg: "CamcopsConfig") -> None:
    current, head = get_current_and_head_revision(
        database_url=cfg.db_url,
        alembic_config_filename=ALEMBIC_CONFIG_FILENAME,
        alembic_base_dir=ALEMBIC_BASE_DIR,
    )
    if current == head:
        log.debug("Database is at correct (head) revision of {}", current)
    else:
        msg = (
            "Database structure is at version {} but should be at version {}. "
            "CamCOPS will not start. Please use the 'upgrade_db' command to "
            "fix this.".format(current, head))
        log.critical(msg)
        raise RuntimeError(msg)
