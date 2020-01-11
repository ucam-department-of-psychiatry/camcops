..  docs/source/developer/internationalization.rst

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

.. _Babel: http://babel.pocoo.org/


.. _dev_internationalization:

Internationalization
--------------------

.. _dev_string_locations:

String locations in CamCOPS
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Task-specific XML files.

  These are loaded by the server (see :ref:`EXTRA_STRING_FILES
  <EXTRA_STRING_FILES>`) and downloaded by the client. They contain string
  versions in different languages.

  Client calls look like ``xstring("stringname")``, or ``xstring(STRINGNAME)``.

  Server calls look like ``req.xstring("stringname")`` or
  ``req.wxstring("stringname")``, etc. The ``w`` prefix is for functions that
  "web-safe" their output (escaping HTML special characters).

- Client/server shared strings.

  Some strings are shared between the client and the server, but are not
  specific to a given task. They are in the special ``camcops.xml`` string
  file, loaded as above.

  Client calls typically look like ``appstring(appstrings::STRINGNAME)``; the
  strings are named by constants listed in ``appstrings.h``.

  Server calls typically look like ``req.wappstring(AS.STRINGNAME)`` where
  ``AS`` is defined in ``camcops_server.cc_modules.cc_string``.

  If a string is "mission critical" for the client, then it should be built
  into the client core instead (as below).

- Client core.

  Some text does not require translation (see below).

  Text visible to the user should be within a Qt ``tr("some text")`` call. Qt
  provides tools to collect these strings into a translation file, translate
  them via Qt Linguist, and distribute them -- see below.

  Client strings that are used only once can live in the source code where they
  are used.

  Client strings that are used in several places should appear in
  ``textconst.h``.

- Server code.

  Some text does not require translation (see below).

  Text visible to the user should look like ``_("some text")``. The use of
  ``_()`` is standard notation that is picked up by internationalization
  software that scans the source code. The ``_`` function is aliased to an
  appropriate translation function, usually via ``_ = req.gettext``. A
  per-request system is used so that different users of the web site can
  operate simultaneously in different languages.

  Where text is re-used, it is placed in ``cc_text.py``. This is in general
  preferable because it allows better automatic translation mechanisms than
  the XML system.


CamCOPS language rules
~~~~~~~~~~~~~~~~~~~~~~

Hard-coded English is OK for the following:

- code
- Qt debugging stream
- command-line text
- debugging tests
- task short names (typically standardized abbreviations)
- database structure (e.g. table names, field names)
- config file settings, and things that refer to them

Everything else should be translatable.


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

  Moreover, the underscore is the standard format for **locale** (rather than
  **language** tags); the underscore is also used by POSIX and Python

  - https://en.wikipedia.org/wiki/Locale_(computer_software)
  - Python: see ``locale.getlocale()``
  - Babel insists on it (rejecting hyphens).

  **We will use the underscore notation throughout.**

  For example, to add Danish:

  .. code-block:: none

    TRANSLATIONS = translations/camcops_da_DK.ts

  These files live in the source tree, not the resource file.

- Run ``qmake``.

- ``lupdate`` scans a Qt project and updates a ``.ts`` translation file.
  In Qt Creator, run :menuselection:`Tools --> External --> Linguist --> Update
  Translations (lupdate)`

  - ``.ts`` translation files are XML.
  - **Pay close attention to error messages from lupdate.**
    In particular, ``static`` methods are fine, but classes implementing
    ``tr()`` must both (a) inherit from ``QObject`` and (b) use the
    ``Q_OBJECT`` macro.
  - However, there is a Qt bug as of 2019-05-03: C++11 raw strings generate the
    error "Unterminated C++ string";
    https://bugreports.qt.io/browse/QTBUG-42736; fixed in Qt 5.12.2.

  - To delete obsolete strings, use the ``-no-obsolete`` option; e.g.

    .. code-block:: bash

        ~/dev/qt_local_build/qt_linux_x86_64_install/bin/lupdate -no-obsolete camcops.pro

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


Tasks: xstrings
~~~~~~~~~~~~~~~

- Language-specific xstring fetch mechanism implemented.
- When the client asks for server strings, all languages are sent.


Determining the language
~~~~~~~~~~~~~~~~~~~~~~~~

- Client: the user chooses the language.

- Server: (a) there is a default server language, which also applies when the
  user is not logged in; (b) users can choose a language.


Server core
~~~~~~~~~~~

- We need to internationalize (a) Python strings and (b) Mako template strings.

  - https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/templates/mako_i18n.html
  - https://docs.pylonsproject.org/projects/pylons-webframework/en/latest/i18n.html
  - http://danilodellaquila.com/en/blog/pyramid-internationalization-howto
  - http://babel.pocoo.org/en/latest/
  - https://github.com/wichert/lingua
  - https://docs.python.org/3/library/gettext.html#class-based-api; there are
    editors for ``gettext`` systems, like

    - https://poedit.net/

      - this is a pretty good open-source one (with a paid professional
        upgrade); from Ubuntu, install with ``sudo snap install poedit``

    - https://wiki.gnome.org/Apps/Gtranslator
    - https://userbase.kde.org/Lokalize

  - https://stackoverflow.com/questions/37998300/python-gettext-specify-locale-in

- Systems like ``gettext`` and Qt's work on the basis that you write the actual
  string in the code, then translate it (rather than having an intermediate
  "lookup string name") -- clearer for developers.

- ``gettext`` is very much like Qt's system:

  - ``xgettext`` or Babel_ scans your code and extracts message catalogues,
    producing ``.po`` (Portable Object) files.

  - ``.po`` files are compiled to ``.mo`` (Machine Object) files

  - ``gettext`` loads ``.mo`` files and does the translation.

  - The convention is to use ``_("some string")`` as the notation for the
    translation function. (Is that what Babel looks for?) Thus, in Mako, the
    equivalent is ``${_("some string")}``.

- This looks like a well-established framework. Babel supports Mako.

- The difficulty is that many have a monolithic context, rather than a
  request-specific context, in which they translate.

We manage this as follows.

**Mako**

.. code-block:: none

    <% _ = request.gettext %>
    ## TRANSLATOR: string context described here
    <p>${_("Please translate me")}</p>

It would be nice if we could just put the ``_`` definition in ``base.mako``,
but that doesn't come through with ``<%inherit file=.../>``. But we can add
it to the system context via
:class:`camcops_server.cc_pyramid.CamcopsMakoLookupTemplateRenderer`. So we do.

**Generic Python**

.. code-block:: python

    _ = request.gettext
    # TRANSLATOR: string context described here
    mytext = _("Please translate me")

If an appropriate comment tag is used, either in Python or Mako (here,
``TRANSLATOR:``, as defined in ``build_translations.py``), the comment appears
in the translation files.

**Forms**

See ``cc_forms.py``; the forms need to be request-aware. This is quite fiddly.

**Efficiency**

Try e.g.

.. code-block:: bash

    inotifywait --monitor server/camcops_server/translations/da_DK/LC_MESSAGES/camcops.mo

... from a single-process CherryPy instance (``camcops_server
.serve_cherrypy``), there's a single read call only.


Updating server strings
~~~~~~~~~~~~~~~~~~~~~~~

There is a CamCOPS development tool, ``build_translations.py``. Its help is as
follows:

.. literalinclude:: build_translations_help.txt
    :language: none


.. todo::
    There are still some of the more complex Deform widgets that aren't properly translated on a per-request basis, such as

    - TranslatableOptionalPendulumNode
    - TranslatableDateTimeSelectorNode
    - CheckedPasswordWidget
