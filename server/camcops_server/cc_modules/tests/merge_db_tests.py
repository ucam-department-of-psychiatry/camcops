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
from pendulum import now as pendulum_now
from sqlalchemy.orm.session import Session, sessionmaker

from camcops_server.cc_modules.cc_alembic import (
    create_database_from_scratch,
    upgrade_database_to_head,
)
from camcops_server.cc_modules.cc_blob import Blob
from camcops_server.cc_modules.cc_config import CamcopsConfig, get_demo_config
from camcops_server.cc_modules.cc_constants import (
    CONFIG_FILE_SITE_SECTION,
    ConfigParamSite,
    ERA_NOW,
)
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_testfactories import (
    AnyIdNumGroupFactory,
    BaseFactory,
    DeviceFactory,
    IpUseFactory,
    UserFactory,
)
from camcops_server.cc_modules.merge_db import merge_camcops_db
from camcops_server.cc_modules.cc_unittest import DEMO_PNG_BYTES
from camcops_server.tasks.photo import Photo

log = logging.getLogger(__name__)


# =============================================================================
# Unit testing
# =============================================================================


@dataclass
class MergeTestDbInfo:
    # ID numbers:
    nhs_which_idnum: int
    nhs_desc: str
    nhs_shortdesc: str
    rio_which_idnum: int
    rio_desc: str
    rio_shortdesc: str
    # Groups:
    groupnum: int


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

    @staticmethod
    def _populate_src_db(session: Session) -> MergeTestDbInfo:
        # Insert some linked data into database 1.
        # I have failed to achieve this with the test factory classes in full,
        # e.g. NHSIdNumDefinitionFactory, PatientFactory, etc. The ordering is
        # currently such that multiple spurious groups seem to get generated.

        log.info("Inserting data into source database...")
        for factory in all_subclasses(BaseFactory):
            factory._meta.sqlalchemy_session = session
        # Objects created via the factory classes will be auto-added to the
        # session. But manually add groups and ID number definitions.

        # Group
        group = Group(
            id=777,
            name="src_group",
            description="source group",
            upload_policy=AnyIdNumGroupFactory.upload_policy,
            finalize_policy=AnyIdNumGroupFactory.finalize_policy,
            ip_use=IpUseFactory(),
        )
        session.add(group)

        # Device
        device = DeviceFactory()

        # Demo user
        user = UserFactory()

        # All sorts of things need this (see GenericTabletRecordMixin):
        now = pendulum_now()
        default_tablet_args = dict(
            _adding_user=user,
            _current=True,
            _device=device,
            _era=ERA_NOW,
            _group=group,
            _group_id=group.id,
            _when_added_batch_utc=now,
            _when_added_exact=now,
        )

        # ID definitions
        nhs_iddef = IdNumDefinition(
            which_idnum=1000,
            short_description="NHS#",
            description="NHS number",
        )
        session.add(nhs_iddef)
        rio_iddef = IdNumDefinition(
            which_idnum=1001,
            short_description="RiO",
            description="RiO number",
        )
        session.add(rio_iddef)

        # Patients with ID numbers
        patient_with_one_idnum = Patient(
            id=1,
            forename="Forename1",
            surname="Surname1",
            sex="M",
            **default_tablet_args,
        )
        session.add(patient_with_one_idnum)
        session.add(
            PatientIdNum(
                id=1,
                patient_id=patient_with_one_idnum.id,
                which_idnum=nhs_iddef.which_idnum,
                idnum_value=555,
                **default_tablet_args,
            )
        )

        patient_with_two_idnums = Patient(
            id=2,
            forename="Forename2",
            surname="Surname2",
            sex="F",
            **default_tablet_args,
        )
        session.add(patient_with_two_idnums)
        session.add(
            PatientIdNum(
                id=2,
                patient_id=patient_with_two_idnums.id,
                which_idnum=nhs_iddef.which_idnum,
                idnum_value=666,
                **default_tablet_args,
            )
        )
        session.add(
            PatientIdNum(
                id=3,
                patient_id=patient_with_two_idnums.id,
                which_idnum=rio_iddef.which_idnum,
                idnum_value=222,
                **default_tablet_args,
            )
        )

        session.commit()  # just in case

        blobargs = dict(
            tablename=Photo.tablename,
            fieldname="photo_blobid",
            filename="some_picture.png",
            mimetype=MimeType.PNG,
            image_rotation_deg_cw=0,
            theblob=DEMO_PNG_BYTES,
            **default_tablet_args,
        )
        default_task_args = default_tablet_args.copy()
        default_task_args.update(when_created=now)
        for cls in Task.all_subclasses_by_tablename():
            # Make one task from each class for both test patients.
            # Beware the factory classes, because they are making new groups.
            t1_kwargs: Dict[str, Any] = default_task_args.copy()
            t2_kwargs = default_task_args.copy()
            t1_kwargs.update(id=1)
            t2_kwargs.update(id=2)

            if issubclass(cls, TaskHasPatientMixin):
                t1_kwargs.update(patient_id=patient_with_one_idnum.id)
                t2_kwargs.update(patient_id=patient_with_two_idnums.id)

            is_photo = cls.__name__ == "Photo"
            if is_photo:
                # We'll set tablepk=0 temporarily, then fix it in a moment.
                blob1 = Blob(id=1, tablepk=0, **blobargs)
                session.add(blob1)
                blob2 = Blob(id=2, tablepk=0, **blobargs)
                session.add(blob2)

            task1 = cls(**t1_kwargs)
            task2 = cls(**t2_kwargs)
            session.add(task1)
            session.add(task2)

            if is_photo:
                task1.photo_blobid = blob1.id
                task2.photo_blobid = blob2.id
                blob1.tablepk = task1.id
                blob2.tablepk = task2.id

        session.commit()  # just in case
        log.info("... source data inserted")

        return MergeTestDbInfo(
            nhs_which_idnum=nhs_iddef.which_idnum,
            nhs_desc=nhs_iddef.description,
            nhs_shortdesc=nhs_iddef.short_description,
            rio_which_idnum=rio_iddef.which_idnum,
            rio_desc=rio_iddef.description,
            rio_shortdesc=rio_iddef.short_description,
            groupnum=group.id,
        )

    @staticmethod
    def _populate_dst_db(
        session: Session, srcinfo: MergeTestDbInfo
    ) -> MergeTestDbInfo:
        log.info("Inserting basic data only into destination database...")
        dstinfo = replace(
            srcinfo, nhs_which_idnum=1, rio_which_idnum=2, groupnum=9
        )
        assert dstinfo.nhs_which_idnum != dstinfo.rio_which_idnum
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
        dst_group = Group(
            id=dstinfo.groupnum,
            name="dest_group",
            description="destination group",
        )
        session.add(dst_group)
        session.commit()
        log.info("... destination data inserted")
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
        log.info("... source database created")
        alembic_currently_working_with_this_sqla_version = False  # todo: fix
        # 2025-02-27: There is an internal Alembic failure with alembic==1.4.2
        # and SQLAlchemy==1.4.49.
        if alembic_currently_working_with_this_sqla_version:
            log.info("Creating destination database (incremental method)...")
            upgrade_database_to_head(self.cfg2)
        else:
            log.info("Creating destination database (from-scratch method)...")
            create_database_from_scratch(self.cfg2)
        log.info("... destination database created")

        # Create a session for each database
        self.db1session: Session = sessionmaker()(
            bind=self.cfg1.get_sqla_engine()
        )
        self.db2session: Session = sessionmaker()(
            bind=self.cfg2.get_sqla_engine()
        )

        # ---------------------------------------------------------------------
        # Data setup
        # ---------------------------------------------------------------------

        self.srcinfo = self._populate_src_db(self.db1session)
        self.dstinfo = self._populate_dst_db(self.db2session, self.srcinfo)

    def test_merge_db(self) -> None:
        # import pdb; pdb.set_trace()
        whichidnum_map = {
            self.srcinfo.nhs_which_idnum: self.dstinfo.nhs_which_idnum,
            self.srcinfo.rio_which_idnum: self.dstinfo.rio_which_idnum,
        }
        groupnum_map = {
            self.srcinfo.groupnum: self.dstinfo.groupnum,
        }
        log.info("Merging test databases...")
        merge_camcops_db(
            src=self.dburl1,
            dst_url=self.dburl2,
            echo=False,
            dummy_run=False,
            info_only=False,
            default_group_id=1,
            default_group_name="testgroup",
            groupnum_map=groupnum_map,
            whichidnum_map=whichidnum_map,
            skip_export_logs=True,
            skip_audit_logs=True,
        )
        log.info("... test databases merged.")
