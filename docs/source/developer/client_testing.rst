..  docs/source/developer/client_testing.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.


.. _Qt Test: https://doc.qt.io/qt-6.5/qtest-overview.html


Testing the client code
=======================

The C++ client code on the server is tested with:

- `Qt Test`_ C++ tests
- the in-app tests under :menuselection:`Settings --> CamCOPS self-tests`
- the :ref:`Demonstration task <demoquestionnaire>`

The `Qt Test`_ C++ tests are kept separate to the code they are testing in the ``tests/auto`` sub-folder of ``tablet_qt``.
So for example, the tests for ``tablet_qt/lib/convert.cpp`` are tested by ``tablet_qt/tests/auto/lib/testconvert.cpp``.


To build all of the tests:

  .. code-block:: bash

      cd /path/to/camcops
      mkdir build-qt6-tests
      cd build-qt6-tests
      /path/to/qt_install/bin/qmake ../tablet_qt/tests
      make

Then for example to run the lib/convert tests:

  .. code-block:: bash

      auto/lib/convert/bin/test_convert

To run all the tests:

  .. code-block:: bash

      find . -path '*/bin/*' -type f -exec {} \;

If Qt reports missing dependencies, try:

  .. code-block:: bash

      export QT_DEBUG_PLUGINS=1

A handy one-liner for building and running a test, reporting success or failure:

  .. code-block:: bash

      /path/to/qt_install/bin/qmake ../tablet_qt/tests && make && auto/lib/convert/bin/test_convert; if [ "$?" == "0" ]; then notify-send "Passed"; else notify-send "Failed"; fi
