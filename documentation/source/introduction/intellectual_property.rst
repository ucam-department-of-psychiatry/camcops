..  documentation/source/introduction/intellectual_property.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
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

.. _intellectual_property:

Intellectual property
=====================

Intellectual property includes (1) CamCOPS code itself, (2) the tasks contained
in and distributed with CamCOPS, and (3) software libraries that CamCOPS relies
on.

CamCOPS itself
--------------

.. note::
    British English: *licence* noun, *license* verb.
    American English: *license* noun and verb.

CamCOPS is free and open-source software, licensed under the GPLv3+. See
:ref:`Licences <licences_camcops>`.

Why the GPL?

- We want CamCOPS, and any derivative works, to remain free and open-source to
  all users. That requires a “copyleft” licence.

- CamCOPS uses Qt under the LGPL; See :ref:`Licences <licences_qt>`. The GPL is
  a copyleft licence compatible with the LGPL. Also, some parts of Qt are only
  available under the GPL for open-source users.

Note also:

- Popular OSI-approved open source licences: https://opensource.org/licenses

- GNU on licences: https://www.gnu.org/licenses/license-list.html

- Stallman on the GPL: https://www.gnu.org/philosophy/pragmatic.html

- Wheeler on GPL compatibility:
  https://www.dwheeler.com/essays/gpl-compatible.html

- Wikipedia on the GPL
  (https://en.wikipedia.org/wiki/GNU_General_Public_License) and on a
  comparison of free/open-source licences
  (https://en.wikipedia.org/wiki/Comparison_of_free_and_open-source_software_licenses).

2. Tasks, scales, and questionnaires distributed with CamCOPS
-------------------------------------------------------------

CamCOPS comes with several tasks, scales, and questionnaires. Their permissions
cover a spectrum:

- Some are in the public domain.

- Some were created for CamCOPS and have the same copyright/licensing
  arrangements as CamCOPS itself (see above).

- Some are subject to copyright, and are included with the prior or explicit
  permission of the copyright holder.

- Some tasks may only be used in certain settings (e.g. only in a
  non-commercial environment). CamCOPS enforces this by requiring you to
  specify the environment you are working in (see :menuselection:`Settings -->
  Intellectual property (IP) permissions`).

- Some may permit reproduction and use by some institutions but not others. For
  some such tasks, CamCOPS provides a “skeleton” task without any scale text.
  This is implemented using an XML string file. Without this file, the task is
  approximately useless, as it will just display “missing” all over the place.
  However, if an institution is legally permitted to use the scale in this way,
  it can create an XML file containing the scale test (using CamCOPS’s internal
  names for the various pieces of text)

- Some do not permit reproduction at all. However, it’s still useful to be able
  to capture data electronically! If you have a licensed copy of a paper-based
  task, then you may still wish to avoid paper capture and transcription to
  some suboptimal data management system (like Excel). For some tasks, CamCOPS
  provides a bare-bones skeleton, with prompts like “Question 1” that do not
  contain any part of the task/scale in question. This makes the CamCOPS task
  useless for anyone who doesn’t own the task in conventional form, but
  potentially useful for those that do.

- For details on each task, see their :ref:`individual descriptions
  <tasks_all>`.

3. Software libraries
---------------------

The CamCOPS app and server rely on some third-party software; see
:ref:`Licences <licences_other>`.
