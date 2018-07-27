#!/usr/bin/env python
# camcops_server/cc_modules/cc_hl7.py

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

import errno
import codecs
import hl7
import lockfile
import logging
import os
import socket
import subprocess
import sys
from typing import List, Optional, TextIO, Tuple, TYPE_CHECKING, Union

from cardinal_pythonlib.datetimefunc import (
    format_datetime,
    get_now_utc_datetime,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.network import ping
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.sql.expression import or_, not_
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Text,
    UnicodeText,
)

from .cc_constants import DateFormat, HL7MESSAGE_TABLENAME, ERA_NOW
from .cc_filename import change_filename_ext, FileType
from .cc_hl7core import (
    make_msh_segment,
    msg_is_successful_ack,
    SEGMENT_SEPARATOR,
)
from .cc_config import CamcopsConfig
from .cc_recipdef import RecipientDefinition
from .cc_request import CamcopsRequest
from .cc_sqla_coltypes import (
    HostnameColType,
    LongText,
    SendingFormatColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from .cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# General HL7 sources
# =============================================================================
# http://python-hl7.readthedocs.org/en/latest/
# http://www.interfaceware.com/manual/v3gen_python_library_details.html
# http://www.interfaceware.com/hl7_video_vault.html#how
# http://www.interfaceware.com/hl7-standard/hl7-segments.html
# http://www.hl7.org/special/committees/vocab/v26_appendix_a.pdf
# http://www.ncbi.nlm.nih.gov/pmc/articles/PMC130066/

# =============================================================================
# HL7 design
# =============================================================================

# WHICH RECORDS TO SEND?
# Most powerful mechanism is not to have a sending queue (which would then
# require careful multi-instance locking), but to have a "sent" log. That way:
# - A record needs sending if it's not in the sent log (for an appropriate
#   server).
# - You can add a new server and the system will know about the (new) backlog
#   automatically.
# - You can specify criteria, e.g. don't upload records before 1/1/2014, and
#   modify that later, and it would catch up with the backlog.
# - Successes and failures are logged in the same table.
# - Multiple recipients are handled with ease.
# - No need to alter database.pl code that receives from tablets.
# - Can run with a simple cron job.

# LOCKING
# - Don't use database locking:
#   https://blog.engineyard.com/2011/5-subtle-ways-youre-using-mysql-as-a-queue-and-why-itll-bite-you  # noqa
# - Locking via UNIX lockfiles:
#       https://pypi.python.org/pypi/lockfile
#       http://pythonhosted.org/lockfile/
#           ... which also works on Windows.

# CALLING THE HL7 PROCESSOR
# - Use "camcops -7 ..." or "camcops --hl7 ..."
# - Call it via a cron job, e.g. every 5 minutes.

# CONFIG FILE
# q.v.

# TO CONSIDER
# - batched messages (HL7 batching protocol)
#   http://docs.oracle.com/cd/E23943_01/user.1111/e23486/app_hl7batching.htm
# - note: DG1 segment = diagnosis

# BASIC MESSAGE STRUCTURE
# - package into HL7 2.X message as encapsulated PDF
#   http://www.hl7standards.com/blog/2007/11/27/pdf-attachment-in-hl7-message/
# - message ORU^R01
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-messages
#   MESSAGES: http://www.interfaceware.com/hl7-standard/hl7-messages.html
# - OBX segment = observation/result segment
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-obx-segment  # noqa
#   http://www.interfaceware.com/hl7-standard/hl7-segment-OBX.html
# - SEGMENTS:
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-segments
# - ED field (= encapsulated data)
#   http://www.interfaceware.com/hl7-standard/hl7-fields.html
# - base-64 encoding
# - Option for structure (XML), HTML, PDF export.


# =============================================================================
# HL7Run class
# =============================================================================

class HL7Run(Base):
    """
    Class representing an HL7/file run for a specific recipient.

    May be associated with multiple HL7/file messages.
    """
    __tablename__ = "_hl7_run_log"

    run_id = Column(
        "run_id", BigInteger,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
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
    recipient = Column(
        "recipient", HostnameColType,
        index=True,
        comment="Recipient definition name (determines uniqueness)"
    )

    # Common to all ways of sending:
    type = Column(
        "type", SendingFormatColType,
        nullable=False,
        comment="Recipient type (e.g. hl7, file)"
    )
    group_id = Column(
        "group_id", Integer, ForeignKey("_security_groups.id"),
        nullable=False, index=True,
        comment="ID of CamCOPS group to export data from"
    )
    primary_idnum = Column(
        "primary_idnum", Integer,
        nullable=False,
        comment="Which ID number was used as the primary ID?"
    )
    require_idnum_mandatory = Column(
        "require_idnum_mandatory", Boolean,
        comment="Must the primary ID number be mandatory in the relevant "
                "policy?"
    )
    start_date = Column(
        "start_date", DateTime,
        comment="Start date for tasks (UTC)"
    )
    end_date = Column(
        "end_date", DateTime,
        comment="End date for tasks (UTC)"
    )
    finalized_only = Column(
        "finalized_only", Boolean,
        comment="Send only finalized tasks"
    )
    task_format = Column(
        "task_format", SendingFormatColType,
        comment="Format that task information was sent in (e.g. PDF)"
    )
    xml_field_comments = Column(
        "xml_field_comments", Boolean,
        comment="Whether to include field comments in XML output"
    )

    # For HL7 method:
    host = Column(
        "host", HostnameColType,
        comment="(HL7) Destination host name/IP address"
    )
    port = Column(
        "port", Integer,
        comment="(HL7) Destination port number"
    )
    divert_to_file = Column(
        "divert_to_file", Text,
        comment="(HL7) Divert to file with this name"
    )
    treat_diverted_as_sent = Column(
        "treat_diverted_as_sent", Boolean,
        comment="(HL7) Treat messages diverted to file as sent"
    )

    # For file method:
    include_anonymous = Column(
        "include_anonymous", Boolean,
        comment="(FILE) Include anonymous tasks"
    )
    overwrite_files = Column(
        "overwrite_files", Boolean,
        comment="(FILE) Overwrite existing files"
    )
    rio_metadata = Column(
        "rio_metadata", Boolean,
        comment="(FILE) Export RiO metadata file along with main file?"
    )
    rio_idnum = Column(
        "rio_idnum", Integer,
        comment="(FILE) RiO metadata: which ID number is the RiO ID?"
    )
    rio_uploading_user = Column(
        "rio_uploading_user", Text,
        comment="(FILE) RiO metadata: name of automatic upload user"
    )
    rio_document_type = Column(
        "rio_document_type", Text,
        comment="(FILE) RiO metadata: document type for RiO"
    )
    script_after_file_export = Column(
        "script_after_file_export", Text,
        comment="(FILE) Command/script to run after file export"
    )

    # More, beyond the recipient definition:
    script_retcode = Column(
        "script_retcode", Integer,
        comment="Return code from the script_after_file_export script"
    )
    script_stdout = Column(
        "script_stdout", UnicodeText,
        comment="stdout from the script_after_file_export script"
    )
    script_stderr = Column(
        "script_stderr", UnicodeText,
        comment="stderr from the script_after_file_export script"
    )

    def __init__(self, recipdef: RecipientDefinition = None,
                 *args, **kwargs) -> None:
        """
        Initialize from a RecipientDefinition, copying its fields.
        (However, we must also support a no-parameter constructor, not least
        for our merge_db() function.)
        """
        super().__init__(*args, **kwargs)
        if recipdef:
            # Copy:
            # ... common
            self.recipient = recipdef.recipient
            self.type = recipdef.type
            self.group_id = recipdef.group_id
            self.primary_idnum = recipdef.primary_idnum
            self.require_idnum_mandatory = recipdef.require_idnum_mandatory
            self.start_date = recipdef.start_date
            self.end_date = recipdef.end_date
            self.finalized_only = recipdef.finalized_only
            self.task_format = recipdef.task_format
            self.xml_field_comments = recipdef.xml_field_comments

            # ... HL7
            self.host = recipdef.host
            self.port = recipdef.port
            self.divert_to_file = recipdef.divert_to_file
            self.treat_diverted_as_sent = recipdef.treat_diverted_as_sent

            # ... File
            self.include_anonymous = recipdef.include_anonymous
            self.overwrite_files = recipdef.overwrite_files
            self.rio_metadata = recipdef.rio_metadata
            self.rio_idnum = recipdef.rio_idnum
            self.rio_uploading_user = recipdef.rio_uploading_user
            self.rio_document_type = recipdef.rio_document_type
            self.script_after_file_export = recipdef.script_after_file_export

        # New things:
        self.start_at_utc = get_now_utc_datetime()
        self.finish_at_utc = None

    def call_script(self, files_exported: Optional[List[str]]) -> None:
        if not self.script_after_file_export:
            # No script to call
            return
        if not files_exported:
            # Didn't export any files; nothing to do.
            self.script_after_file_export = None  # wasn't called
            return
        args = [self.script_after_file_export] + files_exported
        try:
            encoding = sys.getdefaultencoding()
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            self.script_stdout = out.decode(encoding)
            self.script_stderr = err.decode(encoding)
            self.script_retcode = p.returncode
        except Exception as e:
            self.script_stdout = "Failed to run script"
            self.script_stderr = str(e)

    def finish(self) -> None:
        self.finish_at_utc = get_now_utc_datetime()


# =============================================================================
# HL7Message class
# =============================================================================

class HL7Message(Base):
    __tablename__ = HL7MESSAGE_TABLENAME  # indirected to resolve circular dependency  # noqa

    msg_id = Column(
        "msg_id", Integer,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )
    run_id = Column(
        "run_id", BigInteger, ForeignKey("_hl7_run_log.run_id"),
        comment="FK to _hl7_run_log.run_id"
    )
    hl7run = relationship("HL7Run")
    basetable = Column(
        "basetable", TableNameColType,
        index=True,
        comment="Base table of task concerned"
    )
    serverpk = Column(
        "serverpk", Integer,
        index=True,
        comment="Server PK of task in basetable (_pk field)"
    )
    sent_at_utc = Column(
        "sent_at_utc", DateTime,
        comment="Time message was sent at (UTC)"
    )
    reply_at_utc = Column(
        "reply_at_utc", DateTime,
        comment="(HL7) Time message was replied to (UTC)"
    )
    success = Column(
        "success", Boolean,
        comment="Message sent successfully (and, for HL7, acknowledged)"
    )
    failure_reason = Column(
        "failure_reason", Text,
        comment="Reason for failure"
    )
    message = Column(
        "message", LongText,
        comment="(HL7) Message body, if kept"
    )
    reply = Column(
        "reply", Text,
        comment="(HL7) Server's reply, if kept"
    )
    filename = Column(
        "filename", Text,
        comment="(FILE) Destination filename"
    )
    rio_metadata_filename = Column(
        "rio_metadata_filename", Text,
        comment="(FILE) RiO metadata filename, if used"
    )
    cancelled = Column(
        "cancelled", Boolean,
        comment="Message subsequently invalidated (may trigger resend)"
    )
    cancelled_at_utc = Column(
        "cancelled_at_utc", DateTime,
        comment="Time message was cancelled at (UTC)"
    )

    def __init__(self,
                 task: "Task" = None,
                 recipient_def: RecipientDefinition = None,
                 hl7run: HL7Run = None,
                 show_queue_only: bool = False,
                 *args, **kwargs) -> None:
        """
        Must support parameter-free construction, not least for merge_db().
        """
        super().__init__(*args, **kwargs)
        # Internal attributes
        self._host = None  # type: str
        self._port = None  # type: int
        self._msg = None  # type: str
        self._recipient_def = recipient_def
        self._show_queue_only = show_queue_only
        self._task = task  # type: Task
        # Columns
        self.hl7run = hl7run
        if task:
            self.basetable = task.__tablename__
            self.serverpk = task.get_pk()
        else:
            self.basetable = None
            self.serverpk = None

    @reconstructor
    def init_on_load(self) -> None:
        self._host = None  # type: str
        self._port = None  # type: int
        self._msg = None  # type: str
        self._recipient_def = None  # type: RecipientDefinition
        self._show_queue_only = True
        self._task = None  # type: Task

    def valid(self, req: CamcopsRequest) -> bool:
        """Checks for internal validity; returns Boolean."""
        if not self._recipient_def or not self._recipient_def.valid(req):
            return False
        if not self.basetable or self.serverpk is None:
            return False
        if not self._task:
            return False
        anonymous_ok = (self._recipient_def.using_file() and
                        self._recipient_def.include_anonymous)
        task_is_anonymous = self._task.is_anonymous
        if task_is_anonymous and not anonymous_ok:
            return False
        # After this point, all anonymous tasks must be OK. So:
        task_has_primary_id = self._task.get_patient_idnum_value(
            self._recipient_def.primary_idnum) is not None
        if not task_is_anonymous and not task_has_primary_id:
            return False
        return True

    def divert_to_file(self, f: TextIO) -> None:
        """Write an HL7 message to a file."""
        infomsg = (
            "OUTBOUND MESSAGE DIVERTED FROM RECIPIENT {} AT {}\n".format(
                self._recipient_def.recipient,
                format_datetime(self.sent_at_utc, DateFormat.ISO8601)
            )
        )
        print(infomsg, file=f)
        print(str(self._msg), file=f)
        print("\n", file=f)
        log.debug(infomsg)
        self._host = self._recipient_def.divert_to_file
        if self._recipient_def.treat_diverted_as_sent:
            self.success = True

    def send(self,
             req: CamcopsRequest,
             queue_file: TextIO = None,
             divert_file: TextIO = None) -> Tuple[bool, bool]:
        """Send an outbound HL7/file message, by the appropriate method."""
        # returns: tried, succeeded
        if not self.valid(req):
            return False, False

        if self._show_queue_only:
            print("{},{},{},{},{}".format(
                self._recipient_def.recipient,
                self._recipient_def.type,
                self.basetable,
                self.serverpk,
                self._task.when_created
            ), file=queue_file)
            return False, True

        if not self.hl7run:
            return True, False

        if self.msg_id is None:
            # The "self" object should be in the request's dbsession, so:
            req.dbsession.flush()
            assert self.msg_id is not None

        self.sent_at_utc = req.now_utc

        if self._recipient_def.using_hl7():
            self.make_hl7_message(req)  # will write its own error msg/flags
            if self._recipient_def.divert_to_file:
                self.divert_to_file(divert_file)
            else:
                self.transmit_hl7()
        elif self._recipient_def.using_file():
            self.send_to_filestore(req)
        else:
            raise AssertionError("HL7Message.send: invalid recipient_def.type")
        self.save()

        log.debug("HL7Message.send: recipient={}, basetable={}, serverpk={}",
                  self._recipient_def.recipient,
                  self.basetable,
                  self.serverpk)
        return True, self.success

    def send_to_filestore(self, req: CamcopsRequest) -> None:
        """Send a file to a filestore."""
        self.filename = self._recipient_def.get_filename(
            req=req,
            is_anonymous=self._task.is_anonymous,
            surname=self._task.get_patient_surname(),
            forename=self._task.get_patient_forename(),
            dob=self._task.get_patient_dob(),
            sex=self._task.get_patient_sex(),
            idnum_objects=self._task.get_patient_idnum_objects(),
            creation_datetime=self._task.get_creation_datetime(),
            basetable=self.basetable,
            serverpk=self.serverpk,
        )

        filename = self.filename
        directory = os.path.dirname(filename)
        task = self._task
        task_format = self._recipient_def.task_format
        allow_overwrite = self._recipient_def.overwrite_files

        if task_format == FileType.PDF:
            binary_data = task.get_pdf(req)
            string_data = None
        elif task_format == FileType.HTML:
            binary_data = None
            string_data = task.get_html(req)
        elif task_format == FileType.XML:
            binary_data = None
            string_data = task.get_xml(req)
        else:
            raise AssertionError("write_to_filestore_file: bug")

        if not allow_overwrite and os.path.isfile(filename):
            self.failure_reason = "File already exists"
            return

        if self._recipient_def.make_directory:
            try:
                make_sure_path_exists(directory)
            except Exception as e:
                self.failure_reason = "Couldn't make directory {} ({})".format(
                    directory, e)
                return

        try:
            if task_format == FileType.PDF:
                # binary for PDF
                with open(filename, mode="wb") as f:
                    f.write(binary_data)
            else:
                # UTF-8 for HTML, XML
                with codecs.open(filename, mode="w", encoding="utf8") as f:
                    f.write(string_data)
        except Exception as e:
            self.failure_reason = "Failed to open or write file: {}".format(e)
            return

        # RiO metadata too?
        if self._recipient_def.rio_metadata:
            # No spaces in filename
            self.rio_metadata_filename = change_filename_ext(
                self.filename, ".metadata").replace(" ", "")
            self.rio_metadata_filename = self.rio_metadata_filename
            metadata = task.get_rio_metadata(
                self._recipient_def.rio_idnum,
                self._recipient_def.rio_uploading_user,
                self._recipient_def.rio_document_type
            )
            try:
                dos_newline = "\r\n"
                # ... Servelec say CR = "\r", but DOS is \r\n.
                with codecs.open(self.rio_metadata_filename, mode="w",
                                 encoding="ascii") as f:
                    # codecs.open() means that file writing is in binary mode,
                    # so newline conversion has to be manual:
                    f.write(metadata.replace("\n", dos_newline))
                # UTF-8 is NOT supported by RiO for metadata.
            except Exception as e:
                self.failure_reason = ("Failed to open or write RiO metadata "
                                       "file: {}".format(e))
                return

        self.success = True

    def make_hl7_message(self, req: CamcopsRequest) -> None:
        """
        Stores HL7 message in self.msg.

        May also store it in self.message (which is saved to the database), if
        we're saving HL7 messages.
        """
        # http://python-hl7.readthedocs.org/en/latest/index.html

        msh_segment = make_msh_segment(
            message_datetime=req.now,
            message_control_id=str(self.msg_id)
        )
        pid_segment = self._task.get_patient_hl7_pid_segment(
            req, self._recipient_def)
        other_segments = self._task.get_hl7_data_segments(
            req, self._recipient_def)

        # ---------------------------------------------------------------------
        # Whole message
        # ---------------------------------------------------------------------
        segments = [msh_segment, pid_segment] + other_segments
        self._msg = hl7.Message(SEGMENT_SEPARATOR, segments)
        if self._recipient_def.keep_message:
            self.message = str(self._msg)

    def transmit_hl7(self) -> None:
        """Sends HL7 message over TCP/IP."""
        # Default MLLP/HL7 port is 2575
        # ... MLLP = minimum lower layer protocol
        # ... http://www.cleo.com/support/byproduct/lexicom/usersguide/mllp_configuration.htm  # noqa
        # ... http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=hl7  # noqa
        # Essentially just a TCP socket with a minimal wrapper:
        #   http://stackoverflow.com/questions/11126918

        self._host = self._recipient_def.host
        self._port = self._recipient_def.port
        self.success = False

        # http://python-hl7.readthedocs.org/en/latest/api.html
        # ... but we've modified that
        try:
            with MLLPTimeoutClient(self._recipient_def.host,
                                   self._recipient_def.port,
                                   self._recipient_def.network_timeout_ms) \
                    as client:
                server_replied, reply = client.send_message(self._msg)
        except socket.timeout:
            self.failure_reason = "Failed to send message via MLLP: timeout"
            return
        except Exception as e:
            self.failure_reason = "Failed to send message via MLLP: {}".format(
                str(e))
            return

        if not server_replied:
            self.failure_reason = "No response from server"
            return
        self.reply_at_utc = get_now_utc_datetime()
        if self._recipient_def.keep_reply:
            self.reply = reply
        try:
            replymsg = hl7.parse(reply)
        except Exception as e:
            self.failure_reason = "Malformed reply: {}".format(e)
            return

        self.success, self.failure_reason = msg_is_successful_ack(replymsg)


# =============================================================================
# MLLPTimeoutClient
# =============================================================================
# Modification of MLLPClient from python-hl7, to allow timeouts and failure.

SB = '\x0b'  # <SB>, vertical tab
EB = '\x1c'  # <EB>, file separator
CR = '\x0d'  # <CR>, \r
FF = '\x0c'  # <FF>, new page form feed

RECV_BUFFER = 4096


class MLLPTimeoutClient(object):
    """Class for MLLP TCP/IP transmission that implements timeouts."""

    def __init__(self, host: str, port: int, timeout_ms: int = None) -> None:
        """Creates MLLP client and opens socket."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        timeout_s = float(timeout_ms) / float(1000) \
            if timeout_ms is not None else None
        self.socket.settimeout(timeout_s)
        self.socket.connect((host, port))

    def __enter__(self):
        """For use with "with" statement."""
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, traceback):
        """For use with "with" statement."""
        self.close()

    def close(self):
        """Release the socket connection"""
        self.socket.close()

    def send_message(self, message: Union[str, hl7.Message]) \
            -> Tuple[bool, Optional[str]]:
        """Wraps a str, unicode, or :py:class:`hl7.Message` in a MLLP container
        and send the message to the server
        """
        if isinstance(message, hl7.Message):
            message = str(message)
        # wrap in MLLP message container
        data = SB + message + CR + EB + CR
        # ... the CR immediately after the message is my addition, because
        # HL7 Inspector otherwise says: "Warning: last segment have no segment
        # termination char 0x0d !" (sic).
        return self.send(data.encode('utf-8'))

    def send(self, data: bytes) -> Tuple[bool, Optional[str]]:
        """Low-level, direct access to the socket.send (data must be already
        wrapped in an MLLP container).  Blocks until the server returns.
        """
        # upload the data
        self.socket.send(data)
        # wait for the ACK/NACK
        try:
            ack_msg = self.socket.recv(RECV_BUFFER)
            return True, ack_msg
        except socket.timeout:
            return False, None


# =============================================================================
# Main functions
# =============================================================================

def send_all_pending_hl7_messages(cfg: CamcopsConfig,
                                  show_queue_only: bool = False) -> None:
    """Sends all pending HL7 or file messages.

    Obtains a file lock, then iterates through all recipients.
    """
    queue_stdout = sys.stdout
    if not cfg.hl7_lockfile:
        log.error("send_all_pending_hl7_messages: No HL7_LOCKFILE specified"
                  " in config; can't proceed")
        return
    # On UNIX, lockfile uses LinkLockFile
    # https://github.com/smontanaro/pylockfile/blob/master/lockfile/
    #         linklockfile.py
    lock = lockfile.FileLock(cfg.hl7_lockfile)
    if lock.is_locked():
        log.warning("send_all_pending_hl7_messages: locked by another"
                    " process; aborting")
        return
    with lock:  # calls lock.__enter__() and, later, lock.__exit__()
        with cfg.get_dbsession_context() as dbsession:
            if show_queue_only:
                print("recipient,basetable,_pk,when_created", file=queue_stdout)
            for recipient_def in cfg.hl7_recipient_defs:
                send_pending_hl7_messages(dbsession, recipient_def,
                                          show_queue_only, queue_stdout)


def send_pending_hl7_messages(req: CamcopsRequest,
                              recipient_def: RecipientDefinition,
                              show_queue_only: bool,
                              queue_stdout: TextIO) -> None:
    """Pings recipient if necessary, opens any files required, creates an
    HL7Run, then sends all pending HL7/file messages to a specific
    recipient."""
    # Called once per recipient.
    log.debug("send_pending_hl7_messages: " + str(recipient_def))

    use_ping = (recipient_def.using_hl7() and
                not recipient_def.divert_to_file and
                recipient_def.ping_first)
    if use_ping:
        # No HL7 PING method yet. Proposal is:
        # http://hl7tsc.org/wiki/index.php?title=FTSD-ConCalls-20081028
        # So use TCP/IP ping.
        try:
            timeout_s = min(recipient_def.network_timeout_ms // 1000, 1)
            if not ping(hostname=recipient_def.host,
                        timeout_s=timeout_s):
                log.error("Failed to ping {}", recipient_def.host)
                return
        except socket.error:
            log.error("Socket error trying to ping {}; likely need to "
                      "run as root", recipient_def.host)
            return

    if show_queue_only:
        hl7run = None
    else:
        hl7run = HL7Run(recipient_def)

    # Do things, but with safe file closure if anything goes wrong
    use_divert = (recipient_def.using_hl7() and recipient_def.divert_to_file)
    if use_divert:
        try:
            with codecs.open(recipient_def.divert_to_file, "a", "utf8") as f:
                send_pending_hl7_messages_2(req, recipient_def,
                                            show_queue_only,
                                            queue_stdout, hl7run, f)
        except Exception as e:
            log.error("Couldn't open file {} for appending: {}",
                      recipient_def.divert_to_file, e)
            return
    else:
        send_pending_hl7_messages_2(req, recipient_def, show_queue_only,
                                    queue_stdout, hl7run, None)


def send_pending_hl7_messages_2(
        req: CamcopsRequest,
        recipient_def: RecipientDefinition,
        show_queue_only: bool,
        queue_stdout: TextIO,
        hl7run: HL7Run,
        divert_file: Optional[TextIO]) -> None:
    """
    Sends all pending HL7/file messages to a specific recipient.

    Also called once per recipient, but after diversion files safely
    opened and recipient pinged successfully (if desired).
    """
    dbsession = req.dbsession
    n_hl7_sent = 0
    n_hl7_successful = 0
    n_file_sent = 0
    n_file_successful = 0
    files_exported = []
    for cls in Task.all_subclasses_by_tablename():
        if cls.is_anonymous and not recipient_def.include_anonymous:
            continue
        basetable = cls.__tablename__

        # FETCH TASKS TO SEND.

        # Records from the correct group...
        # Current records...
        # noinspection PyProtectedMember, PyPep8
        q = (
            dbsession.query(cls)
            .filter(cls._group_id == recipient_def.group_id)
            .filter(cls._current == True)
        )

        # Having an appropriate date...
        # Best to use when_created, or _when_added_batch_utc?
        # The former. Because nobody would want a system that would miss
        # amendments to records, and records are defined (date-wise) by
        # when_created.
        if recipient_def.start_date:
            q = q.filter(cls.when_created >= recipient_def.start_date)
        if recipient_def.end_date:
            q = q.filter(cls.when_created <= recipient_def.end_date)

        # That haven't already had a successful HL7 message sent to this
        # server..
        subquery = (
            dbsession.query(HL7Message.serverpk)
            .join(HL7Run)  # automatic: HL7Run.run_id == HL7Message.run_id
            .filter(HL7Message.basetable == basetable)
            .filter(HL7Run.recipient == recipient_def.recipient)
            .filter(HL7Message.success == True)
            .filter(or_(not_(HL7Message.cancelled),
                        HL7Message.cancelled.is_(None)))
        )  # nopep8
        # noinspection PyProtectedMember
        q = q.filter(cls._pk.notin_(subquery))
        # http://explainextended.com/2009/09/18/not-in-vs-not-exists-vs-left-join-is-null-mysql/  # noqa

        # That are finalized (i.e. aren't still on the tablet and potentially
        # subject to modification)?
        if recipient_def.finalized_only:
            # noinspection PyProtectedMember
            q = q.filter(cls._era != ERA_NOW)

        # OK. Fetch PKs and send information.
        for task in q:
            msg = HL7Message(task=task,
                             hl7run=hl7run,
                             recipient_def=recipient_def,
                             show_queue_only=show_queue_only)
            dbsession.add(msg)
            tried, succeeded = msg.send(req, queue_stdout, divert_file)
            if not tried:
                continue
            if recipient_def.using_hl7():
                n_hl7_sent += 1
                n_hl7_successful += 1 if succeeded else 0
            else:
                n_file_sent += 1
                n_file_successful += 1 if succeeded else 0
                if succeeded:
                    files_exported.append(msg.filename)
                    if msg.rio_metadata_filename:
                        files_exported.append(msg.rio_metadata_filename)

    if hl7run:
        hl7run.call_script(files_exported)
        hl7run.finish()
    log.info("{} HL7 messages sent, {} successful, {} failed",
             n_hl7_sent, n_hl7_successful, n_hl7_sent - n_hl7_successful)
    log.info("{} files sent, {} successful, {} failed",
             n_file_sent, n_file_successful, n_file_sent - n_file_successful)


# =============================================================================
# File-handling functions
# =============================================================================

def make_sure_path_exists(path: str) -> None:
    """Creates a directory/directories if the path doesn't already exist."""
    # http://stackoverflow.com/questions/273192
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
