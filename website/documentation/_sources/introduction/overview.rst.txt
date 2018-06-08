..  documentation/source/overview/overview.rst

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


Overview
========

CamCOPS is:

- an application that runs on tablet devices including **iPads, Android
  tablets, and desktop computers (Linux, Windows, iOS)**.

- It offers many well-known questionnaires and more advanced tests relevant to
  **cognitive and psychiatric assessment**.

- It is intended for clinical research by qualified professionals.

- It offers structured and unstructured **clinical record-keeping** facilities.

- It operates **offline**, so it can be used in places with no network
  reception.

- It is compatible with UK NHS information security standards (though security
  is multifaceted and you will need to do extra things to meet these security
  requirements).

- It periodically sends its data to a server of yours, which you control.

- The server offers a web ‘front end’ (including printable task summaries,
  quantitative tracking information, and clinical summary views), a relational
  database ‘back end’ for powerful statistical analysis, and automatic export
  facilities including HL7- and file-based export of structured data or PDFs.

Additionally,

- it’s open-source, so you can download and modify the source code. If you’re
  a programmer, it’s very easy to add your own tasks.

Internally,

- the client app is written using C++ using Qt, an open-source cross-platform
  framework.

- The server is written in Python and will run on any suitably configured web
  server.
