..  docs/source/privacy.rst

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


..  This doesn't work (relative path problem):
.. .. include:: ./user_client/include_tabletdefs.rst
..    Instead:

..  |anonymous| image:: _app_icons/anonymous.png
    :align: middle
    :height: 24px
    :width: 24px

..  _AES-256: https://en.wikipedia.org/wiki/Advanced_Encryption_Standard
..  _HTTPS: https://en.wikipedia.org/wiki/HTTPS
..  _URL: https://en.wikipedia.org/wiki/URL


Privacy policy
==============

..  Required documentation:
    .
    Google Play Store:
    https://support.google.com/googleplay/android-developer/topic/9877467
    .
    Apple App Store:
    https://developer.apple.com/app-store/review/guidelines/#privacy

..  contents::
    :local:
    :depth: 3


Where will my data go?
----------------------

**To the institution asking you to use CamCOPS, and only to that institution.**

CamCOPS is a tool for organizations (such as health care organizations or
universities conducting research) to collect information from people that trust
that organization.

When you install CamCOPS, you choose a **server** that you wish to use, by
entering a URL_. This server might belong, for example, to a health care
organization or a university conducting research. We'll call this organization
the **Data Controller**, or Controller for short. "Data controller" is the
legal term used within the UK [#dpa]_ and the European Union [#gdpr]_.

You can use CamCOPS to enter data, as requested by the Controller. CamCOPS will
then send the data to the Controller's server.

CamCOPS only uses encrypted network links (HTTPS_) to send data.

**Before you enter a URL into CamCOPS, make sure you trust its owner.** You
choose which server to use. Data that you enter into CamCOPS will be sent to
that server.

**No data is sent anywhere else.** There is no "CamCOPS base". The team that
develop CamCOPS don't collect statistics from the app about how often it's
used, or who's using it, or any other information. They don't collect any data
about you at all. They are not the Data Controller.


Will my data be identifiable to the Controller?
-----------------------------------------------

**Yes, usually.**

CamCOPS can collect data in several ways.

1.  Clearly identifiable information.

    You might enter your identity details, or the Controller might have set
    things up for you by pre-entering your details. In this situation, your
    details (e.g. your name) will be visible to you when you use CamCOPS.

2.  "Pseudonymised" information.

    Alternatively, the Controller might be asking you to supply "pseudonymised"
    data (where a code or pseudonym stands for your identity). If they are
    collecting pseudonymised data, but you told them your identity at some
    point, it's possible that at least some people in the organization could
    look up your identity. Representatives of the Controller should explain
    this to you, and whether or not your data might be re-identified.

3.  Anonymised information.

    Some CamCOPS tasks are anonymous (marked with the symbol |anonymous|).
    In CamCOPS, anonymous tasks are not attached to identity information in any
    way.

You will have a relationship with the Controller, who should explain to you how
they will use your data. They should obtain your **consent** to the use of
your data, such as for health research.


What data are collected?
------------------------

CamCOPS supports lots of types of :ref:`task <tasks_all>`.

These include **questionnaires and animated tasks**. Questionnaires will
collect the information that you supply. Animated tasks will collect
information about your responses. All tasks record basic timing information,
such as when you started and finished the task.

**Some of the information might be sensitive.** CamCOPS supports tasks that
ask about health, including mental health.

Some tasks collect special types of information, if you choose, such as
**photos.** (To take photos using CamCOPS, you will need to enable "camera
permissions" in operating system that require this, such as Android.)


Does CamCOPS collect any other data?
------------------------------------

**No.**

CamCOPS only collects data that you provide directly. In particular:

- CamCOPS does NOT look for other installed apps.

- CamCOPS does NOT access your device's phone details, contacts, call logs,
  calendars, or any other such data.

- CamCOPS does NOT access your device's location.

- CamCOPS does NOT capture your device's screen.

- CamCOPS does NOT track any other aspects of your usage of your device.


Before my data is sent to the Controller, is it secure on my device?
--------------------------------------------------------------------

CamCOPS collects data onto your device. As soon as possible, it moves the data
off your device and sends it to the Controller's server. In the meantime, data
that you have entered into CamCOPS (which might be identifiable and might be
sensitive) is stored on your device.

CamCOPS encrypts all its stored data with the AES-256_ encryption standard.
You need to enter your CamCOPS password (which you set) to access the CamCOPS
app.

However, the security of your device is also your responsibility. You should
keep your device safe. You should also secure your device itself
electronically, e.g. with a device password, PIN, or biometric security. For
even more security, you could consider enabling whole-device encryption via
your device's operating system.

For more details, see :ref:`Security design <security_design>`.


What will the Controller do with my data?
-----------------------------------------

That is between you and the Controller, but the Controller will have to follow
applicable laws (see below).


What rights do I have?
----------------------

Many countries provide legal rights for you to see data that's about you, check
it's accurate, withdraw your consent, and so on. It is the Controller's job
to respect these rights.

- In the European Union (EU), the legislative framework is the EU's General
  Data Protection Regulation [#gdpr]_.

- In the UK, it's the Data Protection Act (DPA) [#dpa]_.


===============================================================================

.. rubric:: Footnotes

.. [#dpa]

    UK (2018).
    Data Protection Act 2018.
    http://www.legislation.gov.uk/ukpga/2018/12/contents/enacted

.. [#gdpr]

    European Union (2016).
    Regulation (EU) 2016/679 (General Data Protection Regulation).
    *Official Journal of the European Union* L119: 1-88.
    http://ec.europa.eu/justice/data-protection/reform/files/regulation_oj_en.pdf
