#!/usr/bin/env python

"""
camcops_server/tools/generate_task_factories.py

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

Script to generate skeleton Factory Boy test factories for
camcops_server/tasks/tests/factories.py

Probably not needed anymore.

"""

from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.tasks.tests import factories as task_factories


def main() -> None:
    task_dict = {}

    for cls in Task.all_subclasses_by_tablename():
        task_class_name = cls.__name__
        factory_name = f"{task_class_name}Factory"
        factory_class = getattr(task_factories, factory_name, None)
        if factory_class is None:
            task_dict[task_class_name.lower()] = task_class_name
            if issubclass(cls, TaskHasPatientMixin):
                sub_class_name = "TaskHasPatientFactory"
            else:
                sub_class_name = "TaskFactory"

            print(
                f"""
class {factory_name}({sub_class_name}):
    class Meta:
        model = {task_class_name}

    id = factory.Sequence(lambda n: n + 1)
"""
            )

    for filename, class_name in task_dict.items():
        print(f"from camcops_server.tasks.{filename} import {class_name}")


if __name__ == "__main__":
    main()
