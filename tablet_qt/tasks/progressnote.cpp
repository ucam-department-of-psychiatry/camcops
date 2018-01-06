/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "progressnote.h"
#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"

const QString ProgressNote::PROGNOTE_TABLENAME("progressnote");

const QString LOCATION("location");
const QString NOTE("note");


void initializeProgressNote(TaskFactory& factory)
{
    static TaskRegistrar<ProgressNote> registered(factory);
}


ProgressNote::ProgressNote(CamcopsApp& app, DatabaseManager& db,
                           const int load_pk) :
    Task(app, db, PROGNOTE_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addField(LOCATION, QVariant::String);
    addField(NOTE, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString ProgressNote::shortname() const
{
    return "ProgressNote";
}


QString ProgressNote::longname() const
{
    return tr("Progress note");
}


QString ProgressNote::menusubtitle() const
{
    return tr("Clinical progress note entry.");
}


QString ProgressNote::infoFilenameStem() const
{
    return "clinical";
}


// ============================================================================
// Instance info
// ============================================================================

bool ProgressNote::isComplete() const
{
    return !valueIsNull(NOTE);
}


QStringList ProgressNote::summary() const
{
    return QStringList{stringfunc::abbreviate(valueString(NOTE))};
}


QStringList ProgressNote::detail() const
{
    QStringList lines = completenessInfo() + clinicianDetails();
    lines.append(fieldSummary(LOCATION, textconst::LOCATION));
    lines.append(fieldSummary(NOTE, textconst::NOTE));
    return lines;
}


OpenableWidget* ProgressNote::editor(const bool read_only)
{
    QuPagePtr page((new QuPage{
        getClinicianQuestionnaireBlockRawPointer(),
        new QuText(textconst::LOCATION),
        new QuLineEdit(fieldRef(LOCATION)),
        new QuText(textconst::NOTE),
        new QuTextEdit(fieldRef(NOTE)),
    })->setTitle(longname()));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Clinician);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}
