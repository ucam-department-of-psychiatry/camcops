/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

/*

===============================================================================
PRIMARY REFERENCE
===============================================================================

CIS-R: Lewis et al. 1992
- https://www.ncbi.nlm.nih.gov/pubmed/1615114

Helpful chronology:
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3347904/#b2-mjms-13-1-058

===============================================================================
INTERNALS
===============================================================================

The internal methodology of the CIS-R is that the textfile
"BASIC CIS-R 02-03-2010.pqs" contains a sequence, of the type:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LABEL_A1

"Some question?"

[
1 "Option 1"
2 "Option 2"
3 "Option 3"
]

SOMEVAR := answer * 10
if answer == 1 then goto LABEL_B1;
if answer == 2 then goto LABEL_B2;
if answer == 3 then goto LABEL_B3;

&

LABEL_B1

...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===============================================================================
IMPLEMENTATION
===============================================================================

We could in principle do this with a Questionnaire interface, but to be honest
it's going to be easiest to translate with a "direct" interface. Maybe
something like:


void start()
{
    goto(1);
}

void goto_question(int question)
{
    m_current_question = question;
    offer_question();
}

bool offer_question()
{
    // do interesting things
    connect(answer_1, answered, 1);
    return true;
}

bool answered(int answer)
{
    // returns: something we don't care about
    switch (m_current_question) {
    case 1:
        if (answer == 1) {
            m_diagnosis_blah = true;
            return goto(2);
            // C++11: can't do "return goto_question(2);" if goto_question() is
            // of void type, as you're not allowed to return anything from a
            // void function, even of void type:
            // http://stackoverflow.com/questions/35987493/return-void-type-in-c-and-c
            // ... so just make them bool or something.
            // It would be OK in C++14.
        }
        break;
    // ...
    }
}


*/

#include "cisr.h"
#include "tasklib/taskfactory.h"

const QString Cisr::CISR_TABLENAME("cisr");


void initializeCisr(TaskFactory& factory)
{
    static TaskRegistrar<Cisr> registered(factory);
}


Cisr::Cisr(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, CISR_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // ***

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Cisr::shortname() const
{
    return "CIS-R";
}


QString Cisr::longname() const
{
    return tr("Clinical Interview Schedule – Revised");
}


QString Cisr::menusubtitle() const
{
    return tr("Structured diagnostic interview, yielding ICD-10 diagnoses for "
              "depressive and anxiety disorders.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Cisr::isComplete() const
{
    // ***
    return false;
}


QStringList Cisr::summary() const
{
    // ***
    return QStringList{"Not implemented yet!"};
}


QStringList Cisr::detail() const
{
    // ***
    return completenessInfo() + summary();
}


OpenableWidget* Cisr::editor(bool read_only)
{
    // ***
    Q_UNUSED(read_only);
    return nullptr;
}


// ============================================================================
// Task-specific calculations
// ============================================================================


// ============================================================================
// Signal handlers
// ============================================================================
