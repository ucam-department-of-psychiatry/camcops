#!/usr/bin/env python

"""
camcops_server/cc_modules/celery.py

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

**Celery app.**

Basic steps to set up Celery:

- Our app will be "camcops_server.cc_modules".
- Within that, Celery expects "celery.py", in which configuration is set up
  by defining the ``app`` object.
- Also, in ``__init__.py``, we should import that app. (No, scratch that; not
  necessary.)
- That makes ``@shared_task`` work in all other modules here.
- Finally, here, we ask Celery to scan ``tasks.py`` to find tasks.

Modified:

- The ``@shared_task`` decorator doesn't offer all the options that
  ``@app.task`` has. Let's skip ``@shared_task`` and the increased faff that
  entails.

The difficult part seems to be getting a broker URL in the config.

- If we load the config here, from ``celery.py``, then if the config uses any
  SQLAlchemy objects, it'll crash because some aren't imported.
- A better way is to delay configuring the app.
- But also, it is very tricky if the config uses SQLAlchemy objects; so it
  shouldn't.

Note also re logging:

- The log here is configured (at times, at least) by Celery, so uses its log
  settings. At the time of startup, that looks like plain ``print()``
  statements.

**In general, prefer delayed imports during actual tasks. Otherwise circular
imports are very hard to avoid.**

If using a separate ``celery_tasks.py`` file:

- Import this only after celery.py, or the decorators will fail.

- If you see this error from ``camcops_server launch_workers`` when using a
  separate ``celery_tasks.py`` file: 

  .. code-block:: none

    [2018-12-26 21:08:01,316: ERROR/MainProcess] Received unregistered task of type 'camcops_server.cc_modules.celery_tasks.export_to_recipient_backend'.
    The message has been ignored and discarded.

    Did you remember to import the module containing this task?
    Or maybe you're using relative imports?

    Please see
    http://docs.celeryq.org/en/latest/internals/protocol.html
    for more information.

    The full contents of the message body was:
    '[["recipient_email_rnc"], {}, {"callbacks": null, "errbacks": null, "chain": null, "chord": null}]' (98b)
    Traceback (most recent call last):
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/celery/worker/consumer/consumer.py", line 558, in on_task_received
        strategy = strategies[type_]
    KeyError: 'camcops_server.cc_modules.celery_tasks.export_to_recipient_backend'

  then (1) run with ``--verbose``, which will show you the list of registered
  tasks; (2) note that everything here is absent; (3) insert a "crash" line at
  the top of this file and re-run; (4) note what's importing this file too
  early.
  
General advice:

- https://medium.com/@taylorhughes/three-quick-tips-from-two-years-with-celery-c05ff9d7f9eb

Task decorator options:

- http://docs.celeryproject.org/en/latest/reference/celery.app.task.html
- ``bind``: makes the first argument a ``self`` parameter to manipulate the
  task itself; 
  http://docs.celeryproject.org/en/latest/userguide/tasks.html#example
- ``acks_late`` (for the decorator) or ``task_acks_late``: see

  - http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_acks_late
  - http://docs.celeryproject.org/en/latest/faq.html#faq-acks-late-vs-retry
  - Here I am retrying on failure with exponential backoff, but not using
    ``acks_late`` in addition.

"""  # noqa

import logging
from typing import Any, Dict, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from celery import Celery, current_task

# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa

if TYPE_CHECKING:
    from celery.app.task import Task as CeleryTask

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

CELERY_APP_NAME = "camcops_server.cc_modules"
# CELERY_TASKS_MODULE = "celery_tasks"
# ... look for "celery_tasks.py" (as opposed to the more common "tasks.py")

CELERY_TASK_MODULE_NAME = CELERY_APP_NAME + ".celery"

MAX_RETRIES = 10
CELERY_SOFT_TIME_LIMIT_SEC = 300


# =============================================================================
# Configuration
# =============================================================================

def get_celery_settings_dict() -> Dict[str, Any]:
    """
    This function is passed as a callable to Celery's ``add_defaults``, and
    thus is called when needed (rather than immediately).
    """  # noqa
    log.debug("Configuring Celery")
    from camcops_server.cc_modules.cc_config import get_default_config_from_os_env  # delayed import  # noqa
    config = get_default_config_from_os_env()

    # Schedule
    schedule = {}  # type: Dict[str, Any]
    for crontab_entry in config.crontab_entries:
        recipient_name = crontab_entry.content
        schedule_name = f"export_to_{recipient_name}"
        log.info("Adding regular export job {}: crontab: {}",
                 schedule_name, crontab_entry)
        schedule[schedule_name] = {
            "task": CELERY_TASK_MODULE_NAME + ".export_to_recipient_backend",
            "schedule": crontab_entry.get_celery_schedule(),
            "args": (recipient_name, ),
        }

    # Final Celery settings
    return {
        "beat_schedule": schedule,
        "broker_url": config.celery_broker_url,
        "timezone": config.schedule_timezone,
    }


# =============================================================================
# The Celery app
# =============================================================================

celery_app = Celery()
celery_app.add_defaults(get_celery_settings_dict)
# celery_app.autodiscover_tasks([CELERY_APP_NAME],
#                               related_name=CELERY_TASKS_MODULE)

_ = '''

@celery_app.on_configure.connect
def _app_on_configure(**kwargs) -> None:
    log.critical("@celery_app.on_configure: {!r}", kwargs)


@celery_app.on_after_configure.connect
def _app_on_after_configure(**kwargs) -> None:
    log.critical("@celery_app.on_after_configure: {!r}", kwargs)

'''


# =============================================================================
# Test tasks
# =============================================================================

@celery_app.task(bind=True)
def debug_task(self) -> None:
    """
    Test as follows:

    .. code-block:: python

        from camcops_server.cc_modules.celery import *
        debug_task.delay()

    and also launch workers with ``camcops_server launch_workers``.

    For a bound task, the first (``self``) argument is the task instance; see
    http://docs.celeryproject.org/en/latest/userguide/tasks.html#bound-tasks

    """
    log.info(f"self: {self!r}")
    log.info(f"Backend: {current_task.backend}")


@celery_app.task
def debug_task_add(a: float, b: float) -> float:
    """
    Test as follows:

    .. code-block:: python

        from camcops_server.cc_modules.celery import *
        debug_task_add.delay()
    """
    result = a + b
    log.info("a = {}, b = {} => a + b = {}", a, b, result)
    return result


# =============================================================================
# Exponential backoff
# =============================================================================

def backoff(attempts: int) -> int:
    """
    Return a backoff delay, in seconds, given a number of attempts.

    The delay increases very rapidly with the number of attempts:
    1, 2, 4, 8, 16, 32, ...

    As per https://blog.balthazar-rouberol.com/celery-best-practices.

    """
    return 2 ** attempts


# =============================================================================
# Real tasks
# =============================================================================

@celery_app.task(bind=True,
                 ignore_result=True,
                 max_retries=MAX_RETRIES,
                 soft_time_limit=CELERY_SOFT_TIME_LIMIT_SEC)
def export_task_backend(self: "CeleryTask",
                        recipient_name: str,
                        basetable: str,
                        task_pk: int) -> None:
    """
    This function exports a single task but does so with only simple (string,
    integer) information, so it can be called via the Celery task queue.

    Args:
        self: the Celery task, :class:`celery.app.task.Task`
        recipient_name: export recipient name (as per the config file)
        basetable: name of the task's base table
        task_pk: server PK of the task
    """
    from camcops_server.cc_modules.cc_export import export_task  # delayed import  # noqa
    from camcops_server.cc_modules.cc_request import command_line_request_context  # delayed import  # noqa
    from camcops_server.cc_modules.cc_taskfactory import (
        task_factory_no_security_checks,
    )  # delayed import

    try:
        with command_line_request_context() as req:
            recipient = req.get_export_recipient(recipient_name)
            task = task_factory_no_security_checks(req.dbsession,
                                                   basetable, task_pk)
            if task is None:
                log.error(
                    "export_task_backend for recipient {!r}: No task found "
                    "for {} {}", recipient_name, basetable, task_pk)
                return
            export_task(req, recipient, task)
    except Exception as exc:
        self.retry(countdown=backoff(self.request.retries), exc=exc)


@celery_app.task(bind=True,
                 ignore_result=True,
                 max_retries=MAX_RETRIES,
                 soft_time_limit=CELERY_SOFT_TIME_LIMIT_SEC)
def export_to_recipient_backend(self: "CeleryTask",
                                recipient_name: str) -> None:
    """
    From the backend, exports all pending tasks for a given recipient.

    There are two ways of doing this, when we call
    :func:`camcops_server.cc_modules.cc_export.export`. If we set
    ``schedule_via_backend=True``, this backend job fires up a whole bunch of
    other backend jobs, one per task to export. If we set
    ``schedule_via_backend=False``, our current backend job does all the work.

    Which is best?

    - Well, keeping it to one job is a bit simpler, perhaps.
    - But everything is locked independently so we can do the multi-job
      version, and we may as well use all the workers available. So my thought
      was to use ``schedule_via_backend=True``.
    - However, that led to database deadlocks (multiple processes trying to
      write a new ExportRecipient).
    - With some bugfixes to equality checking and a global lock (see
      :meth:`camcops_server.cc_modules.cc_config.CamcopsConfig.get_master_export_recipient_lockfilename`),
      we can try again with ``True``.
    - Yup, works nicely.

    Args:
        self: the Celery task, :class:`celery.app.task.Task`
        recipient_name: export recipient name (as per the config file)
    """
    from camcops_server.cc_modules.cc_export import export  # delayed import  # noqa
    from camcops_server.cc_modules.cc_request import command_line_request_context  # delayed import  # noqa

    try:
        with command_line_request_context() as req:
            export(req, recipient_names=[recipient_name],
                   schedule_via_backend=True)
    except Exception as exc:
        self.retry(countdown=backoff(self.request.retries), exc=exc)
