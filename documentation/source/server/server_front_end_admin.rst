..  documentation/source/server/server_front_end_admin.rst

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

.. _website_admin:

Web site: admin functions
=========================

.. _task_admin:

Administrative options available for individual tasks
-----------------------------------------------------

In the HTML view of a task, some users will have some of these additional
options, shown at the very bottom:

Apply special note
~~~~~~~~~~~~~~~~~~

This allows you to apply a textual note to a task, which will be displayed
alongside it in the future. (For example, you could use this feature to mark a
task’s content as disputed, if you are prohibited by policy from deleting
data.)

The note will be visible when viewing all predecessor/successor versions of the
same record.

.. _edit_patient:

Edit patient details
~~~~~~~~~~~~~~~~~~~~

This allows you to edit the patient record for this task, and others created
alongside it on the same client device (e.g. if someone has misspelled a name).
The option is only available for finalized tasks.

Erase task instance
~~~~~~~~~~~~~~~~~~~

This deletes the task’s data (leaving the empty task structure as a
placeholder). Predecessor/successor versions are also erased. Other tasks for
the same patient will not be affected.

Erasure is prohibited for non-finalized tasks (for one thing, the tablet might
re-upload the record). Finalize the records from the tablet (or, if you
absolutely must, :ref:`force-finalize <force_finalize>` them from the server)
first.

When might one want to erase a task? See :ref:`Delete patient entirely
<delete_patient>`.

Group administrator options
---------------------------

These options, on the main menu, are only available to users who are marked as
administrators for one or more groups.

View/manage users
~~~~~~~~~~~~~~~~~

Superusers can add, edit, and delete all users.

Group administrators can add users to their group, and edit/delete users who
are in a group that they administer.

More specifically, you may edit any user if you are a superuser. Otherwise, you
may edit a user if (1) they are not a superuser or group administrator, and (2)
you are a group administrator for a group that they’re in.

The following are *user* attributes:

- username
- password, and whether this must be changed at next login
- full name
- email
- group membership(s)
- which group the user will currently upload into
- superuser status

The following are attributes of the *user—group association*, i.e. apply
separately to each group the user is in:

- permission to upload from tablets and other client devices
- permission to register tablet/client devices
- permission to log in to the server’s web front end
- permission to browse records from all patients when no patient filter is set
  (if disabled, no records appear in this circumstance)
- permission to perform bulk research data dumps
- permission to run reports
- permission to add special notes to tasks

When adding a user, make sure you give them permission to log in, for at least
one group, if you want them to be able to use the web front end! (You don’t
have to do this, though – for example, some users may have permission only to
upload from tablets, not use the server web interface.)

.. note::

    Groupadmins can’t currently change passwords for their users, but the
    editing screen makes it look like they should. And they should, probably;
    that would be tedious for the superuser otherwise. TODO: Fix this.

.. _delete_patient:

Delete patient entirely
~~~~~~~~~~~~~~~~~~~~~~~

This allows you to delete a patient (as identified by an ID number of your
choosing) from a specified group. **All tasks belonging to this patient are
deleted.** This operation is IRREVERSIBLE, so a number of confirmation steps
are required.

.. note::

    **When should records be deleted?**

    This can a complex question. To delete clinical records in the UK, one must
    know the age of the records (e.g. destruction after 30 years), but also
    factors such as whether the patient had a mental disorder within the
    meaning of the Mental Health Act 1983 [#mha]_, or died whilst in the care
    of an NHS organization. See UK Department of Health, 2006, Records
    Management: NHS Code of Practice [#nhsrecmancop]_.

    CamCOPS allows you to view records created before a certain date (e.g.
    created more than 30 years ago), by specifying a suitable end date in the
    search criteria, and for privileged users, this can be done across all
    patients.

    The other criteria for deletion (e.g. mental disorder, death) are outside
    the scope of CamCOPS.

.. _force_finalize:

Forcibly preserve/finalize records for a device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Client devices (tablets, or desktop clients) should finalize their own records.
“Finalizing” means saying to the server “I have finished editing these; they’re
all yours.” Tablets erase tasks locally when they finalize them (to minimize
the amount of information stored on mobile devices), though they sometimes keep
a copy of patient/subject identifiers to save typing later if the same patients
will be re-assessed.

If a device is somehow disrupted – broken, CamCOPS uninstalled, device lost
[#devicelost]_ – then you might need to tell the server that the client will no
longer be editing these data. That’s what “forcibly finalizing” is.

After force-finalizing, the finalized versions will be treated as distinct from
any remaining on the tablet, if the tablet is later rescued.

The option will allow you to proceed even if the patient identification does
not meet the necessary requirements; see also the facility to :ref:`edit
patient details, above <edit_patient>`.

Superuser options
-----------------

These options are only available to users with the superuser flag set.

.. _view_manage_groups:

View/manage groups
~~~~~~~~~~~~~~~~~~

This option allows you to define ID policies for groups, and to configure which
groups have intrinsic permission to see which other groups (if any). See
:ref:`Groups <groups>`.

View audit trail
~~~~~~~~~~~~~~~~

View the CamCOPS audit trail (optionally, filtering it according to a range of
criteria).

Internally, this audit trail is stored in the `_security_audit` table.

View HL7 message log
~~~~~~~~~~~~~~~~~~~~

View a log of outbound HL7 messages that CamCOPS has sent (along with their
success/failure status).

.. todo:: The HL7 implementation is currently disabled. This needs fixing.

View HL7 run log
~~~~~~~~~~~~~~~~

View a log of HL7 runs. A run is when CamCOPS checks to see if any HL7 messages
should be sent. Each message belongs to a run. An individual run may cause
zero, one, or many messages to be sent.

View/edit ID number definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS supports multiple simultaneous ID numbers. For example:

=============== =========================== =================
ID type number  Description                 Short description
=============== =========================== =================
1               NHS number                  NHS
2               CPFT RiO number             CPFT
3               CUH MRN                     CUH
4               Smith group research ID     RIDSmith
99              Jones group research ID     RIDJones
=============== =========================== =================

You can create and edit these definitions here. When you edit them, there are a
few additional options for HL7 messaging.

Edit server settings
~~~~~~~~~~~~~~~~~~~~

You can set the server’s master database title here. The title is displayed to
all users using the database.

Developer test page
~~~~~~~~~~~~~~~~~~~

This is a page offering server test options; it’s not for general use.

Settings
--------

Show database/server settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows the server’s ID number definitions, which extra string families are
present, and which tasks the server knows about.

Change password
~~~~~~~~~~~~~~~

This should be self-explanatory!

Choose group into which to upload data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When one of your tablets or other client devices (i.e. a client device using
your username) uploads data to this CamCOPS server, it will store its patient
and task details in a group. Which group should this be? You get to choose
here, from the groups that you are a member of (and have permission to upload
into).

Show your user settings
~~~~~~~~~~~~~~~~~~~~~~~

This shows details about your user (including group memberships).


.. rubric:: Footnotes

.. [#devicelost]
    A disaster; you should hope that the device was encrypted and be slightly
    relieved that CamCOPS data itself is.

.. [#mha]
    UK Mental Health Act 1983:
    https://www.legislation.gov.uk/ukpga/1983/20/contents. UK Mental Health Act
    2007: https://www.legislation.gov.uk/ukpga/2007/12/contents.

.. [#nhsrecmancop]
    UK Department of Health, 2006, Records Management: NHS Code of Practice:
    https://www.gov.uk/government/publications/records-management-code-of-practice-for-health-and-social-care
