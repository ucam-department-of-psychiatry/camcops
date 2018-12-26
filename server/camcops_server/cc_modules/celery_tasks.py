#!/usr/bin/env python

"""
camcops_server/cc_modules/celery_tasks.py

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

**Celery tasks.**

See also ``celery.py``.

**In general, prefer delayed imports here. Otherwise circular imports are very
hard to avoid.**

"""

import logging

from cardinal_pythonlib.logs import BraceStyleAdapter
from celery import shared_task

# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa

log = BraceStyleAdapter(logging.getLogger(__name__))


@shared_task(ignore_result=True)
def add(x: float, y: float) -> float:
    """
    Task to add two numbers. For testing!

    Args:
        x: a float
        y: another float

    Returns:
        x + y

    """
    return x + y


@shared_task(ignore_result=True)
def export_task_backend(recipient_name: str,
                        basetable: str,
                        task_pk: int) -> None:
    """
    This function exports a single task but does so with only simple (string,
    integer) information, so it can be called via the Celery task queue.

    Args:
        recipient_name: export recipient name (as per the config file)
        basetable: name of the task's base table
        task_pk: server PK of the task
    """
    from camcops_server.cc_modules.cc_export import export_task  # delayed import  # noqa
    from camcops_server.cc_modules.cc_request import command_line_request_context  # delayed import  # noqa
    from camcops_server.cc_modules.cc_taskfactory import (
        task_factory_no_security_checks,
    )  # delayed import

    with command_line_request_context() as req:
        recipient = req.get_export_recipient(recipient_name)
        task = task_factory_no_security_checks(req.dbsession,
                                               basetable, task_pk)
        export_task(req, recipient, task)


@shared_task(ignore_result=True)
def export_to_recipient_backend(recipient_name: str) -> None:
    """
    From the backend, exports all pending tasks for a given recipient.

    There are two ways of doing this, when we call
    :func:`camcops_server.cc_modules.cc_export.export`. If we set
    ``schedule_via_backend=True``, this backend job fires up a whole bunch of
    other backend jobs, one per task to export. If we set
    ``schedule_via_backend=False``, our current backend job does all the work.
    Which is best? Well, keeping it to one job is a bit simpler, perhaps, but
    everything is locked independently so we can do the multi-job version, and
    we may as well use all the workers available. So my thought was to use
    ``schedule_via_backend=True``. However, that leads to database deadlocks!
    So ``False``.

    Args:
        recipient_name: export recipient name (as per the config file)
    """
    from camcops_server.cc_modules.cc_export import export  # delayed import  # noqa
    from camcops_server.cc_modules.cc_request import command_line_request_context  # delayed import  # noqa

    with command_line_request_context() as req:
        export(req, recipient_names=[recipient_name],
               schedule_via_backend=False)
