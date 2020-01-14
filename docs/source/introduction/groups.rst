..  docs/source/introduction/groups.rst

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

.. _groups:

Groups
======

CamCOPS assigns each uploaded task to one *group*. Groups have the following
functions:

- Groups help to define *access control*: what information can a user see?

- A group has a pair of *ID policies*: what information about a subject/patient
  is required to (a) upload to the server, and (b) finalize that upload,
  clearing the data off the tablet?

..  contents::
    :local:
    :depth: 3


.. _group_access_control:

Access control
--------------

Users may belong to one or several groups. Users can see data from the groups
they belong to. In addition, each group may also have permission to view other
groups (and users also gain the permissions of their groups).

Users upload data to one group at a time (but can change which group that is).

To make all that concrete, here are some ways that groups can operate. Imagine a
research-active hospital. Here are some of its users:

=========== =================================== ===============================
User        Description                         Group(s) to which user belongs
=========== =================================== ===============================
Smith       Research associate                  depression_crp_study
Jones       PhD student                         depression_crp_study
Willis      Research associate                  depression_ketamine_study
Fox         PhD student                         depression_ketamine_study
Armstrong   Research associate                  healthy_development_study
Bliss       PhD student                         healthy_development_study
Cratchett   Principal investigator              depression_crp_study;
                                                depression_ketamine_study
Boxworth    Principal investigator; consultant  healthy_development_study;
                                                clinical
Amundsen    SHO                                 clinical
Richards    SpR                                 clinical
Dennis      consultant                          clinical
=========== =================================== ===============================

Suppose also that we have the following group-to-group permissions:

=========== ===================================================================
Group       … can see other group(s)
=========== ===================================================================
clinical    depression_crp_study; depression_ketamine_study
=========== ===================================================================

Then users would have the following permissions:

=========== ============================ ================================= ================================= ================
User        Can see depression CRP study Can see depression ketamine study Can see healthy development study Can see clinical
=========== ============================ ================================= ================================= ================
Smith       **yes**                      no                                no                                no
Jones       **yes**                      no                                no                                no
Willis      no                           **yes**                           no                                no
Fox         no                           **yes**                           no                                no
Armstrong   no                           no                                **yes**                           no
Bliss       no                           no                                **yes**                           no
Cratchett   **yes**                      **yes**                           no                                no
Boxworth    **yes**                      **yes**                           **yes**                           **yes**
Amundsen    **yes**                      **yes**                           no                                **yes**
Richards    **yes**                      **yes**                           no                                **yes**
Dennis      **yes**                      **yes**                           no                                **yes**
=========== ============================ ================================= ================================= ================

This example embodies these specimen principles:

- Researchers see only the patients consented into their study.

- A researcher may be part of one or several studies.

- Clinicians (members of the ``clinical`` group) can see all records, including
  research records, for patients consented into clinical research for the
  hospital (in this case: ``depression_crp_study``,
  ``depression_ketamine_study``).

- There may be some studies that don’t involve patients, so clinicians don’t
  get some sort of superuser status (in this case:
  ``healthy_development_study`` is not visible to clinicians in general).

In this example you would also probably want to ensure that the hospital’s main
clinical ID number was required for the ``clinical``, ``depression_crp_study``,
and ``depression_ketamine_study`` groups (and it would probably be optional for
the ``healthy_development_study`` group, since that might involve non-patient
volunteers who aren’t registered with the hospital).

.. note::

    CamCOPS superusers can see everything. This is an administrative role.


Identification policies
-----------------------

First, please see :ref:`Patient Identification <patient_identification>`.

Since different situations may require different identification policies,
CamCOPS lets you configure this by group. Here are some contrasting scenarios:

**Scenario 1: unitary ID policy**

Imagine an institution that has a single centralized ID system (e.g. a hospital
that only uses UK NHS numbers). It requires that all data conform to the
principle that you must always use an NHS number. It also requires that you
specify forename, surname, date of birth, and sex. You could create an ID
number type 1 that you call “NHS number”, or “NHS” for short. All CamCOPS
groups that you create might use these policies:

.. code-block:: none

    Upload and finalize:

        forename AND surname AND sex AND dob AND idnum1

**Scenario 2: multiple pseudonymous studies**

Suppose a University CamCOPS site is hosting multiple independent studies. Its
ID numbers might look like this:

=========   =========================================  =================
ID number   Description                                Short description
=========   =========================================  =================
1           MRI of adolescent development study ID     MRIAD
2           MEG of hallucinations study ID             MEGHAL
3           Affective trajectory of painters study ID  MOODPAINT
=========   =========================================  =================

Then a hypothetical ``mri_ad`` group might have these policies

.. code-block:: none

    Upload and finalize:

        sex AND idnum1

while the ``meg_hal`` group has these:

.. code-block:: none

    Upload and finalize:

        sex AND idnum2

... and so on. Each study requires its own study-specific ID but does not
require subjects to be identified in other ways.

**Scenario 3: mixture of requirements**

Let’s use the hospital scenario above. We might have the following ID number
types:

=========   =========================================  =================
ID number   Description                                Short description
=========   =========================================  =================
1           Hospital number                            H
2           NHS number                                 NHS
3           Research Healthy Development Study number  ResHealthyDev
=========   =========================================  =================

The hospital might want all studies involving patients to have fully
identifiable information, so the ``clinical``, ``depression_crp_study``, and
``depression_ketamine_study`` groups might all have the following ID policies:

.. code-block:: none

    Upload:

        forename AND surname AND dob AND sex AND (idnum1 OR idnum2)

    Finalize:

        forename AND surname AND dob AND sex AND idnum1 AND idnum2

The difference between uploading and finalizing allows clinicians some leeway
by allowing them to fetch NHS numbers later.

In contrast, the ``healthy_development_study`` might involve volunteers who
might not have a hospital number, and don’t need to know their NHS number, but
can provide it if they wish and consent to have their research records
cross-linked to their hospital or other NHS records. That group might have
these policies:

.. code-block:: none

    Upload:

        sex AND idnum3

    Finalize:

        sex AND idnum3


**Other variations**

Some clinical research studies might want to enforce their study-specific
number in addition to the hospital's common clinical identifier (such as an NHS
number).

These requirements are why CamCOPS allows an ID policy to be set for each
group. A global setting wouldn't be enough.

If still further isolation is required, additional CamCOPS instances
(databases) can be created.


Group administrators
--------------------

For a large-scale system, it can be be desirable to delegate user
management to group administrators ("groupadmins"), such that groupadmins can
manage their own users WITHOUT being able to see all records on the system.

For example, Alice may be a superuser, but Bob, Carol, Dave, and Edna all run
separate studies. Alice doesn't want to have to manage the dozens of end users,
so she makes Bob a groupadmin for his study, Carol a groupadmin for hers, and
so on. Then Alice only has to worry about setting up the groups and the
groupadmins in the first place (and perhaps rescuing groupadmins who forget
their password).

This is a bit tricky conceptually. CamCOPS implements it as follows:

- Only superusers can set groupadmin status, and create/delete groups.

- We want groupadmins to be able to add users. If they try to add a user that
  already exists, we don't want a duplicate user added (so the fact of a user's
  previous existence may become known to groupadmins). When they add a user,
  they must make that user a member of at least one group

- We can't let groupadmins delete users arbitrarily. We allow groupadmins to
  delete a user if all the users' groups were administered by this
  groupadmin. (Phrased a different way: a groupadmin can't delete a user who
  belongs to any groups that don't "belong" to the groupadmin.)

- The groupadmin can grant/revoke access for their groups only.

- As a result, some permissions are group-specific [#usergroupmembership]_:

    - login (users can login if the "login" permission is set for *any* group)

    - upload (users can upload to a group only if they have "upload" permission
      for that group)

    - register devices (similar to "upload")

    - view all patients when unfiltered (if you're in more than one group, this
      per-group setting would be applied to patients' records belonging to each
      group according to your permissions for that group)

    - may dump data (applies to data for that group only) [#nosecondhand]_

    - may run reports (also per-group) [#nosecondhand]_

    - may add notes (also per-group)

- A certain amount of crosstalk is hard to avoid, e.g. for these flags:

    - must change password (this flag is associated with a user, not a group;
      it wouldn't make sense to say that you have to change your password for
      group A but not for group B, so the outcome is that any groupadmin can
      make any of "their" users change their password).

- Groupadmins can perform user editing functions (such as altering permissions
  or resetting passwords) for users that they oversee.

- Groupadmins may not edit permissions for (or delete) other groupadmins or for
  superusers, unless they are themselves a superuser.

- Note that this leaves one other main area where the superuser may have to
  step in. Suppose Bob administers group B. Richard is in group C, and Bob
  wants to add him to group B. Bob won't be able to see or edit Richard, so the
  superuser will have to intervene. (If Bob were adding a completely new user,
  Sandra, that'd be different -- Bob could create Sandra's user and assign her
  to group B simultaneously.)


===============================================================================

.. rubric:: Footnotes

.. [#usergroupmembership]
    Implemented in the ``UserGroupMembership`` class.

.. [#nosecondhand]
    Specifically, note that there is no "second-hand" authority to dump/report.
    For example, if group G1 can "see" G2, and user U has authority to report
    on (or dump data from) G1, that authority does not extend to G2 -- even
    though U could browse tasks from G2 via the second-hand authority for that.
