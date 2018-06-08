..  documentation/source/misc/known_problems.rst

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


Known problems: client
======================

Problems directly relating to the CamCOPS client
------------------------------------------------

Problems relating to third-party software
-----------------------------------------

Qt: QLabel height
~~~~~~~~~~~~~~~~~

It seems likely that the Qt function `QLabel::heightForWidth()` sometimes gets
heights wrong for some stylesheets, leading to excessive vertical height. See
`labelwordwrapwide.cpp` (and to see the problem: try the demo `QuMcqGrid`). I
think I’ve largely compensated for this, though.

Spinboxes are relatively poor for entering numbers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The spinbox numerical entry fields are weak in terms of NULL values. This is an
intrinsic weakness in Qt’s `QSpinBox` and `QDoubleSpinBox` that works like this:

- if you send a null value to a `QSpinBox`, it’ll typically show its minimum
  value; for example, for the range 5–10, if you send it 0, it’ll show 5.

- If you then delete the “5” and retype “5”, it doesn’t generate any “changed”
  signals, either via its string or its integer signals. Therefore, this change
  isn’t detected by the `QuSpinBoxInteger` or `QuSpinBoxDouble` framework. You
  have to delete it, replace it with something else, and re-enter it, for the
  change to be noticed and the yellow NULL indicator to disappear.

There’s no clear way round this, except that `QuLineEditInteger` and
`QuLineEditDouble` do a better job.

QuPickerInline is visually a bit suboptimal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The width requirements of `QuPickerInline` are a bit much, but then it’s also a
bit duff visually compared to `QuPickerPopup`.

Qt: ScrollMessageBox scrolling under Android
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Under Android, `ScrollMessageBox` scrolls with multi-finger gestures but not
with single-finger swipes, even though the single-finger gestures work fine
elsewhere. This also varies with device, e.g. Asus Transformer Prime TF201
requires a two-finger swipe in `ScrollMessageBox`, whereas Samsung Galaxy S5 (?)
provides a one-finger swipe. See my thoughts in `uifunc::applyScrollGestures()`.
See also https://forum.qt.io/topic/62385/one-finger-swipe-gestures and
https://bugreports.qt.io/browse/QTBUG-40461.

Qt: cursor positioning bug under Android
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, copy/paste selection cursors appear on screen far removed from the
text they relate to. This is a Qt bug; see
https://bugreports.qt.io/browse/QTBUG-58503. Related Qt bugs include
QTBUG-34867, QTBUG-58700.

Also potentially related to this: when `LogBox` or `LogMessageBox` are used with
`word_wrap = true` on Android, the touch-to-scroll goes wrong. These classes
use a `QPlainTextEdit`.

Qt: expand/collapse arrows in tree views are too small on high-DPI screens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The arrow markers for the diagnostic trees don’t scale with DPI. See discussion
in `diagnosticcodeselector.cpp`; the problem is that it’s not obvious how to set
them programmatically. In fact, this is very hard indeed; see also my attempts
in `TreeViewProxyStyle` and `TreeViewControlDelegate`, neither of which can
make the changes where they’re needed. Reported as a bug:
https://bugreports.qt.io/browse/QTBUG-62323.

Potential Qt performance bug; not recently verified; may have gone
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes there is a delay after clicking on a `QuBoolean` with an image, like
the picture-naming in the ACE-III. The delay occurs whether you click the
boolean indicator (with its “you are touching me” shading) or the image. It
seems to occur only if the main window is not maximized. The delay is in calling
`AspectRatioPixmap::mousePressEvent`, for example. Using `#define
DEBUG_CLICK_TIMING` shows that the delay is not because the widget's overridden
`sizeHint` (etc.) code is being called. I’m not sure that this is a problem in
my code. Not retested recently; other things have also improved performance
(e.g. threaded database writes).

VerticalScrollArea layout
~~~~~~~~~~~~~~~~~~~~~~~~~

`VerticalScrollArea` is nearly perfect. I’m unclear if any residual minor error
relates to `VerticalScrollArea` itself, or to misreporting of ideal height by
e.g. `GridLayoutHfw`. (Example: PDSS [with no task strings]?) (Note: it’s
sometimes worth trying to un-maximize then maximize the window; the error can
sometimes go away.)

Update 2017-07-09: I think this is fixed now.

Known problems: server
=======================

Problems directly relating to the CamCOPS server
------------------------------------------------

Problems relating to the web server framework
---------------------------------------------

“Proxy error” or “Website unavailable” whilst downloading big files through Apache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you perform a very slow operation, creating a very large file to download,
the time it takes CamCOPS to respond might exceed the timeout set by Apache. The
Apache logs might show an error like “Internal error: proxy: error reading
status line from remote server”.

The first thing to check is the gunicorn configuration: to your `camcops
serve_gunicorn` command, try adding e.g. `--timeout 300` (an increase from the
default of 30 s).

This might just change the Apache error to “The timeout specified has expired:
proxy: error reading...”, in which case you should also edit the Apache
configuration file to add e.g. `ProxyTimeout 300`.

Then restart CamCOPS and Apache.

Problems relating to other third-party software
-----------------------------------------------

Warnings during “camcops merge_db” relating to the “mysqldb” driver and UTF-8
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If, during a `camcops merge_db` command using the mysqldb driver (a database URL
like `mysql+mysqldb://...`), you get errors like this:

::

    2017-08-25 22:27:23.234 cardinal_pythonlib.sqlalchemy.merge_db:INFO: Processing table 'blobs' via ORM class <class 'camcops_server.cc_modules.cc_blob.Blob'>
    /home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/sqlalchemy/engine/default.py:504: Warning: (1300, "Invalid utf8 character string: '89504E'")
        cursor.execute(statement, parameters)
    /home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/sqlalchemy/engine/default.py:504: Warning: (1300, "Invalid utf8 character string: 'FFD8FF'")
        cursor.execute(statement, parameters)

… or like this, with the charset set to ‘utf8mb4’ for the database and SQLAlchemy URL:

::

    2017-08-25 22:38:36.628 cardinal_pythonlib.sqlalchemy.merge_db:INFO: Processing table 'blobs' via ORM class <class 'camcops_server.cc_modules.cc_blob.Blob'>
    /home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/sqlalchemy/engine/default.py:504: Warning: (1300, "Invalid utf8mb4 character string: '89504E'")
        cursor.execute(statement, parameters)
    /home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/sqlalchemy/engine/default.py:504: Warning: (1300, "Invalid utf8mb4 character string: 'FFD8FF'")
        cursor.execute(statement, parameters)

… then this is likely a mysqldb bug. Potentially related problems:

- https://bitbucket.org/zzzeek/sqlalchemy/issues/3291/problem-using-binary-type-with-foreign-key
- https://bitbucket.org/zzzeek/sqlalchemy/issues/3804/invalid-utf8-character-string-warning-on
- https://github.com/PyMySQL/mysqlclient-python/issues/81
- https://github.com/PyMySQL/mysqlclient-python/pull/106

The problem goes away using “pymysql” rather than “mysqldb”, so try this:

::

    DB_URL = mysql+pymysql://username:password@127.0.0.1:3306/database?charset=utf8mb4

Missing file in Deform package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exceptions/warning occur as follows:

::

    pyramid.httpexceptions.HTTPNotFound: https://127.0.0.1:8000/deform_static/fonts/glyphicons-halflings-regular.woff2

Reason: CamCOPS correctly registers a static view at `/deform_static` which
refers to `deform:static/`; this means “look within the ‘deform’ package for the
directory `static/`”. This is correct. The file
`glyphicons-halflings-regular.woff2` is simply missing from the `static/fonts`
directory in deform==2.0.4. Similar problems elsewhere:
https://github.com/aspnet/Home/issues/959.

Solution implemented: fetch the file from
http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.2/fonts/glyphicons-halflings-regular.woff2
and route from `/deform_static/fonts/glyphicons-halflings-regular.woff2`
to a manual view providing the file.

There’s another bootstrap symbol debugging file missing, but I’ve not bothered
with that one yet (I’m not sure exactly which version is required).
