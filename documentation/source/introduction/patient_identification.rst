..  documentation/source/introduction/patient_identification.rst

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

.. _patient_identification:

Patient/subject identification in CamCOPS
=========================================

Overview
--------

CamCOPS is intended for use in a variety of situations, ranging from anonymous
or pseudonymous use (in which subjects are identified only by a code) through
to full identifiable clinical data (in which subjects must typically be
identified by multiple identifiers for safety).

We can use the phrase **“identification policy”** to describe what set of
information is required in a particular scenario.

A single instance of CamCOPS supports multiple **groups**, and each group can
have its own identification policies. Thus, for example, a pseudonymous
research study can co-exist with identifiable records. See
:ref:`Groups <groups>` for more detail.

Patient identification fields
-----------------------------

CamCOPS includes the following patient identification/information fields. Not
all need be used.

- Forename
- Surname
- Date of birth
- Sex (one of: M, F, X)
- ID numbers(s), which are flexibly defined (see below)
- (\*) Address (free text)
- (\*) General practitioner’s (GP’s) details (free text)
- (\*) Other details (free text)

All except those marked (\*) may be selected as part of the minimum patient
identification details. What counts as the minimum is configurable.
Furthermore, the meaning of the ID numbers is entirely configurable. Below we
explain the purposes of this system.

When writing an ID policy, use the following terms:

============  ==============================================================
Term          Meaning
============  ==============================================================
forename      Forename
surname       Surname
dob           Date of birth
sex           Sex
idnum\ *<n>*  The ID number of type *n*, e.g. idnum3 means ID number type 3
anyidnum      Whether any ID number type is present
============  ==============================================================

Configuring the meaning of the ID number fields
-----------------------------------------------

Your institution will use one or more ID number fields. For example, in the UK
NHS, every patient should have a unique nationwide NHS number. Most NHS
institutions use their own ID as well, and some specialities (such as liaison
psychiatry) operate in multiple hospitals. Research studies may use a local,
idiosyncratic numbering system. Configure the meanings of up to 8 numbering
systems (see server configuration.)

The first ID number is special in only one way: the web viewer’s drop-down ID
selector will default to it. So, pick your institution’s main ID number for
this slot; that will save your users some effort.

.. todo:: Have the default ID number type configurable per group?

Uploading and finalizing policies
---------------------------------

The server supports two ID policies: an upload policy – the minimum set of
identifying information required to upload information to the server – and a
finalizing policy – the minimum set of identifying information required for a
tablet to “sign off” and transfer all its information to the server (after
which the tablet app can’t edit that information).

The policies you require depend on your institution. Some examples are given
below.

You can configure the policies using brackets ( ), AND, OR, and any of the
fields listed above (except those marked \* above). Some examples are shown
below. Configure the policies using the :ref:`View/manage groups
<view_manage_groups>` option on the server main menu.

Examples
--------

Example 1: clinical, multi-site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose we have a mental health NHS Trust – call it CPFT – with its own
hospitals that provides liaison psychiatry services in four other hospitals. We
might use the following IDs:

=========   =============================   =================
ID number   Description                     Short description
=========   =============================   =================
1           CPFT RiO number                 CPFT RiO
2           NHS number                      NHS
3           CPFT M number                   CPFT M
4           Addenbrooke’s number            Add
5           Papworth number                 Pap
6           Hinchingbrooke number           Hinch
7           Peterborough City Hosp number   PCH
=========   =============================   =================

and these policies:

*Upload policy*

.. code-block:: none

   forename AND surname AND dob AND sex AND anyidnum

*Finalize policy*

.. code-block:: none

    forename AND surname AND dob AND sex AND idnum1

This would allow users to enter information while sitting in Addenbrooke’s
Hospital and in possession of the forename, surname, DOB, sex, and
Addenbrooke’s hospital number. Equally, the same would be true at any other of
the hospitals; or the NHS number could be used.

The user could then print out the information (from the CamCOPS webview PDFs)
for the Addenbrooke’s records, or store an electronic copy.

Once back at a CPFT office, the CPFT number(s) could be looked up, or created,
and entered into the CamCOPS tablet application (by editing that patient’s
details).

Only once this is done will the CamCOPS software allow a “final” upload (an
upload that moves rather than copies).

“Final” records would then conform to a hypothetical CPFT policy of requiring a
CPFT RiO number for each record, as well as basic information (forename,
surname, DOB, sex).

An alternative organization might standardize upon NHS numbers instead, and
edit its finalizing policy accordingly.

Example 2: research
~~~~~~~~~~~~~~~~~~~

Suppose we’re operating in a very simple research context. We don’t want
patient-identifiable data on our computers; we’ll operate with pseudonyms
(codes for each subject). We might have a separate secure database to look up
individuals from our pseudonyms, but that is outside CamCOPS. We might have the
following identifiers:

=========   ==================  =================
ID number   Description         Short description
=========   ==================  =================
1           Research ID number  RID
=========   ==================  =================

*Upload policy*

.. code-block:: none

   sex AND idnum1

*Finalize policy*

.. code-block:: none

    sex AND idnum1

This requires users to enter the subject’s sex and research ID only.

Example 3: research hosted by a clinical institution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose you’re a research group operating within a clinical institution, but
collecting data (under appropriate ethics approval) for research purposes. You
may want to use patient-identifiable data or pseudonyms. You will want full
read access to your data (likely at the SQL level), but you shouldn’t have full
read access to all patients at that institution.

There are at least three possible approaches. You could set up a new server, or
you could add a second CamCOPS database to your existing server, or you can
simply add a new group to your CamCOPS server. The last is likely to be
quickest and best.


Minimum details required by the tablet software
-----------------------------------------------

The tablet’s internal minimum identification policy, which is fixed, is:

.. code-block:: none

    sex AND ((forename AND surname AND dob) OR anyidnum)

This allows either a named (forename, surname, DOB, sex) or an
anonymous/pseudonym-based system for research (sex plus one ID number), or any
other sensible mixture as above.
