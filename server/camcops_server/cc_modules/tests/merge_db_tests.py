"""
camcops_server/cc_modules/tests/merge_db_tests.py

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
"""

from configparser import ConfigParser
from dataclasses import dataclass, replace
from io import StringIO
import logging
import os.path
from tempfile import TemporaryDirectory
from typing import Any, Dict
from unittest import TestCase

from cardinal_pythonlib.classes import all_subclasses
from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.sqlalchemy.session import make_sqlite_url
from sqlalchemy.orm.session import Session, sessionmaker

from camcops_server.cc_modules.cc_alembic import (
    create_database_from_scratch,
    upgrade_database_to_head,
)
from camcops_server.cc_modules.cc_config import CamcopsConfig, get_demo_config
from camcops_server.cc_modules.cc_constants import (
    CONFIG_FILE_SITE_SECTION,
    ConfigParamSite,
)
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_testfactories import (
    BaseFactory,
    GroupFactory,
    ID_OFFSET,
    NHSIdNumDefinitionFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    RioIdNumDefinitionFactory,
    RioPatientIdNumFactory,
)
from camcops_server.cc_modules.merge_db import merge_camcops_db
from camcops_server.cc_modules.cc_unittest import DEMO_PNG_BYTES
from camcops_server.tasks.tests import factories as task_factories

log = logging.getLogger(__name__)


# =============================================================================
# Unit testing
# =============================================================================


@dataclass
class MergeTestDbInfo:
    nhs_which_idnum: int
    nhs_desc: str
    nhs_shortdesc: str
    rio_which_idnum: int
    rio_desc: str
    rio_shortdesc: str


class MergeDbTests(TestCase):
    @staticmethod
    def _get_config(dburl: str) -> CamcopsConfig:
        base_cfg_txt = get_demo_config()
        parser = ConfigParser()
        parser.read_string(base_cfg_txt)
        parser.set(CONFIG_FILE_SITE_SECTION, ConfigParamSite.DB_URL, dburl)
        with StringIO() as buffer:
            parser.write(buffer)
            return CamcopsConfig(
                config_filename="", config_text=buffer.getvalue()
            )

    def _populate_src_db(self, session: Session) -> MergeTestDbInfo:
        # Insert some linked data into database 1.
        # ... taken from DemoDatabaseTestCase
        log.info("Inserting data into source database...")
        for factory in all_subclasses(BaseFactory):
            factory._meta.sqlalchemy_session = session

        self.demo_database_group = GroupFactory()

        patient_with_two_idnums = PatientFactory(
            _group=self.demo_database_group
        )
        NHSPatientIdNumFactory(patient=patient_with_two_idnums)
        RioPatientIdNumFactory(patient=patient_with_two_idnums)

        patient_with_one_idnum = PatientFactory(
            _group=self.demo_database_group
        )
        NHSPatientIdNumFactory(patient=patient_with_one_idnum)

        for cls in Task.all_subclasses_by_tablename():
            factory_class = getattr(task_factories, f"{cls.__name__}Factory")

            t1_kwargs: Dict[str, Any] = dict(_group=self.demo_database_group)
            t2_kwargs = t1_kwargs
            if issubclass(cls, TaskHasPatientMixin):
                t1_kwargs.update(patient=patient_with_two_idnums)
                t2_kwargs.update(patient=patient_with_one_idnum)

            if cls.__name__ == "Photo":
                t1_kwargs.update(
                    create_blob__fieldname="photo_blobid",
                    create_blob__filename="some_picture.png",
                    create_blob__mimetype=MimeType.PNG,
                    create_blob__image_rotation_deg_cw=0,
                    create_blob__theblob=DEMO_PNG_BYTES,
                )

            factory_class(**t1_kwargs)
            factory_class(**t2_kwargs)

        session.commit()  # just in case

        return MergeTestDbInfo(
            # Not sure why, but the source ones start at 1002.
            # Delayed factory operation somehow?
            nhs_which_idnum=ID_OFFSET + 2,
            nhs_desc=NHSIdNumDefinitionFactory.description,
            nhs_shortdesc=NHSIdNumDefinitionFactory.short_description,
            rio_which_idnum=ID_OFFSET + 3,
            rio_desc=RioIdNumDefinitionFactory.description,
            rio_shortdesc=RioIdNumDefinitionFactory.short_description,
        )

    @staticmethod
    def _populate_dst_db(
        session: Session, srcinfo: MergeTestDbInfo
    ) -> MergeTestDbInfo:
        log.info("Inserting basic data only into destination database...")
        dstinfo = replace(srcinfo, nhs_which_idnum=1, rio_which_idnum=2)
        # Hacky...
        dst_iddef_nhs = IdNumDefinition(
            which_idnum=dstinfo.nhs_which_idnum,
            description=dstinfo.nhs_desc,
            short_description=dstinfo.nhs_shortdesc,
        )
        session.add(dst_iddef_nhs)
        dst_iddef_rio = IdNumDefinition(
            which_idnum=dstinfo.rio_which_idnum,
            description=dstinfo.rio_desc,
            short_description=dstinfo.rio_shortdesc,
        )
        session.add(dst_iddef_rio)
        session.commit()
        return dstinfo

    def setUp(self) -> None:
        # ---------------------------------------------------------------------
        # Basic setup
        # ---------------------------------------------------------------------

        # Create database URLs
        self.tempdir = TemporaryDirectory()
        self.dbfilename1 = os.path.join(self.tempdir.name, "camcops_test_1.db")
        self.dbfilename2 = os.path.join(self.tempdir.name, "camcops_test_2.db")
        self.dburl1 = make_sqlite_url(self.dbfilename1)
        self.dburl2 = make_sqlite_url(self.dbfilename2)
        log.info(f"Test database URLs:\n- {self.dburl1}\n- {self.dburl2}")

        # Create configs
        self.cfg1 = self._get_config(self.dburl1)
        self.cfg2 = self._get_config(self.dburl2)

        # Create table structure in each.
        log.info("Creating source database (from-scratch method)...")
        create_database_from_scratch(self.cfg1)
        log.info("Creating destination database (incremental method)...")
        upgrade_database_to_head(self.cfg2)

        # Create a session for each database
        self.db1session = sessionmaker()(
            bind=self.cfg1.get_sqla_engine()
        )  # type: Session
        self.db2session = sessionmaker()(
            bind=self.cfg2.get_sqla_engine()
        )  # type: Session

        # ---------------------------------------------------------------------
        # Data setup
        # ---------------------------------------------------------------------

        self.srcinfo = self._populate_src_db(self.db1session)
        self.dstinfo = self._populate_dst_db(self.db2session, self.srcinfo)

    def test_merge_db(self) -> None:
        merge_camcops_db(
            src=self.dburl1,
            dst_url=self.dburl2,
            echo=False,
            dummy_run=False,
            info_only=False,
            default_group_id=1,
            default_group_name="testgroup",
            groupnum_map={},
            whichidnum_map={
                self.srcinfo.nhs_which_idnum: self.dstinfo.nhs_which_idnum,
                self.srcinfo.rio_which_idnum: self.dstinfo.rio_which_idnum,
            },
            skip_export_logs=True,
            skip_audit_logs=True,
        )
