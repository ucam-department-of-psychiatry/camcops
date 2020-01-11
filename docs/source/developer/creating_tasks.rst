 ..  docs/source/client/creating_tasks.rst

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

.. _Likert: https://en.wikipedia.org/wiki/Likert_scale
.. _NHS number: http://www.datadictionary.nhs.uk/version2/data_dictionary/data_field_notes/n/nhs_number_de.asp
.. _Visual analogue scale: https://en.wikipedia.org/wiki/Visual_analogue_scale

.. include:: ../user/include_tabletdefs.rst

Creating tasks
==============

..  contents::
    :local:
    :depth: 3

Tasks on the client (tablet, desktop) are written in C++. All client tasks are
classes that inherit from the `Task` class, define their database structure,
and implement an `editor()` function that implements the task itself.
Typically, one of two methods is used:

- Simple tasks create a `Questionnaire` object and use questionnaire elements
  (described below) to capture user responses. Arbitrary logic is possible,
  both in terms of what constitutes “enough information” and in terms of page
  flow (see e.g. the :ref:`CIS-R <cisr>`).

- Complex tasks create a graphics widget and manipulate Qt graphics objects
  directly, giving arbitrary power. Examples include the :ref:`IDED3D task
  <ided3d>`.

On the server, a single Python class represents the task. It must define its
database structure and provide an HTML view on the data (used for the HTML and
PDF representations). More or less everything else is optional, but tasks may
provide numerical summary information (for trackers) or customize their
clinical text views.


Questionnaire elements
----------------------

Programmers can embed arbitrary logic in a task. Several elements are
available; all inherit from `QuElement`. Elements are grouped into pages
(`QuPage`).


Display/sound
~~~~~~~~~~~~~

These elements are primarily for static display (though, for example, the
programmer can manipulate the contents of static text dynamically).

- `QuAudioPlayer`. Allows sounds to be played.

- `QuBackground`. Widget that is styled (via CSS) to have a colour. Used to
  create striping background effects for custom tables (etc.).

- `QuHeading`. Subclass of `QuText`; displays headings.

- `QuHorizontalLine`. A horizontal rule or line.

- `QuImage`. A static image.

- `QuSpacer`. A fixed-size spacer.

- `QuText`. Static text.


User input
~~~~~~~~~~

- `QuBoolean`. An element to control a single boolean (0/1/NULL) field. It may
  display text or an image. The text may appear as a button or with an adjacent
  widget. Some possible appearances:

  - Unselected (NULL): |check_unselected| or :unselectedtext:`Option`

  - Unselected (NULL) and required: |check_unselected_required| or
    :missingtext:`Option`

  - False: |check_false_black| or |check_false_red| or :unselectedtext:`Option`

  - True: |check_true_black| or |check_true_red| or :selectedtext:`Option`

- `QuButton`. A button, used to execute arbitrary code.

- `QuCanvas`. A canvas for sketching, which can take a default or background
  image.

- `QuCountdown`. A countdown timer.

- `QuDateTime`. Date/time input method.

- `QuDiagnosticCode`. Allows searching and selection of diagnostic codes using
  a recognized system (e.g. :ref:`ICD-10 <diagnosis_icd10>`).

- `QuLineEdit`. One-line text editor. (For a bigger version, see `QuTextEdit`.)

- `QuLineEditDouble`. A one-line editor for a floating-point number, allowing
  constraints.

- `QuLineEditInteger`. A one-line editor for an integer (C++ 32-bit int),
  allowing constraints.

- `QuLineEditLongLong`. A one-line editor for a large (64-bit) signed integer,
  allowing constraints.

- `QuLineEditNHSNumber`. A one-line editor for an `NHS number`_, with
  validation.

- `QuLineEditULongLong`. A one-line editor for a large unsigned integer,
  allowing constraints. (**Note** that the CamCOPS client generally avoids
  unsigned 64-bit integers, because SQLite3 doesn't have it as one of its core
  data types; see https://www.sqlite.org/datatype3.html.)

- `QuMcq`. A simple 1-from-many or multiple-choice question (MCQ), with a range
  of layout and visual options.

  - Unselected: |radio_unselected| or :unselectedtext:`Option`

  - Unselected and a response is required: |radio_unselected_required| or
    :missingtext:`Option`

  - Selected: |radio_selected| or :selectedtext:`Option`

- `QuMcqGrid`. An MCQ specialized to operate in a grid, with lots of questions
  having a common set of possible answers.

- `QuMcqGridDouble`. A specialized MCQ with a double grid (lots of questions
  having a common pair of sets of possible answers; e.g. for each question,
  pick one from A/B/C and pick one from X/Y/Z).

- `QuMcqGridSingleBoolean`. Another specialized MCQ; as for `QuMcqGrid` but
  with an additional Boolean variable per question (e.g. for each question,
  pick one of absent/mild/moderate/severe, and tick if distressing).

- `QuMultipleResponse`. An n-from-many (multiple response) question.

  - Unselected: |check_unselected| or :unselectedtext:`Option`

  - Unselected and more responses required: |check_unselected_required| or
    :missingtext:`Option`

  - Selected: |check_true_red| or :selectedtext:`Option`

- `QuPhoto`. Uses the device camera to take a photo.

- `QuPickerInline`. Pick from a list of options using a spinner or similar
  interface.

- `QuPickerPopup`. Pick from a list of options using a pop-up selector.

- `QuSpinBoxDouble`. Offers a text editing box with spinbox controls, for
  floating-point entry.

- `QuSpinBoxInteger`. Offers a text editing box with spinbox controls, for
  integer entry.

- `QuSlider`. A slider, for discrete or continuous numerical variables.

- `QuTextEdit`. An expanding editor for entering large quantities of text.
  (For a smaller version, see `QuLineEdit`.)

- `QuThermometer`. A thermometer-style visual analogue scale.


Layout
~~~~~~

These elements are simply for layout:

- `QuFlowContainer`. A container that flows its contents like a word processor
  flows words.

- `QuGridContainer`. A container implementing a grid of cells, like a table.

- `QuHorizontalContainer`. Arranges other elements in a horizontal row.

- `QuVerticalContainer`. Arranges other elements in a vertical column.


Dynamic questionnaire logic, with examples
------------------------------------------

Individual task classes inherit from ``Task`` which inherits from
``DatabaseObject``. Database objects have **fields** (``Field`` objects) that
are referred to by name (plus methods to load/save from the database).

Questionnaire elements automatically and dynamically reflect their field
content. For example, a ``QuMcq`` object (and many other ``Element`` objects)
takes a ``FieldRefPtr``, which is a pointer to a ``FieldRef``. A ``FieldRef``
may refer to something wholly arbitrary and transient (such as via
getter/setter functions), but most typically a ``FieldRef`` refers to a field
in a ``DatabaseObject``, by field name. This system allows questionnaires to
show arbitrary content but provides a simple mechanism to have one or many
fields provide views onto the task's fields.

- A very basic example is the ``Irac`` task, which uses two ``QuMcq`` elements.

- A basic example using ``QuMcqGrid`` is the ``Phq9`` task.

- An example of a slightly more complex view on data is the ``Bmi`` task. This
  stores mass and height in metric units, but can provide a dynamic editable
  view in Imperial units.

More dynamic content usually requires that the Task objects keeps some sort of
reference to the questionnaire during editing. The simplest way is to keep a
safe pointer to the Questionnaire (``QPointer<Questionnaire> m_questionnaire``)
but you can keep pointers to more detailed things too. (The task will not *own*
the Questionnaire. A `QPointer <http://doc.qt.io/qt-5/qpointer.html>`_ is
automatically set to zero when its referenced object is destroyed.)

Since ``FieldRef`` objects also maintain a **mandatory** flag, data input can
be made conditional.

- A reasonably simple example of this is the ``Icd10Depressive`` task. It
  connects the ``FieldRef::valueChanged`` signal, for each of its informative
  fields, to its ``Icd10Depressive::updateMandatory`` function. This function
  calculates whether the task is in a position to know if the patient
  definitely meets the criteria for depression, or definitely does not have
  depression by these criteria, or whether there is insufficient information to
  be sure. If there is insufficient information, all the relevant fields are
  set to mandatory, using ``FieldRef::setMandatory()``. If it has all the
  information it needs, it makes the fields non-mandatory (optional). It
  achieves all this without storing a pointer to its Questionnaire.

- The ``Cecaq3`` task is a much more complicated example, mostly using this
  simple principle.

The **display** of elements can also be made conditional, in a simple way.

Elements (and pages) can have one or several string **tags** added to them.
``FieldRef`` objects can have **hints** attached to them. Both these systems
allow recipients of callbacks to identify the source, without the need for a
profusion of callback functions. Tags are also (and more commonly) used to set
an attribute (such as being visible or mandatory) on multiple elements or field
references that are conceptually related.

- The ``Cape42`` task uses hints to determine which question a callback is
  coming from. If the subject endorses a symptom, a set of further questions
  (frequency, distress) is made visible (and potentially mandatory), using the
  tag system to apply visibility. The result is that if the subject doesn't
  endorse the symptom, he/she can move on without seeing the follow-up
  questions, but those questions appear and must be completed if the symptom is
  endorsed.

- In the ``Ace3`` task, if the subject has got all the free address recall
  questions right, the cued recall page shows a "Nothing to see here; move
  along" message. Internally, it has a ``m_questionnaire`` pointer as its only
  link to its Questionnaire.

- The ``Bdi`` task switches which of three ``QuMcqGrid`` elements is shown,
  depending on which scale version is selected. It takes the approach of
  storing safe pointers to them directly.

Tasks can use callbacks with the hints and tags systems, but can of course
also store safe pointers to elements or ``FieldRef`` objects.

- The ``Caps`` task is an example of storing  ``FieldRefPtr`` objects for use
  in callbacks.

Arbitrarily complex logic can be used with the **dynamic questionnaire**
system. Rather than a plain ``Questionnaire``, one can use a
``DynamicQuestionnaire``. This takes as parameters two functions: one to make
a page (given its integer index), and one to report whether or not there are
more pages to go (given the integer index of the current page).

- The ``Cisr`` task is pretty complex as questionnaires go. It implements a
  decision tree that includes or skips questions (pages) depending on the
  subject's answers. The total number of pages depends on the subject's
  answers, and the subject can browse back and forth. New pages are created and
  build dynamically; see ``Cisr::makePage()`` and ``Cisr::morePagesToGo()``.


Implementing specific elements
------------------------------

Likert-type scales
~~~~~~~~~~~~~~~~~~

Likert_-type scales are discrete -- for example,

.. code-block:: none

    Roses are best when red.

     Strongly    Disagree    Neutral      Agree      Strongly
     disagree                                         agree
        |-----------|-----------|-----------X-----------|

These are fairly well suited to a ``QuSlider``. Because asymmetry can bias the
response, you probably want a slider that displays its handle in the centre
when no value has been selected, and which is symmetric in terms of the
colouring left/right of the handle. For example, if we code the scale above
from 1 "strongly disagree" to 5 "strongly agree", we could do this:

.. code-block:: cpp

    #include "questionnairelib/questionnaire.h"
    #include "questionnairelib/qugridcontainer.cpp"
    #include "questionnairelib/quslider.h"
    #include "questionnairelib/qutext.h"

    // ...

    OpenableWidget* MyTask::editor(const bool read_only)
    {
        const QString ROSES_FIELDNAME("roses");
        const int STRONGLY_DISAGREE = 1;
        const int DISAGREE = 2;
        const int NEUTRAL = 3;
        const int AGREE = 4;
        const int STRONGLY_AGREE = 5;

        // --------------------------------------------------------------------
        // Question
        // --------------------------------------------------------------------

        auto rose_q = new QuText("Roses are best when red.");

        // --------------------------------------------------------------------
        // Likert-style slider
        // --------------------------------------------------------------------
        // Create the horizontal slider
        QuSlider* likert_slider = new QuSlider(
            fieldRef(ROSES_FIELDNAME), STRONGLY_DISAGREE, STRONGLY_AGREE, 1);
        likert_slider->setHorizontal(true);
        likert_slider->setBigStep(1);

        // Ticks for every interval, above and below
        likert_slider->setTickInterval(1);
        likert_slider->setTickPosition(QSlider::TickPosition::TicksBothSides);

        // Labels
        likert_slider->setTickLabels({
            {STRONGLY_DISAGREE, "Strongly\ndisagree"},  // or an xstring()
            {DISAGREE, "Disagree"},
            {NEUTRAL, "Neutral"},
            {AGREE, "Agree"},
            {STRONGLY_AGREE, "Strongly\nagree"},
        });
        likert_slider->setTickLabelPosition(QSlider::TickPosition::TicksAbove);

        // Don't show the numerical value
        likert_slider->setShowValue(false);

        // Symmetry
        likert_slider->setNullApparentValue(NEUTRAL);
        likert_slider->setSymmetric(true);
        likert_slider->setEdgeInExtremeLabels(false);

        // --------------------------------------------------------------------
        // Grid to improve layout
        // --------------------------------------------------------------------

        // Make the scale take 70% of the screen width.
        const int MARGIN_WIDTH = 15;  // each side
        const int LIKERT_WIDTH = 70;
        auto likert_slider_grid = new QuGridContainer();
        likert_slider_grid->setColumnStretch(0, MARGIN_WIDTH);
        likert_slider_grid->setColumnStretch(1, LIKERT_WIDTH);
        likert_slider_grid->setColumnStretch(2, MARGIN_WIDTH);
        likert_slider_grid->addCell(QuGridCell(likert_slider, 0, 1));

        // --------------------------------------------------------------------
        // Page, questionnaire
        // --------------------------------------------------------------------

        auto page1 = new QuPage{rose_q, likert_slider_grid};
        page1->setTitle("Test Likert");
        auto questionnaire = new Questionnaire(m_app, {page1});
        questionnaire->setReadOnly(read_only);
        return questionnaire;
    }

The main disadvantage is that sliders require their handles be dragged
(rather than tap-to-choose); this is part of the Qt ``QSlider`` behaviour.
Clicking to the left/right moves the slider, but not all the way to the click
point. This is pretty minor, though, and there are desirable aspects to it too
(e.g. nudging it to the right/left is possible).

Alternatives might include:

- a vertical ``QuSlider``, similarly;
- a (vertical) ``QuThermometer``;
- a future modification to make ``QuSlider`` tap-to-choose;
- a future modification to make ``QuThermometer`` operate horizontally.


Visual analogue scales
~~~~~~~~~~~~~~~~~~~~~~

A `visual analogue scale`_ is continuous; for example:

.. code-block:: none

    Please rate something.

       Low                                             High
        |------------------------------------X----------|

You can implement this with a ``QuSlider``, as above. Use a large integer range
(e.g. 0-1000) as a discrete approximation to a continuous space. (Not
continuous enough for you? Pick a bigger integer range. How many pixels do you
have, anyway?) Scale to your desired floating-point range as follows. (See also
the example in the :ref:`QOL-Basic <qol_basic>` task.) Suppose we want to
represent the range 0-1 with 1000 steps (i.e. to 3dp).

.. code-block:: cpp

    #include "questionnairelib/questionnaire.h"
    #include "questionnairelib/qugridcontainer.cpp"
    #include "questionnairelib/quslider.h"

    // ...

    OpenableWidget* MyTask::editor(const bool read_only)
    {
        const QString VAS_FIELDNAME("vas");
        const int VAS_MIN_INT = 0;  // the internal integer minimum
        const int VAS_CENTRAL_INT = 500;  // centre, for initial display
        const int VAS_MAX_INT = 1000;  // the internal integer maximum
        const double VAS_MIN = 0.0;  // the database/display minimum
        const double VAS_MAX = 1.0;  // the database/display maximum
        const int VAS_DISPLAY_DP = 3;
        const int VAS_ABSOLUTE_SIZE_CM = 10.0;
        const bool VAS_CAN_SHRINK = true;

        // --------------------------------------------------------------------
        // VAS-style slider
        // --------------------------------------------------------------------

        // Create the horizontal slider
        QuSlider* vas_slider = new QuSlider(
            fieldRef(VAS_FIELDNAME), VAS_MIN_INT, VAS_MAX_INT, 1);
        vas_slider->setConvertForRealField(true, VAS_MIN, VAS_MAX, VAS_DISPLAY_DP);
        vas_slider->setHorizontal(true);
        vas_slider->setBigStep(1);

        // Ticks just at the extremes
        vas_slider->setTickInterval(VAS_MAX_INT);
        vas_slider->setTickPosition(QSlider::TickPosition::TicksBothSides);

        // Labels
        vas_slider->setTickLabels({
            {VAS_MIN_INT, QString::number(VAS_MIN)},  // or whatever
            {VAS_MAX_INT, QString::number(VAS_MAX)},
        });
        vas_slider->setTickLabelPosition(QSlider::TickPosition::TicksAbove);

        // Show the numerical value
        vas_slider->setShowValue(true);

        // Symmetry
        vas_slider->setNullApparentValue(VAS_CENTRAL_INT);
        vas_slider->setSymmetric(true);
        vas_slider->setEdgeInExtremeLabels(false);

        // Absolute size, if absolutely required (beware small screens -- you
        // may want the can_shrink parameter to be true for those; if the
        // screen is too small, the slider goes below the specified absolute
        // size).
        vas_slider->setAbsoluteLengthCm(VAS_ABSOLUTE_SIZE_CM, VAS_CAN_SHRINK);

        // --------------------------------------------------------------------
        // Page, questionnaire
        // --------------------------------------------------------------------

        auto page1 = new QuPage{vas_slider};
        page1->setTitle("Test VAS");
        auto questionnaire = new Questionnaire(m_app, {page1});
        questionnaire->setReadOnly(read_only);
        return questionnaire;
    }

Note that the use of ``setConvertForRealField`` means that your database
representation will be in the desired floating-point format. Integers will only
be used internally in the slider.
