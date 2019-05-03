..  docs/source/developer/internationalization.rst

..  Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).
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

Internationalization
--------------------

Overview of the Qt translation system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Begin by editing the Qt project file to add a ``TRANSLATIONS`` entry.

  Qt suggests looking up languages via ``QLocale::system::name()`` (see
  https://doc.qt.io/qt-5/internationalization.html). This
  (https://doc.qt.io/qt-5/qlocale.html#name) returns a string of the form
  ``language_country`` where ``language`` is a lower-case two-letter ISO-639
  language code (i.e. ISO-639-1), and ``country`` is an uppercase, "two- or
  three-letter" ISO 3166 country code. Thus, for example: ``en_GB`` (English,
  United Kingdom of Great Britain and Northern Ireland); probably ``da_DK``
  (Danish, Denmark).

  See

  - https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
  - https://en.wikipedia.org/wiki/ISO_3166

  Though the more common format appears to be ``language-country``, Qt Linguist
  prefers and auto-recognizes the underscore version.

  - https://en.wikipedia.org/wiki/IETF_language_tag
  - https://witekio.com/de/blog/qt-internationalization-arabic-chinese-right-left/

  For example, to add Danish:

  .. code-block:: none

    TRANSLATIONS = translations/camcops_da_DK.ts

  These files live in the source tree, not the resource file.

- Run ``qmake``.

- ``lupdate`` scans a Qt project and updates a ``.ts`` translation file.
  In Qt Creator, run :menuselection:`Tools --> External --> Linguist --> Update
  Translations (lupdate)`

  - ``.ts`` translation files are XML.
  - Qt bug as of 2019-05-03: C++11 raw strings generate the error "Unterminated
    C++ string"; https://bugreports.qt.io/browse/QTBUG-42736; fixed in Qt
    5.12.2

- The Qt Linguist tool edits ``.ts`` files.

  - Class-related strings appear helpfully in against their class.
  - Free-standing strings created with ``QObject::tr()`` appear against
    ``QObject``.
  - However, ``lupdate`` looks like it reads the C++ in a fairly superficial
    way; specifically, it will NOT find strings defined this way:

    .. code-block:: cpp

        #define TR(stringname, text) const QString stringname(QObject::tr(text))
        TR(SOMESTRING, "some string contents");

    but will find this semantically equivalent version:

    .. code-block:: cpp

        const QString SOMESTRING(QObject::tr("some string contents"));

    See also https://doc.qt.io/archives/qq/qq03-swedish-chef.html.


Implementing translatable strings in C++
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Note also in particular that for obvious initialization order reasons,
  ``QObject::tr()`` doesn't help with static variables. See e.g.
  https://stackoverflow.com/questions/3493540/qt-tr-in-static-variable.
  So, options include:

  - if used in one place in the code, just use ``tr()`` from within a
    ``Q_OBJECT`` class, e.g.

    .. code-block:: cpp

        void doSomething()
        {
            // ...
            alert(tr("You need to draw on the banana!"));
        }

  - if used multiple in one function, e.g.

    .. code-block:: cpp

        void doSomething()
        {
            const QString mystring(tr("Configure ExpDetThreshold task"));
            // ...
        }

  - if used repeatedly from different places, consider a static member
    function, e.g.

    .. code-block:: cpp

        // something.h

        class Something
        {
            Q_OBJECT
            // ...
        private:
            static QString txtAuditory();
        }


        // something.cpp

        QString Something::txtAuditory()
        {
            return tr("Auditory");
        }

    ... which appears in the right class in Qt Linguist.

- You are likely to need to re-run ``qmake`` before ``lupdate`` (or, for
  example, it can fail to pick up on namespaces).


Setting up the translation system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See code.


Making the binary translation files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Run ``lrelease``, e.g. from within Qt Creator as :menuselection:`Tools -->
  External --> Linguist --> Release Translations (lrelease)`. This converts
  ``.ts`` files to ``.qm`` files.

- You need to add the ``.qm`` files to your resources.

- As always, the ``:/`` prefix in a filename, or ``qrc:///`` for a URL, points
  to the resources.


CamCOPS language rules
~~~~~~~~~~~~~~~~~~~~~~

- Code: English.
- Qt debugging streams: English.
- Command-line text: English.
- Everything else: translatable.
