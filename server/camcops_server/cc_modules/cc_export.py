#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_export.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

.. _ActiveMQ: http://activemq.apache.org/
.. _AMQP: https://www.amqp.org/
.. _APScheduler: https://apscheduler.readthedocs.io/
.. _Celery: http://www.celeryproject.org/
.. _Dramatiq: https://dramatiq.io/
.. _RabbitMQ: https://www.rabbitmq.com/
.. _Redis: https://redis.io/
.. _ZeroMQ: http://zeromq.org/

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
  
  - On UNIX, ``lockfile`` uses ``LinkLockFile``:
    https://github.com/smontanaro/pylockfile/blob/master/lockfile/linklockfile.py
  
*MESSAGE QUEUE AND BACKEND*

Thoughts as of 2018-12-22.

- See https://www.fullstackpython.com/task-queues.html. Also http://queues.io/;
  https://stackoverflow.com/questions/731233/activemq-or-rabbitmq-or-zeromq-or.

- The "default" is Celery_, with ``celery beat`` for scheduling, via an
  AMQP_ broker like RabbitMQ_.
  
  - Downside: no longer supported under Windows as of Celery 4.
  
    - There are immediate bugs when running the demo code with Celery 4.2.1,
      fixed by setting the environment variable ``set
      FORKED_BY_MULTIPROCESSING=1`` before running the worker; see
      https://github.com/celery/celery/issues/4178 and
      https://github.com/celery/celery/pull/4078.
  
  - Downside: backend is complex; e.g. Erlang dependency of RabbitMQ.
  
  - Celery also supports Redis_, but Redis_ doesn't support Windows directly
    (except the Windows Subsystem for Linux in Windows 10+).
  
- Another possibility is Dramatiq_ with APScheduler_.

  - Of note, APScheduler_ can use an SQLAlchemy database table as its job
    store, which might be good.
  - Dramatiq_ uses RabbitMQ_ or Redis_.
  - Dramatiq_ 1.4.0 (2018-11-25) installs cleanly under Windows. Use ``pip
    install --upgrade "dramatic[rabbitmq, watch]"`` (i.e. with double quotse,
    not the single quotes it suggests, which don't work under Windows).
  - However, the basic example (https://dramatiq.io/guide.html) fails under
    Windows; when you fire up ``dramatic count_words`` (even with ``--processes
    1 --threads 1``) it crashes with an error from ``ForkingPickler`` in
    ``multiprocessing.reduction``, i.e.
    https://docs.python.org/3/library/multiprocessing.html#windows. It also
    emits a ``PermissionError: [WinError 5] Access is denied``. This is
    discussed a bit at https://github.com/Bogdanp/dramatiq/issues/75;
    https://github.com/Bogdanp/dramatiq/blob/master/docs/source/changelog.rst.
    The changelog suggests 1.4.0 should work, but it doesn't.

- Worth some thought about ZeroMQ_, which is a very different sort of thing.
  Very cross-platform. Needs work to guard against message loss (i.e. messages
  are unreliable by default). Dynamic "special socket" style.

- Possibly also ActiveMQ_.

- OK; so speed is not critical but we want message reliability, for it to work
  under Windows, and decent Python bindings with job scheduling.
  
  - OUT: Redis (not Windows easily), ZeroMQ (fast but not by default reliable),
    ActiveMQ (few Python frameworks?).
  - REMAINING for message handling: RabbitMQ.
  - Python options therefore: Celery (but Windows not officially supported from
    4+); Dramatiq (but Windows also not very well supported and seems a bit
    bleeding-edge).

- This is looking like a mess from the Windows perspective.

- An alternative is just to use the database, of course.

  - https://softwareengineering.stackexchange.com/questions/351449/message-queue-database-vs-dedicated-mq
  - http://mikehadlow.blogspot.com/2012/04/database-as-queue-anti-pattern.html
  - https://blog.jooq.org/2014/09/26/using-your-rdbms-for-messaging-is-totally-ok/
  - https://stackoverflow.com/questions/13005410/why-do-we-need-message-brokers-like-rabbitmq-over-a-database-like-postgresql
  - https://www.quora.com/What-is-the-best-practice-using-db-tables-or-message-queues-for-moderation-of-content-approved-by-humans
  
- Let's take a step back and summarize the problem.

  - Many web threads may upload tasks. This should trigger a prompt export for
    all push recipients.
  - Whichever way we schedule a backend task job, it should be as the
    combination of recipient, basetable, task PK. (That way, if one recipient
    fails, the others can proceed independently.)
  - Every job should check that it's not been completed already (in case of
    accidental job restarts), i.e. is idempotent as far as we can make it.
  - How should this interact with the non-push recipients?
  - We should use the same locking method for push and non-push recipients.
  - We should make the locking granular and use file locks -- for example, for
    each task/recipient combination (or each whole-database export for a given
    recipient).

"""  # noqa

import io
import logging
import os
import sqlite3
import tempfile
from typing import List, Generator, Tuple, Type, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import (
    OdsResponse,
    SqliteBinaryResponse,
    TextAttachmentResponse,
    XlsxResponse,
    ZipResponse,
)
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_engine
import lockfile
from pyramid.response import Response
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session as SqlASession, sessionmaker

from camcops_server.cc_modules.cc_audit import audit
from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_dump import copy_tasks_and_summaries
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportRecipient,
    gen_tasks_having_exportedtasks,
    get_collection_for_export,
)
from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions
from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_tsv import TsvCollection
from camcops_server.cc_modules.celery import export_task_backend

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_taskcollection import TaskCollection

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Main functions
# =============================================================================

def print_export_queue(req: "CamcopsRequest",
                       recipient_names: List[str] = None,
                       all_recipients: bool = False,
                       via_index: bool = True,
                       pretty: bool = False) -> None:
    """
    Called from the command line.

    Shows tasks that would be exported.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient_names: list of export recipient names (as per the config
            file)
        all_recipients: use all recipients?
        via_index: use the task index (faster)?
        pretty: use ``str(task)`` not ``repr(task)`` (prettier, slower because
            it has to query the patient)
    """
    recipients = req.get_export_recipients(
        recipient_names=recipient_names,
        all_recipients=all_recipients,
        save=False
    )
    if not recipients:
        log.warning("No export recipients")
        return
    for recipient in recipients:
        log.info("Tasks to be exported for recipient: {}", recipient)
        collection = get_collection_for_export(req, recipient,
                                               via_index=via_index)
        for task in collection.gen_tasks_by_class():
            print(
                f"{recipient.recipient_name}: "
                f"{str(task) if pretty else repr(task)}"
            )


def export(req: "CamcopsRequest",
           recipient_names: List[str] = None,
           all_recipients: bool = False,
           via_index: bool = True,
           schedule_via_backend: bool = False) -> None:
    """
    Called from the command line.

    Exports all relevant tasks (pending incremental exports, or everything if
    applicable) for specified export recipients.

    Obtains a file lock, then iterates through all recipients.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient_names: list of export recipient names (as per the config
            file)
        all_recipients: use all recipients?
        via_index: use the task index (faster)?
        schedule_via_backend: schedule jobs via the backend instead?
    """
    recipients = req.get_export_recipients(recipient_names=recipient_names,
                                           all_recipients=all_recipients)
    if not recipients:
        log.warning("No export recipients")
        return

    for recipient in recipients:
        log.info("Exporting to recipient: {}", recipient)
        if recipient.using_db():
            if schedule_via_backend:
                raise NotImplementedError()  # todo: implement whole-database export via Celery backend  # noqa
            else:
                export_whole_database(req, recipient, via_index=via_index)
        else:
            # Non-database recipient.
            export_tasks_individually(
                req, recipient,
                via_index=via_index, schedule_via_backend=schedule_via_backend)


def export_whole_database(req: "CamcopsRequest",
                          recipient: ExportRecipient,
                          via_index: bool = True) -> None:
    """
    Exports to a database.
    
    Holds a recipient-specific file lock in the process.
    
    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient: an :class:`camcops_server.cc_modules.cc_exportmodels.ExportRecipient`
        via_index: use the task index (faster)?
    """  # noqa
    cfg = req.config
    lockfilename = cfg.get_export_lockfilename_db(
        recipient_name=recipient.recipient_name)
    try:
        with lockfile.FileLock(lockfilename, timeout=0):  # doesn't wait
            collection = get_collection_for_export(req, recipient,
                                                   via_index=via_index)
            dst_engine = create_engine(recipient.db_url,
                                       echo=recipient.db_echo)
            log.info("Exporting to database: {}",
                     get_safe_url_from_engine(dst_engine))
            dst_session = sessionmaker(bind=dst_engine)()  # type: SqlASession
            task_generator = gen_tasks_having_exportedtasks(collection)
            export_options = TaskExportOptions(
                include_blobs=recipient.db_include_blobs,
                # *** todo: other options, specifically DB_PATIENT_ID_PER_ROW
            )
            copy_tasks_and_summaries(
                tasks=task_generator,
                dst_engine=dst_engine,
                dst_session=dst_session,
                export_options=export_options,
                req=req,
            )
            dst_session.commit()
    except lockfile.AlreadyLocked:
        log.warning("Export logfile {!r} already locked by another process; "
                    "aborting", lockfilename)


def export_tasks_individually(req: "CamcopsRequest",
                              recipient: ExportRecipient,
                              via_index: bool = True,
                              schedule_via_backend: bool = False) -> None:
    """
    Exports all necessary tasks for a recipient.
    
    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient: an :class:`camcops_server.cc_modules.cc_exportmodels.ExportRecipient`
        via_index: use the task index (faster)?
        schedule_via_backend: schedule jobs via the backend instead?
    """  # noqa
    collection = get_collection_for_export(req, recipient, via_index=via_index)
    if schedule_via_backend:
        recipient_name = recipient.recipient_name
        for task_or_index in collection.gen_all_tasks_or_indexes():
            if isinstance(task_or_index, Task):
                basetable = task_or_index.tablename
                task_pk = task_or_index.get_pk()
            else:
                basetable = task_or_index.task_table_name
                task_pk = task_or_index.task_pk
            log.info("Submitting background job to export task {}.{} to {}",
                     basetable, task_pk, recipient_name)
            export_task_backend.delay(
                recipient_name=recipient_name,
                basetable=basetable,
                task_pk=task_pk
            )
    else:
        for task in collection.gen_tasks_by_class():
            # Do NOT use this to check the working of export_task_backend():
            # export_task_backend(recipient.recipient_name, task.tablename, task.get_pk())  # noqa
            # ... it will deadlock at the database (because we're already
            # within a query of some sort, I presume)
            export_task(req, recipient, task)


def export_task(req: "CamcopsRequest",
                recipient: ExportRecipient,
                task: Task) -> None:
    """
    Exports a single task, checking that it remains valid to do so.
    
    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        recipient: an :class:`camcops_server.cc_modules.cc_exportmodels.ExportRecipient`
        task: a :class:`camcops_server.cc_modules.cc_task.Task` 
    """  # noqa

    # Double-check it's OK! Just in case, for example, an old backend task has
    # persisted, or someone's managed to get an iffy back-end request in some
    # other way.
    if not recipient.is_task_suitable(task):
        # Warning will already have been emitted.
        return

    cfg = req.config
    lockfilename = cfg.get_export_lockfilename_task(
        recipient_name=recipient.recipient_name,
        basetable=task.tablename,
        pk=task.get_pk(),
    )
    dbsession = req.dbsession
    try:
        with lockfile.FileLock(lockfilename, timeout=0):  # doesn't wait
            # We recheck the export status once we hold the lock, in case
            # multiple jobs are competing to export it.
            if ExportedTask.task_already_exported(
                    dbsession=dbsession,
                    recipient_name=recipient.recipient_name,
                    basetable=task.tablename,
                    task_pk=task.get_pk()):
                log.info("Task {!r} already exported to recipient {!r}; "
                         "ignoring", task, recipient)
                # Not a warning; it's normal to see these because it allows the
                # client API to skip some checks for speed.
                return
            # OK; safe to export now.
            et = ExportedTask(recipient, task)
            dbsession.add(et)
            et.export(req)
            dbsession.commit()  # so the ExportedTask is visible to others ASAP
    except lockfile.AlreadyLocked:
        log.warning("Export logfile {!r} already locked by another process; "
                    "aborting", lockfilename)


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
    audit_descriptions.append(
        f"{cls.__tablename__}: "
        f"{','.join(str(pk) for pk in pklist)}"
    )


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
        audit(req, f"SQL dump: {'; '.join(audit_descriptions)}")
        # ---------------------------------------------------------------------
        # Fetch file contents, either as binary, or as SQL
        # ---------------------------------------------------------------------
        filename_stem = (
            f"CamCOPS_dump_{format_datetime(req.now, DateFormat.FILENAME)}"
        )
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


def get_tsv_collection_from_task_collection(
        req: "CamcopsRequest",
        collection: "TaskCollection",
        sort_by_heading: bool) -> Tuple[TsvCollection, List[str]]:
    """
    Converts a collection of tasks to a collection of spreadsheet-style data.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        sort_by_heading: sort columns within each page by heading name? 

    Returns:
        tuple: ``tsv_collection, audit_descriptions`` where ``tsv_collection``
        is a :class:`camcops_server.cc_modules.cc_tsv.TsvCollection` object and
        ``audit_descriptions`` is a list of strings describing the data being
        fetched.

    """  # noqa
    audit_descriptions = []  # type: List[str]
    # Task may return >1 file for TSV output (e.g. for subtables).
    tsvcoll = TsvCollection()
    # Iterate through tasks, creating the TSV collection
    for cls in collection.task_classes():
        for task in gen_audited_tasks_for_task_class(collection, cls,
                                                     audit_descriptions):
            tsv_pages = task.get_tsv_pages(req)
            tsvcoll.add_pages(tsv_pages)

    tsvcoll.sort_pages()
    if sort_by_heading:
        tsvcoll.sort_headings_within_all_pages()

    return tsvcoll, audit_descriptions


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
    tsvcoll, audit_descriptions = get_tsv_collection_from_task_collection(
        req, collection, sort_by_heading)
    audit(req, f"Basic dump: {'; '.join(audit_descriptions)}")
    body = tsvcoll.as_zip()
    filename = (
        f"CamCOPS_dump_{format_datetime(req.now, DateFormat.FILENAME)}.zip"
    )
    return ZipResponse(body=body, filename=filename)


def task_collection_to_xlsx_response(
        req: "CamcopsRequest",
        collection: "TaskCollection",
        sort_by_heading: bool) -> Response:
    """
    Converts a set of tasks to an Excel XLSX file.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        sort_by_heading: sort columns within each page by heading name? 

    Returns:
        a :class:`pyramid.response.Response` object

    """  # noqa
    tsvcoll, audit_descriptions = get_tsv_collection_from_task_collection(
        req, collection, sort_by_heading)
    audit(req, f"Basic dump: {'; '.join(audit_descriptions)}")
    body = tsvcoll.as_xlsx()
    filename = (
        f"CamCOPS_dump_{format_datetime(req.now, DateFormat.FILENAME)}.xlsx"
    )
    return XlsxResponse(body=body, filename=filename)


def task_collection_to_ods_response(
        req: "CamcopsRequest",
        collection: "TaskCollection",
        sort_by_heading: bool) -> Response:
    """
    Converts a set of tasks to an OpenOffice ODS file.

    Args:
        req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        collection: a :class:`camcops_server.cc_modules.cc_taskcollection.TaskCollection`
        sort_by_heading: sort columns within each page by heading name? 

    Returns:
        a :class:`pyramid.response.Response` object

    """  # noqa
    tsvcoll, audit_descriptions = get_tsv_collection_from_task_collection(
        req, collection, sort_by_heading)
    audit(req, f"Basic dump: {'; '.join(audit_descriptions)}")
    body = tsvcoll.as_ods()
    filename = (
        f"CamCOPS_dump_{format_datetime(req.now, DateFormat.FILENAME)}.ods"
    )
    return OdsResponse(body=body, filename=filename)
