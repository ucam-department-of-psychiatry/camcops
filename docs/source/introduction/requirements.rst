..  docs/source/introduction/hardware.rst

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

Requirements and costs
======================

..  contents::
    :local:
    :depth: 3


.. _hardware_requirements_client:

Android clients: hardware requirements
--------------------------------------

The minimum Android SDK version is 16, meaning Android 4.1 (‘Jelly Bean’,
released in 2012). For development, we have used:

- Asus Transformer Prime TF201 (2011, running Android 4.1.1) — nice keyboard
  with an extra battery in it, though WiFi only with no 3G connection.
  (Its charger uses a non-standard USB specification that supplies 15V, rather
  than the standard 5V, so it can fail to charge properly if you plug a random
  USB charger into it! [#asuscharger]_

- Sony Xperia Z2 tablet (2014; available in WiFi and 3G versions), with
  Bluetooth keyboard.


iOS clients: hardware requirements
----------------------------------

- We suggest an iPad or iPad mini; iPhones are probably just too small. CamCOPS
  has been tested on an iPad 2 and works fine.

- A physical (e.g. Bluetooth) keyboard is useful if you plan on using the
  clinical clerking aspects or other tasks requiring significant typing.

- Not much information is stored on the tablet (it’s shipped periodically to
  the server) so we think any model of iPad will do.


Mobile Windows clients: hardware requirements
---------------------------------------------

There are no specific Windows requirements; CamCOPS should run on any Windows
laptop.

However, the Microsoft Surface Book 2 (e.g. 13.5" display, 8 Gb RAM, i5
processor, 256 Gb SSD) is very good and provides a lightweight Windows laptop
with good battery life and a detachable touchscreen/tablet. Its default
on-screen keyboard has some layout problems (it overlays other windows, without
resizing them) but the physical keyboard is good.

.. note::

    The Surface Book 2 onscreen keyboard sometimes overlays windows, at the
    bottom of the screen. The windows in question (e.g. CamCOPS) are not
    informed about this and don't know how big the on-screen keyboard is, so
    can't do anything about it. The solution is either (a) to use the physical
    keyboard, which is much better, or (b) to remember that this isn't just a
    tablet, and resize the window!

.. todo::

    Width of dropdown boxes for dates/spinboxes is too small under Win10 in
    tablet mode.

.. todo::

    Check: ID/ED-3D "incorrect" sound not playing under Win10, even though
    "correct" sound works fine (and listed correctly in resource file, and
    working on other platorms). Investigate.


Other desktop/laptop clients: hardware requirements
---------------------------------------------------

There are no specific hardware requirements. The CamCOPS client runs on the
following desktop operating systems: Linux, Windows, and Mac OS/X.


.. _hardware_requirements_server:

Server: hardware and software requirements
------------------------------------------

There are no specific hardware requirements.

Operating system:

- Developed for Linux.

- Windows support is in development.

Web server:

- CamCOPS provides a WSGI application and tools to serve it so an internal
  TCP/IP port or (under Linux) UNIX socket; it doesn’t care which web server
  you use as the front end.

Database:

- CamCOPS uses `SQLAlchemy <https://www.sqlalchemy.org/>`_ so is fairly
  database-agnostic, though it does provide some custom date/time fields,
  currently specialized for MySQL, Microsoft SQL Server, and SQLite (though
  SQLite is for clients, not servers!).


Representative costs
--------------------

We have set up CamCOPS in the low-cost environment of a research-active
university that provides network support, with WiFi tablet access, and the
high-cost environment of an NHS institution with a secure VPN (including 3G and
WiFi access) and outsourced IT support. Here are some representative
costs, with dates, from those environments.

.. list-table::
   :widths: 10 45 45
   :header-rows: 1

   * - Component
     - Low-cost university research environment
     - High-cost NHS clinical environment

   * - Server: setup and first year
     - **£0–£1,500 approx.**
       Existing Linux server with Internet connection. SSL security certificate
       free via central university funding. Or a standard computer: e.g. Intel
       Xeon E3-blahblah 3.1 GHz, 16 Gb RAM, 2 Tb HD £793 (in 2013), plus some
       sort of keyboard/mouse/monitor, and a backup system.
     - **£5,771.81.**
       Subcontracted virtual Linux server with managed backup. SSL security
       certificate (valid for 5 years). Changes to DNS/firewall to allow access
       to the NHS server from a partner NHS organization (selectively). Total
       £4,809.84 + VAT (in 2013).

   * - Server: maintenance
     - **£0.**
       Power/network/SSL certificates via central university provision.
     - **£4,247.81.**
       Ongoing annual server support costs £3,539.84 + VAT. (This excludes SSL
       certificate renewal: £260 + VAT every 5 years, in 2013.)

   * - Each tablet: purchase and first year
     - **£360–£400 approx.**
       *One option:* Asus EeePad Transformer Prime TF201 (with keyboard): around
       £400 (in 2013).
       *Another option:* Apple iPad 2 (16 Gb, WiFi only) £329 from Apple
       (2013). Bluetooth keyboard/case: lots to choose from, but some from
       around £30.
       *Another option:* Something much cheaper.
       *Another option:* Microsoft Surface Book 2 (13.5" display, 8 Gb RAM, i5
       processor, 256 Gb SSD), touchscreen/detachable keyboard/Windows 10:
       £1,250 (in 2019). Over the top for CamCOPS, but runs all sorts of other
       things; good for the roving clinician.
     - **£1,081.**
       Apple iPad 2 (16 Gb, 3G, WiFi) £410 (inc. VAT). Bluetooth keyboard/case
       £50. MDM license £36. VPN token £315. VPN SIM £120. Support costs for
       first two years £300, i.e. £150 for first year.

   * - Each tablet: maintenance
     - **£0.**
       It doesn’t cost much to run a tablet.
     - **£150.**
       Annual support costs (inc. VAT).

   * - Software (CamCOPS, LAMP stack)
     - **£0.**
     - **£0.**


===============================================================================

.. rubric:: Footnotes

.. [#asuscharger]
   http://www.transformerforums.com/forum/asus-transformer-tf101-help/23451-solved-transformer-not-charging.html
