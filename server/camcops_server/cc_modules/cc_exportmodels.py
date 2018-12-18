#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_exportmodels.py

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

**Define models for export functions (e.g. HL7, file-based export).**

"""

import logging
import os
import socket
import subprocess
import sys
from typing import Generator, List, Tuple, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import (
    get_now_utc_datetime,
    get_now_utc_pendulum,
)
from cardinal_pythonlib.email.sendmail import (
    CONTENT_TYPE_HTML,
    CONTENT_TYPE_TEXT,
)
from cardinal_pythonlib.fileops import mkdir_p
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.network import ping
from cardinal_pythonlib.sqlalchemy.list_types import StringListType
import hl7
from pendulum import DateTime as Pendulum
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import (
    reconstructor,
    relationship,
    Session as SqlASession,
    sessionmaker,
)
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Text,
    UnicodeText,
)

from camcops_server.cc_modules.cc_dump import copy_tasks_and_summaries
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_exportrecipient import (
    ConfigParamExportRecipient,
    ExportRecipient,
    ExportTransmissionMethod,
)
from camcops_server.cc_modules.cc_filename import (
    change_filename_ext,
    FileType,
)
from camcops_server.cc_modules.cc_hl7 import (
    make_msh_segment,
    MLLPTimeoutClient,
    msg_is_successful_ack,
    SEGMENT_SEPARATOR,
)
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_sqla_coltypes import (
    LongText,
    TableNameColType,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_taskcollection import (
    TaskCollection,
    TaskSortMethod,
)
from camcops_server.cc_modules.cc_taskfactory import task_factory_no_security_checks  # noqa

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DOS_NEWLINE = "\r\n"
UTF8 = "utf8"


# =============================================================================
# Create task collections for export
# =============================================================================

def get_collection_for_export(req: "CamcopsRequest",
                              recipient: ExportRecipient,
                              via_index: bool = True) -> TaskCollection:
    """
    Returns an appropriate task collection for this export recipient, namely
    those tasks that are desired and (in the case of incremental exports)
    haven't already been sent.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient: an :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`
        via_index: use the task index (faster)?

    Returns:
        a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
    """  # noqa
    if not via_index:
        log.debug("Task index disabled for get_collection_for_export()")
    collection = TaskCollection(
        req=req,
        sort_method_by_class=TaskSortMethod.CREATION_DATE_ASC,
        current_only=True,
        via_index=via_index,
        export_recipient=recipient,
    )
    return collection


def gen_exported_tasks(
        export_run: "ExportRun",
        dbsession: SqlASession,
        collection: TaskCollection) -> Generator["ExportedTask", None, None]:
    """
    Generates task export entries from a collection.

    Args:
        export_run: an :class:`ExportRun`
        dbsession: a :class:`sqlalchemy.orm.session.Session`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`

    Yields:
        :class:`ExportedTask` objects

    """  # noqa
    for task in collection.gen_tasks_by_class():
        log.debug("Exporting task: {}", task)
        et = ExportedTask(export_run, task)
        dbsession.add(et)
        yield et


def gen_tasks_from_exported_tasks(
        export_run: "ExportRun",
        dbsession: SqlASession,
        collection: TaskCollection) -> Generator["Task", None, None]:
    """
    Generates tasks from a collection, creating export logs as we go.
    
    Used for database exports.

    Args:
        export_run: an :class:`ExportRun`
        dbsession: a :class:`sqlalchemy.orm.session.Session`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`

    Yields:
        :class:`camcops_server.cc_modules.cc_task.Task` objects

    """  # noqa
    for et in gen_exported_tasks(export_run, dbsession, collection):
        yield et.task
        et.succeed()


# =============================================================================
# ExportRun class
# =============================================================================

class ExportRun(Base):
    """
    Class representing an export run for a specific recipient.

    May be associated with multiple tasks being exported.
    """
    __tablename__ = "_export_runs"

    id = Column(
        "id", BigInteger, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    recipient_id = Column(
        "recipient_id", BigInteger, ForeignKey(ExportRecipient.id),
        nullable=False,
        comment="FK to {}.{}".format(ExportRecipient.__tablename__,
                                     ExportRecipient.id.name)
    )
    start_at_utc = Column(
        "start_at_utc", DateTime,
        nullable=False, index=True,
        comment="Time run was started (UTC)"
    )
    finish_at_utc = Column(
        "finish_at_utc", DateTime,
        comment="Time run was finished (UTC)"
    )

    recipient = relationship(ExportRecipient)
    exported_tasks = relationship("ExportedTask")

    def __init__(self, recipient: ExportRecipient = None,
                 *args, **kwargs) -> None:
        """
        Initialize from an ExportRecipient, copying its fields.
        (However, we must also support a no-parameter constructor, not least
        for our :func:`merge_db` function.)
        """
        super().__init__(*args, **kwargs)
        self.recipient = recipient

        # New things:
        self.start_at_utc = get_now_utc_datetime()
        self.finish_at_utc = None
        self.hl7_server_pinged = False

    @reconstructor
    def init_on_load(self) -> None:
        """
        Called when SQLAlchemy recreates an object; see
        https://docs.sqlalchemy.org/en/latest/orm/constructors.html.
        """
        self.hl7_server_pinged = False

    def export(self, req: "CamcopsRequest",
               via_index: bool = True) -> None:
        """
        Performs the export.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            via_index: use the task index (faster)?
        """
        dbsession = req.dbsession
        recipient = self.recipient
        collection = get_collection_for_export(req, recipient,
                                               via_index=via_index)

        if recipient.using_db():
            # Database recipient.
            dst_engine = create_engine(recipient.db_url,
                                       echo=recipient.db_echo)
            dst_session = sessionmaker(bind=dst_engine)()  # type: SqlASession
            task_generator = gen_tasks_from_exported_tasks(
                self, dbsession, collection)
            export_options = TaskExportOptions(
                include_blobs=recipient.db_include_blobs,
                # *** todo: other options, e.g. DB_PATIENT_ID_PER_ROW
            )
            copy_tasks_and_summaries(
                tasks=task_generator,
                dst_engine=dst_engine,
                dst_session=dst_session,
                export_options=export_options,
                req=req,
            )
            dst_session.commit()
        else:
            # Non-database recipient.
            et_generator = gen_exported_tasks(self, dbsession, collection)
            for exported_task in et_generator:
                exported_task.export(req)

        self.finish()

    def finish(self) -> None:
        """
        Records the export finish time.
        """
        self.finish_at_utc = get_now_utc_datetime()

    def ping_hl7_server(self) -> bool:
        """
        Performs a TCP/IP ping on our HL7 server; returns success. If we've
        already pinged successfully during this run, don't bother doing it
        again.

        (No HL7 PING method yet. Proposal is
        http://hl7tsc.org/wiki/index.php?title=FTSD-ConCalls-20081028
        So use TCP/IP ping.)

        Returns:
            bool: success

        """
        if not self.hl7_server_pinged:
            recipient = self.recipient
            timeout_s = min(recipient.hl7_network_timeout_ms // 1000, 1)
            if ping(hostname=recipient.hl7_host, timeout_s=timeout_s):
                self.hl7_server_pinged = True
            else:
                log.error("Failed to ping {!r}", recipient.hl7_host)
        return self.hl7_server_pinged


# =============================================================================
# ExportedTask class
# =============================================================================

class ExportedTask(Base):
    """
    Class representing an attempt to exported a task (as part of a
    :class:`ExportRun` to a specific
    :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`.
    """
    __tablename__ = "_exported_tasks"

    id = Column(
        "id", BigInteger,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    export_run_id = Column(
        "export_run_id", BigInteger, ForeignKey(ExportRun.id),
        comment="FK to {}.{}".format(ExportRun.__tablename__,
                                     ExportRun.id.name)
    )
    basetable = Column(
        "basetable", TableNameColType, nullable=False, index=True,
        comment="Base table of task concerned"
    )
    task_server_pk = Column(
        "task_server_pk", Integer, nullable=False, index=True,
        comment="Server PK of task in basetable (_pk field)"
    )
    success = Column(
        "success", Boolean, default=False, nullable=False,
        comment="Task exported successfully?"
    )
    failure_reasons = Column(
        "failure_reasons", StringListType,
        comment="Reasons for failure"
    )
    cancelled = Column(
        "cancelled", Boolean, default=False, nullable=False,
        comment="Export subsequently cancelled/invalidated (may trigger resend)"  # noqa
    )
    cancelled_at_utc = Column(
        "cancelled_at_utc", DateTime,
        comment="Time message was cancelled at (UTC)"
    )

    export_run = relationship(ExportRun)
    hl7_messages = relationship("ExportedTaskHL7Message")
    filegroups = relationship("ExportedTaskFileGroup")
    emails = relationship("ExportedTaskEmail")

    def __init__(self,
                 export_run: ExportRun = None,
                 task: "Task" = None,
                 basetable: str = None,
                 task_server_pk: int = None,
                 *args, **kwargs) -> None:
        """
        Can initialize with a task, or a basetable/task_server_pk combination.

        Args:
            export_run: an :class:`ExportRun` object
            task: a :class:`camcops_server.cc_modules.cc_task.Task` object
            basetable: base table name of the task
            task_server_pk: server PK of the task

        (However, we must also support a no-parameter constructor, not least
        for our :func:`merge_db` function.)
        """
        super().__init__(*args, **kwargs)
        self.failure_reasons = []  # type: List[str]
        self.export_run = export_run
        if task:
            assert (not basetable) and task_server_pk is None, (
                "Task specified; mustn't specify basetable/task_server_pk"
            )
            self.basetable = task.tablename
            self.task_server_pk = task.get_pk()
            self._task = task
        else:
            self.basetable = basetable
            self.task_server_pk = task_server_pk
            self._task = None  # type: Task

    @reconstructor
    def init_on_load(self) -> None:
        """
        Called when SQLAlchemy recreates an object; see
        https://docs.sqlalchemy.org/en/latest/orm/constructors.html.
        """
        self._task = None  # type: Task

    @property
    def task(self) -> "Task":
        """
        Returns the associated task.
        """
        if self._task is None:
            dbsession = SqlASession.object_session(self)
            try:
                self._task = task_factory_no_security_checks(
                    dbsession, self.basetable, self.task_server_pk)
            except KeyError:
                log.warning(
                    "Failed to retrieve task for basetable={!r}, PK={!r}",
                    self.basetable,
                    self.task_server_pk
                )
                self._task = None
        return self._task

    def succeed(self) -> None:
        """
        Register success.
        """
        self.success = True

    def fail(self, msg: str) -> None:
        """
        Record failure, and why.

        Args:
            msg: why
        """
        self.success = False
        log.debug("Task export failed: {}", msg)
        self.failure_reasons.append(msg)

    def export(self, req: "CamcopsRequest") -> None:
        """
        Performs an export of the specific task.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        dbsession = req.dbsession
        recipient = self.export_run.recipient
        transmission_method = recipient.transmission_method

        if transmission_method == ExportTransmissionMethod.EMAIL:
            email = ExportedTaskEmail(self)
            dbsession.add(email)
            email.export_task(req)

        elif transmission_method == ExportTransmissionMethod.FILE:
            efg = ExportedTaskFileGroup(self)
            dbsession.add(efg)
            efg.export_task(req)

        elif transmission_method == ExportTransmissionMethod.HL7:
            ehl7 = ExportedTaskHL7Message(self)
            if ehl7.valid():
                dbsession.add(ehl7)
                ehl7.export_task(req)
            else:
                self.fail("Task not valid for HL7 export")

        else:
            raise AssertionError("Bug: bad transmission_method")

    @property
    def filegroup(self) -> "ExportedTaskFileGroup":
        """
        Returns a :class:`ExportedTaskFileGroup`, creating it if necessary.
        """
        if self.filegroups:
            filegroup = self.filegroups[0]  # type: ExportedTaskFileGroup
        else:
            filegroup = ExportedTaskFileGroup(self)
            self.filegroups.append(filegroup)
        return filegroup

    def export_file(self,
                    filename: str,
                    text: str = None,
                    binary: bytes = None,
                    text_encoding: str = UTF8) -> None:
        """
        Exports a file.

        Args:
            filename:
            text: text contents (specify this XOR ``binary``)
            binary: binary contents (specify this XOR ``text``)
            text_encoding: encoding to use when writing text
        """
        filegroup = self.filegroup
        filegroup.export_file(filename=filename,
                              text=text,
                              binary=binary,
                              text_encoding=text_encoding)

    def cancel(self) -> None:
        """
        Marks the task export as cancelled/invalidated.

        May trigger a resend (which is the point).
        """
        self.cancelled = True
        self.cancelled_at_utc = get_now_utc_datetime()


# =============================================================================
# HL7Message class
# =============================================================================

class ExportedTaskHL7Message(Base):
    """
    Represents an individual HL7 message.
    """
    __tablename__ = "_exported_task_hl7msg"

    id = Column(
        "id", BigInteger, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    exported_task_id = Column(
        "exported_task_id", BigInteger, ForeignKey(ExportedTask.id),
        nullable=False,
        comment="FK to {}.{}".format(ExportedTask.__tablename__,
                                     ExportedTask.id.name)
    )
    sent_at_utc = Column(
        "sent_at_utc", DateTime,
        comment="Time message was sent at (UTC)"
    )
    reply_at_utc = Column(
        "reply_at_utc", DateTime,
        comment="Time message was replied to (UTC)"
    )
    success = Column(
        "success", Boolean,
        comment="Message sent successfully and acknowledged by HL7 server"
    )
    failure_reason = Column(
        "failure_reason", Text,
        comment="Reason for failure"
    )
    message = Column(
        "message", LongText,
        comment="Message body, if kept"
    )
    reply = Column(
        "reply", Text,
        comment="Server's reply, if kept"
    )

    exported_task = relationship(ExportedTask)

    def __init__(self,
                 exported_task: ExportedTask = None,
                 *args, **kwargs) -> None:
        """
        Must support parameter-free construction, not least for
        :func:`merge_db`.
        """
        super().__init__(*args, **kwargs)
        self.exported_task = exported_task

        self._hl7_msg = None  # type: hl7.Message

    @reconstructor
    def init_on_load(self) -> None:
        """
        Called when SQLAlchemy recreates an object; see
        https://docs.sqlalchemy.org/en/latest/orm/constructors.html.
        """
        self._hl7_msg = None

    @staticmethod
    def task_acceptable_for_hl7(recipient: ExportRecipient,
                                task: "Task") -> bool:
        """
        Is the task valid for HL7 export. (For example, anonymous tasks and
        tasks missing key ID information may not be.)

        Args:
            recipient: an :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`
            task: a :class:`camcops_server.cc_modules.cc_task.Task` object

        Returns:
            bool: valid?

        """  # noqa
        if not task:
            return False
        if task.is_anonymous:
            return False  # Cannot send anonymous tasks via HL7
        patient = task.patient
        if not patient:
            return False
        if not recipient.primary_idnum:
            return False  # required for HL7
        if not patient.has_idnum_type(recipient.primary_idnum):
            return False
        return True

    def valid(self) -> bool:
        """
        Checks for internal validity; returns a bool.
        """
        exported_task = self.exported_task
        task = exported_task.task
        recipient = exported_task.export_run.recipient
        return self.task_acceptable_for_hl7(recipient, task)

    def succeed(self, now: Pendulum = None) -> None:
        """
        Record that we succeeded, and so did our associated task export.
        """
        now = now or get_now_utc_datetime()
        self.success = True
        self.sent_at_utc = now
        self.exported_task.succeed()

    def fail(self, msg: str) -> None:
        """
        Record that we failed, and so did our associated task export.

        Args:
            msg: reason for failure
        """
        self.success = False
        self.failure_reason = msg
        self.exported_task.fail("HL7 sending failed")

    def export_task(self, req: "CamcopsRequest") -> None:
        """
        Exports the task itself to an HL7 message.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        if not self.valid():
            self.fail(
                "Unsuitable for HL7; should have been filtered out earlier")
            return
        self.make_hl7_message(req)
        recipient = self.exported_task.export_run.recipient
        if recipient.hl7_debug_divert_to_file:
            self.divert_to_file()
        else:
            # Proper HL7 message
            self.transmit_hl7()

    def divert_to_file(self) -> None:
        """
        Write an HL7 message to a file. For debugging.
        """
        exported_task = self.exported_task
        recipient = exported_task.export_run.recipient
        filename = recipient.hl7_debug_divert_to_file
        now_utc = get_now_utc_pendulum()
        infomsg = (
            "OUTBOUND HL7 MESSAGE DIVERTED FROM RECIPIENT "
            "{!r} TO FILE {!r} AT {}".format(
                recipient.recipient_name,
                filename,
                now_utc
            )
        )
        contents = infomsg + "\n" + str(self._hl7_msg) + "\n"
        exported_task.export_file(filename=filename, text=contents)
        log.info(infomsg)

        if recipient.hl7_debug_treat_diverted_as_sent:
            self.sent_at_utc = now_utc
            self.succeed(now_utc)
        else:
            self.fail("Exported to file as requested but not sent via HL7")

    def make_hl7_message(self, req: "CamcopsRequest") -> None:
        """
        Makes an HL7 message and stores it in ``self._hl7_msg``.

        May also store it in ``self.message`` (which is saved to the database),
        if we're saving HL7 messages.

        See

        - http://python-hl7.readthedocs.org/en/latest/index.html
        """
        task = self.exported_task.task
        recipient = self.exported_task.export_run.recipient

        # ---------------------------------------------------------------------
        # Parts
        # ---------------------------------------------------------------------
        msh_segment = make_msh_segment(
            message_datetime=req.now,
            message_control_id=str(self.id)
        )
        pid_segment = task.get_patient_hl7_pid_segment(req, recipient)
        other_segments = task.get_hl7_data_segments(req, recipient)

        # ---------------------------------------------------------------------
        # Whole message
        # ---------------------------------------------------------------------
        segments = [msh_segment, pid_segment] + other_segments
        self._hl7_msg = hl7.Message(SEGMENT_SEPARATOR, segments)
        if recipient.hl7_keep_message:
            self.message = str(self._hl7_msg)

    def transmit_hl7(self) -> None:
        """
        Sends the HL7 message over TCP/IP.

        - Default MLLP/HL7 port is 2575
        - MLLP = minimum lower layer protocol

          - http://www.cleo.com/support/byproduct/lexicom/usersguide/mllp_configuration.htm
          - http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=hl7
          - Essentially just a TCP socket with a minimal wrapper:
            http://stackoverflow.com/questions/11126918
            
        - http://python-hl7.readthedocs.org/en/latest/api.html; however,
          we've modified that
        """  # noqa
        export_run = self.exported_task.export_run
        recipient = export_run.recipient

        if recipient.hl7_ping_first:
            pinged = export_run.ping_hl7_server()
            if not pinged:
                self.fail("Could not ping HL7 host")
                return

        try:
            log.info("Sending HL7 message to {}:{}",
                     recipient.hl7_host, recipient.hl7_port)
            with MLLPTimeoutClient(recipient.hl7_host,
                                   recipient.hl7_port,
                                   recipient.hl7_network_timeout_ms) as client:
                server_replied, reply = client.send_message(self._hl7_msg)
        except socket.timeout:
            self.fail("Failed to send message via MLLP: timeout")
            return
        except Exception as e:
            self.fail("Failed to send message via MLLP: {}".format(e))
            return

        if not server_replied:
            self.fail("No response from server")
            return

        self.reply_at_utc = get_now_utc_datetime()
        if recipient.hl7_keep_reply:
            self.reply = reply

        try:
            replymsg = hl7.parse(reply)
        except Exception as e:
            self.fail("Malformed reply: {}".format(e))
            return

        success, failure_reason = msg_is_successful_ack(replymsg)
        if success:
            self.succeed()
        else:
            self.fail(failure_reason)


# =============================================================================
# FileExport class
# =============================================================================

class ExportedTaskFileGroup(Base):
    """
    Represents a small set of files exported in relation to a single task.
    """
    __tablename__ = "_exported_task_filegroup"

    id = Column(
        "id", BigInteger, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    exported_task_id = Column(
        "exported_task_id", BigInteger, ForeignKey(ExportedTask.id),
        nullable=False,
        comment="FK to {}.{}".format(ExportedTask.__tablename__,
                                     ExportedTask.id.name)
    )
    filenames = Column(
        "filenames", StringListType,
        comment="List of filenames exported"
    )
    script_called = Column(
        "script_called", Boolean, default=False, nullable=False,
        comment="Was the {} script called?".format(
            ConfigParamExportRecipient.FILE_SCRIPT_AFTER_EXPORT)
    )
    script_retcode = Column(
        "script_retcode", Integer,
        comment="Return code from the {} script".format(
            ConfigParamExportRecipient.FILE_SCRIPT_AFTER_EXPORT)
    )
    script_stdout = Column(
        "script_stdout", UnicodeText,
        comment="stdout from the {} script".format(
            ConfigParamExportRecipient.FILE_SCRIPT_AFTER_EXPORT)
    )
    script_stderr = Column(
        "script_stderr", UnicodeText,
        comment="stderr from the {} script".format(
            ConfigParamExportRecipient.FILE_SCRIPT_AFTER_EXPORT)
    )

    exported_task = relationship(ExportedTask)

    def __init__(self, exported_task: ExportedTask = None) -> None:
        """
        Args:
            exported_task: :class:`ExportedTask` object
        """
        self.exported_task = exported_task
        self.filenames = []  # type: List[str]

    def export_file(self,
                    filename: str,
                    text: str = None,
                    binary: bytes = None,
                    text_encoding: str = UTF8) -> None:
        """
        Exports the file.

        Args:
            filename:
            text: text contents (specify this XOR ``binary``)
            binary: binary contents (specify this XOR ``text``)
            text_encoding: encoding to use when writing text
        """
        assert bool(text) != bool(binary), "Specify text XOR binary"
        exported_task = self.exported_task
        filename = os.path.abspath(filename)
        directory = os.path.dirname(filename)
        recipient = exported_task.export_run.recipient

        if not recipient.file_overwrite_files and os.path.isfile(filename):
            exported_task.fail("File already exists")
            return

        if recipient.file_make_directory:
            try:
                mkdir_p(directory)
            except Exception as e:
                exported_task.fail("Couldn't make directory "
                                   "{!r}: {}".format(directory, e))
                return

        try:
            log.debug("Writing to {!r}", filename)
            if text:
                with open(filename, mode="w", encoding=text_encoding) as f:
                    f.write(text)
            else:
                with open(filename, mode="wb") as f:
                    f.write(binary)
        except Exception as e:
            exported_task.fail("Failed to open or write file {!r}: {}".format(
                filename, e))
            return

        self.note_exported_file(filename)

    def note_exported_file(self, *filenames: str) -> None:
        """
        Records a filename that has been exported, or several.

        Args:
            *filenames: filenames
        """
        self.filenames.extend(filenames)

    def export_task(self, req: "CamcopsRequest") -> None:
        """
        Exports the task itself to a file.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        exported_task = self.exported_task
        task = exported_task.task
        recipient = exported_task.export_run.recipient
        task_format = recipient.task_format
        task_filename = recipient.get_filename(req, task)

        # Export task
        if task_format == FileType.PDF:
            binary = task.get_pdf(req)
            text = None
        elif task_format == FileType.HTML:
            binary = None
            text = task.get_html(req)
        elif task_format == FileType.XML:
            binary = None
            text = task.get_xml(req)
        else:
            raise AssertionError("Unknown task_format")
        self.export_file(task_filename,
                         text=text, binary=binary, text_encoding=UTF8)

        # RiO metadata too?
        if recipient.file_export_rio_metadata:
            # No spaces in filename
            rio_metadata_filename = change_filename_ext(
                task_filename, ".metadata").replace(" ", "")
            metadata = task.get_rio_metadata(
                recipient.rio_idnum,
                recipient.rio_uploading_user,
                recipient.rio_document_type
            )
            # We're going to write in binary mode, to get the newlines right.
            # One way is:
            #     with codecs.open(filename, mode="w", encoding="ascii") as f:
            #         f.write(metadata.replace("\n", DOS_NEWLINE))
            # Here's another.
            metadata = metadata.replace("\n", DOS_NEWLINE)
            # ... Servelec say CR = "\r", but DOS is \r\n.
            metadata_binary = metadata.encode("ascii")
            # UTF-8 is NOT supported by RiO for metadata.
            self.export_file(rio_metadata_filename, binary=metadata_binary)

        self.finish_run_script_if_necessary()

    def succeed(self) -> None:
        """
        Register success.
        """
        self.exported_task.succeed()

    def fail(self, msg: str) -> None:
        """
        Record failure, and why.

        Args:
            msg: why
        """
        self.exported_task.fail(msg)

    def finish_run_script_if_necessary(self) -> None:
        """
        Completes the file export by running the external script, if required.
        """
        if not self.filenames:
            self.succeed()
            return
        exported_task = self.exported_task
        recipient = exported_task.export_run.recipient
        if not recipient.file_script_after_export:
            return
        args = [recipient.file_script_after_export] + self.filenames
        try:
            encoding = sys.getdefaultencoding()
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            self.script_called = True
            self.script_stdout = out.decode(encoding)
            self.script_stderr = err.decode(encoding)
            self.script_retcode = p.returncode
            self.succeed()
        except Exception as e:
            self.script_called = False
            self.script_stdout = ""
            self.script_stderr = str(e)
            self.fail("Failed to run script")


# =============================================================================
# EmailExport class
# =============================================================================

class ExportedTaskEmail(Base):
    """
    Represents an individual email export.
    """
    __tablename__ = "_exported_task_email"

    id = Column(
        "id", BigInteger, primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    exported_task_id = Column(
        "exported_task_id", BigInteger, ForeignKey(ExportedTask.id),
        nullable=False,
        comment="FK to {}.{}".format(ExportedTask.__tablename__,
                                     ExportedTask.id.name)
    )
    email_id = Column(
        "email_id", BigInteger, ForeignKey(Email.id),
        comment="FK to {}.{}".format(Email.__tablename__,
                                     Email.id.name)
    )

    exported_task = relationship(ExportedTask)
    email = relationship(Email)

    def __init__(self, exported_task: ExportedTask = None) -> None:
        """
        Args:
            exported_task: :class:`ExportedTask` object
        """
        self.exported_task = exported_task

    def export_task(self, req: "CamcopsRequest") -> None:
        """
        Exports the task itself to an email.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        exported_task = self.exported_task
        task = exported_task.task
        recipient = exported_task.export_run.recipient
        task_format = recipient.task_format
        task_filename = recipient.get_filename(req, task)
        encoding = "utf8"

        # Export task
        attachments = []  # type: List[Tuple[str, bytes]]
        if task_format == FileType.PDF:
            binary = task.get_pdf(req)
        elif task_format == FileType.HTML:
            binary = task.get_html(req).encode(encoding)
        elif task_format == FileType.XML:
            binary = task.get_xml(req).encode(encoding)
        else:
            raise AssertionError("Unknown task_format")
        attachments.append((task_filename, binary))

        self.email = Email(
            from_addr=recipient.email_from,
            # date: automatic
            sender=recipient.email_sender,
            reply_to=recipient.email_reply_to,
            to=recipient.email_to,
            cc=recipient.email_cc,
            bcc=recipient.email_bcc,
            subject=recipient.get_email_subject(req, task),
            body=recipient.get_email_body(req, task),
            content_type=(
                CONTENT_TYPE_HTML if recipient.email_body_as_html
                else CONTENT_TYPE_TEXT
            ),
            charset=encoding,
            attachments_binary=attachments,
            save_msg_string=recipient.email_keep_message,
        )
        self.email.send(
            host=recipient.email_host,
            username=recipient.email_host_username,
            password=recipient.email_host_password,
            port=recipient.email_port,
            use_tls=recipient.email_use_tls,
        )
        if self.email.sent:
            exported_task.succeed()
        else:
            exported_task.fail("Failed to send e-mail")
