#!/usr/bin/env python

"""
camcops_server/cc_modules/celery.py

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

**Celery app.**

Basic steps to set up Celery:

- Our app will be "camcops_server.cc_modules".
- Within that, Celery expects "celery.py", in which configuration is set up
  by defining the ``app`` object.
- Also, in ``__init__.py``, we should import that app.
- That makes ``@shared_task`` work in all other modules here.
- Finally, here, we ask Celery to scan ``tasks.py`` to find tasks.

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

"""

import logging
from typing import Any, Dict

from cardinal_pythonlib.logs import BraceStyleAdapter
from celery import Celery, current_task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

CELERY_APP_NAME = "camcops_server.cc_modules"
CELERY_TASKS_MODULE = "celery_tasks"
# ... look for "celery_tasks.py" (as opposed to the more common "tasks.py")


# =============================================================================
# Configuration
# =============================================================================

def get_celery_settings_dict() -> Dict[str, Any]:
    """
    This function is passed as a callable to Celery's ``add_defaults``, and
    thus is called when needed (rather than immediately).
    """
    log.debug("Configuring Celery")
    from camcops_server.cc_modules.cc_config import get_default_config_from_os_env  # delayed import  # noqa
    config = get_default_config_from_os_env()

    schedule = {}  # type: Dict[str, Any]
    for crontab_entry in config.crontab_entries:
        recipient_name = crontab_entry.content
        schedule_name = "export_to_{}".format(recipient_name)
        log.info("Adding regular export job {}: crontab: {}",
                 schedule_name, crontab_entry)
        schedule[schedule_name] = {
            "task": "camcops_server.cc_modules.celery_tasks.export_to_recipient_backend",  # noqa
            "schedule": crontab_entry.get_celery_schedule(),
            "args": (recipient_name, ),
        }

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
celery_app.autodiscover_tasks([CELERY_APP_NAME],
                              related_name=CELERY_TASKS_MODULE)

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
    log.info("self: {!r}".format(self))
    log.info("Backend: {}".format(current_task.backend))


@celery_app.task
def debug_task_add(a: int, b: int) -> int:
    """
    Test as follows:

    .. code-block:: python

        from camcops_server.cc_modules.celery import *
        debug_task_add.delay()
    """
    result = a + b
    log.info("a = {}, b = {} => a + b = {}", a, b, result)
    return result
