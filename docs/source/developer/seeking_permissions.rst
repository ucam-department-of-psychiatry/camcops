..  docs/source/developer/seeking_permisssions.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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


Seeking permissions
-------------------

It is critical that task content does not enter the CamCOPS code base
(repository) without appropriate permissions.

Developers should **document ownership and permissions carefully**, including
dates of correspondence etc. Most things that are written are subject to
copyright, so a lack of copyright information usually means you have to hunt
for the owner, not that there isn't one!

**If in doubt about permissions for open-source reproduction, but you're sure
your institution is allowed to reproduce it, keep task content separate and
install it on a per-institution basis.**

Here's a specimen e-mail seeking permission from a copyright holder:

    Dear **XXX**,

    We are very interested in incorporating **XXX_TASK_XXX** into CamCOPS
    (https://camcops.readthedocs.io/), and wonder whether you might permit
    this.

    Our understanding of the copyright status of **XXX_TASK_XXX** is:

    * **details: who owns the copyright?**
    * **details: what are the known licensing terms?**

    May we ask if that is correct?

    CamCOPS is free and open-source software for capturing structured data
    relevant to psychiatry directly from patients, clinicians, and researchers.
    It was developed in the University of Cambridge, UK, and is in use for
    clinical and research purposes. Data flow is entirely under the control of
    the hosting institution. CamCOPS implements both open/free tasks and
    closed/restricted tasks using one of the following methods:

    - Open/free tasks are embedded into CamCOPS directly; this is our preferred
      method.

    - Some tasks may be permitted to some institutions but not others. These
      can be implemented via a public "skeleton" in CamCOPS (with no task
      content) and a "plugin" containing the task content (e.g. text for a
      questionnaire) that licensed users can add to their CamCOPS installation,
      converting the skeleton into a fully working copy.

    - Some closed tasks do not permit electronic reproduction. Sometimes, these
      still benefit from an electronic data capture "skeleton" that never
      includes task content, but is still preferable to paper capture and
      manual (laborious and error-prone) transcription. The electronic skeleton
      can then be used in conjunction with a licensed paper copy of the task.

    In addition, all CamCOPS tasks can be restricted if necessary according to
    flags that the end user can set: clinical use? Research use? Educational
    use? Commercial use? For example, a task can be restricted to noncommercial
    use only (though this relies on end-user honesty and end-user liability).

    Would it be permissible for us to incorporate **XXX_TASK_XXX** into
    CamCOPS? We'd be most grateful.

    Thank you for your time in considering this.

    Yours sincerely,

    **XXX**
