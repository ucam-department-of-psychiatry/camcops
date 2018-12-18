#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_export.py

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

**Export and research dump functions.**

Export design:

*WHICH RECORDS TO SEND?*

The most powerful mechanism is not to have a sending queue (which would then
require careful multi-instance locking), but to have a "sent" log. That way:

- A record needs sending if it's not in the sent log (for an appropriate
  recipient).
- You can add a new recipient and the system will know about the (new)
  backlog automatically.
- You can specify criteria, e.g. don't upload records before 1/1/2014, and
  modify that later, and it would catch up with the backlog.
- Successes and failures are logged in the same table.
- Multiple recipients are handled with ease.
- No need to alter database.pl code that receives from tablets.
- Can run with a simple cron job.

*LOCKING*

- Don't use database locking:
  https://blog.engineyard.com/2011/5-subtle-ways-youre-using-mysql-as-a-queue-and-why-itll-bite-you
- Locking via UNIX lockfiles:

  - https://pypi.python.org/pypi/lockfile
  - http://pythonhosted.org/lockfile/ (which also works on Windows)

"""  # noqa

import io
import logging
import os
import sqlite3
import tempfile
from typing import List, Generator, Type, TYPE_CHECKING
import zipfile

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    SqliteBinaryResponse,
    TextAttachmentResponse,
    ZipResponse,
)
import lockfile
from pyramid.response import Response
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session as SqlASession, sessionmaker

from camcops_server.cc_modules.cc_audit import audit
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dump import copy_tasks_and_summaries
from camcops_server.cc_modules.cc_exportmodels import (
    ExportRun,
    get_collection_for_export,
)
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_tsv import TsvCollection

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_taskcollection import TaskCollection

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Main functions
# =============================================================================

def print_export_queue(req: "CamcopsRequest",
                       recipient_names: List[str] = None,
                       via_index: bool = True) -> None:
    """
    Shows tasks that would be exported.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient_names: list of export recipient names (as per the config
            file); blank for "all"
        via_index: use the task index (faster)?
    """
    recipients = req.config.get_export_recipients(req, recipient_names)
    if not recipients:
        log.warning("No export recipients")
        return
    for recipient in recipients:
        log.info("Tasks to be exported for recipient: {}", recipient)
        collection = get_collection_for_export(req, recipient,
                                               via_index=via_index)
        for task in collection.gen_tasks_by_class():
            print(task)


def export(req: "CamcopsRequest",
           recipient_names: List[str] = None,
           via_index: bool = True) -> None:
    """
    Exports all relevant tasks (pending incremental exports, or everything if
    applicable) for specified export recipients.

    Obtains a file lock, then iterates through all recipients.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient_names: list of export recipient names (as per the config
            file); blank for "all"
        via_index: use the task index (faster)?
    """
    cfg = req.config
    dbsession = req.dbsession
    recipients = cfg.get_export_recipients(req, recipient_names)
    if not recipients:
        log.warning("No export recipients")
        return
    # On UNIX, lockfile uses LinkLockFile
    # https://github.com/smontanaro/pylockfile/blob/master/lockfile/linklockfile.py  # noqa
    lock = lockfile.FileLock(cfg.export_lockfile)
    if lock.is_locked():
        log.warning("Export lockfile locked by another process; aborting")
        return
    with lock:  # calls lock.__enter__() and, later, lock.__exit__()
        for recipient in recipients:
            log.info("Exporting to recipient: {}", recipient)
            export_run = ExportRun(recipient)
            dbsession.add(export_run)
            export_run.export(req, via_index=via_index)


# =============================================================================
# Helpers for task collection export functions
# =============================================================================

def gen_audited_tasks_for_task_class(
        collection: "TaskCollection",
        cls: Type[Task],
        audit_descriptions: List[str]) -> Generator[Task, None, None]:
    """
    Generates tasks from a collection, for a given task class, simultaneously
    adding to an audit description. Used for user-triggered downloads.

    Args:
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        cls: the task class to generate
        audit_descriptions: list of strings to be modified

    Yields:
        :class:`camcops_server.cc_modules.cc_task.Task` objects
    """  # noqa
    pklist = []  # type: List[int]
    for task in collection.tasks_for_task_class(cls):
        pklist.append(task.get_pk())
        yield task
    audit_descriptions.append("{}: {}".format(
        cls.__tablename__, ",".join(str(pk) for pk in pklist)))


def gen_audited_tasks_by_task_class(
        collection: "TaskCollection",
        audit_descriptions: List[str]) -> Generator[Task, None, None]:
    """
    Generates tasks from a collection, across task classes, simultaneously
    adding to an audit description. Used for user-triggered downloads.

    Args:
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        audit_descriptions: list of strings to be modified

    Yields:
        :class:`camcops_server.cc_modules.cc_task.Task` objects
    """  # noqa
    for cls in collection.task_classes():
        for task in gen_audited_tasks_for_task_class(collection, cls,
                                                     audit_descriptions):
            yield task


# =============================================================================
# Convert task collections to different export formats for user download
# =============================================================================

def task_collection_to_sqlite_response(req: "CamcopsRequest",
                                       collection: "TaskCollection",
                                       export_options: TaskExportOptions,
                                       as_sql_not_binary: bool) -> Response:
    """
    Converts a set of tasks to an SQLite export, either as binary or the SQL
    text to regenerate it.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        export_options: a :class:`TaskExportOptions` object
        as_sql_not_binary: provide SQL text, rather than SQLite binary? 

    Returns:
        a :class:`pyramid.response.Response` object

    """  # noqa

    # -------------------------------------------------------------------------
    # Create memory file, dumper, and engine
    # -------------------------------------------------------------------------

    # This approach failed:
    #
    #   memfile = io.StringIO()
    #
    #   def dump(querysql, *multiparams, **params):
    #       compsql = querysql.compile(dialect=engine.dialect)
    #       memfile.write("{};\n".format(compsql))
    #
    #   engine = create_engine('{dialect}://'.format(dialect=dialect_name),
    #                          strategy='mock', executor=dump)
    #   dst_session = sessionmaker(bind=engine)()  # type: SqlASession
    #
    # ... you get the error
    #   AttributeError: 'MockConnection' object has no attribute 'begin'
    # ... which is fair enough.
    #
    # Next best thing: SQLite database.
    # Two ways to deal with it:
    # (a) duplicate our C++ dump code (which itself duplicate the SQLite
    #     command-line executable's dump facility), then create the database,
    #     dump it to a string, serve the string; or
    # (b) offer the binary SQLite file.
    # Or... (c) both.
    # Aha! pymysqlite.iterdump does this for us.
    #
    # If we create an in-memory database using create_engine('sqlite://'),
    # can we get the binary contents out? Don't think so.
    #
    # So we should first create a temporary on-disk file, then use that.

    # -------------------------------------------------------------------------
    # Make temporary file (one whose filename we can know).
    # We use tempfile.mkstemp() for security, or NamedTemporaryFile,
    # which is a bit easier. However, you can't necessarily open the file
    # again under all OSs, so that's no good. The final option is
    # TemporaryDirectory, which is secure and convenient.
    #
    # https://docs.python.org/3/library/tempfile.html
    # https://security.openstack.org/guidelines/dg_using-temporary-files-securely.html  # noqa
    # https://stackoverflow.com/questions/3924117/how-to-use-tempfile-namedtemporaryfile-in-python  # noqa
    # -------------------------------------------------------------------------
    db_basename = "temp.sqlite3"
    with tempfile.TemporaryDirectory() as tmpdirname:
        db_filename = os.path.join(tmpdirname, db_basename)
        # ---------------------------------------------------------------------
        # Make SQLAlchemy session
        # ---------------------------------------------------------------------
        url = "sqlite:///" + db_filename
        engine = create_engine(url, echo=False)
        dst_session = sessionmaker(bind=engine)()  # type: SqlASession
        # ---------------------------------------------------------------------
        # Iterate through tasks, creating tables as we need them.
        # ---------------------------------------------------------------------
        audit_descriptions = []  # type: List[str]
        task_generator = gen_audited_tasks_by_task_class(collection,
                                                         audit_descriptions)
        # ---------------------------------------------------------------------
        # Next bit very tricky. We're trying to achieve several things:
        # - a copy of part of the database structure
        # - a copy of part of the data, with relationships intact
        # - nothing sensitive (e.g. full User records) going through
        # - adding new columns for Task objects offering summary values
        # - Must treat tasks all together, because otherwise we will insert
        #   duplicate dependency objects like Group objects.
        # ---------------------------------------------------------------------
        copy_tasks_and_summaries(tasks=task_generator,
                                 dst_engine=engine,
                                 dst_session=dst_session,
                                 export_options=export_options,
                                 req=req)
        dst_session.commit()
        # ---------------------------------------------------------------------
        # Audit
        # ---------------------------------------------------------------------
        audit(req, "SQL dump: {}".format("; ".join(audit_descriptions)))
        # ---------------------------------------------------------------------
        # Fetch file contents, either as binary, or as SQL
        # ---------------------------------------------------------------------
        filename_stem = "CamCOPS_dump_{}".format(
            format_datetime(req.now, DateFormat.FILENAME))
        suggested_filename = filename_stem + (
            ".sql" if as_sql_not_binary else ".sqlite3")

        if as_sql_not_binary:
            # SQL text
            con = sqlite3.connect(db_filename)
            with io.StringIO() as f:
                # noinspection PyTypeChecker
                for line in con.iterdump():
                    f.write(line + "\n")
                con.close()
                f.flush()
                sql_text = f.getvalue()
            return TextAttachmentResponse(body=sql_text,
                                          filename=suggested_filename)
        else:
            # SQLite binary
            with open(db_filename, 'rb') as f:
                binary_contents = f.read()
            return SqliteBinaryResponse(body=binary_contents,
                                        filename=suggested_filename)


def task_collection_to_tsv_zip_response(
        req: "CamcopsRequest",
        collection: "TaskCollection",
        sort_by_heading: bool) -> Response:
    """
    Converts a set of tasks to a TSV (tab-separated value) response, as a set
    of TSV files (one per table) in a ZIP file.
    
    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        sort_by_heading: sort columns within each page by heading name? 

    Returns:
        a :class:`pyramid.response.Response` object

    """  # noqa
    # -------------------------------------------------------------------------
    # Create memory file and ZIP file within it
    # -------------------------------------------------------------------------
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")

    # -------------------------------------------------------------------------
    # Iterate through tasks
    # -------------------------------------------------------------------------
    audit_descriptions = []  # type: List[str]
    for cls in collection.task_classes():
        # Task may return >1 file for TSV output (e.g. for subtables).
        tsvcoll = TsvCollection()

        for task in gen_audited_tasks_for_task_class(collection, cls,
                                                     audit_descriptions):
            tsv_pages = task.get_tsv_pages(req)
            tsvcoll.add_pages(tsv_pages)

        if sort_by_heading:
            tsvcoll.sort_headings_within_all_pages()

        # Write to ZIP.
        # If there are no valid task instances, there'll be no TSV; that's OK.
        for filename_stem in tsvcoll.get_page_names():
            tsv_filename = filename_stem + ".tsv"
            tsv_contents = tsvcoll.get_tsv_file(filename_stem)
            z.writestr(tsv_filename, tsv_contents.encode("utf-8"))

    # -------------------------------------------------------------------------
    # Finish and serve
    # -------------------------------------------------------------------------
    z.close()

    # Audit
    audit(req, "Basic dump: {}".format("; ".join(audit_descriptions)))

    # Return the result
    zip_contents = memfile.getvalue()
    memfile.close()
    zip_filename = "CamCOPS_dump_{}.zip".format(
        format_datetime(req.now, DateFormat.FILENAME))
    return ZipResponse(body=zip_contents, filename=zip_filename)
