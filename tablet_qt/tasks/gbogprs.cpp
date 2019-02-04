///*
//    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

//    This file is part of CamCOPS.

//    CamCOPS is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.

//    CamCOPS is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
//    GNU General Public License for more details.

//    You should have received a copy of the GNU General Public License
//    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
//*/

//#include "gbogprs.h"
//#include "maths/mathfunc.h"
//#include "lib/stringfunc.h"
//#include "questionnairelib/questionnairefunc.h"
//#include "questionnairelib/namevaluepair.h"
//#include "questionnairelib/quboolean.h"
//#include "questionnairelib/qudatetime.h"
//#include "questionnairelib/questionnaire.h"
//#include "questionnairelib/qugridcontainer.h"
//#include "questionnairelib/qugridcell.h"
//#include "questionnairelib/quheading.h"
//#include "questionnairelib/quflowcontainer.h"
//#include "questionnairelib/quhorizontalcontainer.h"
//#include "questionnairelib/quhorizontalline.h"
//#include "questionnairelib/qulineedit.h"
//#include "questionnairelib/qulineeditinteger.h"
//#include "questionnairelib/qumcq.h"
//#include "questionnairelib/qumcqgrid.h"
//#include "questionnairelib/quslider.h"
//#include "questionnairelib/quspacer.h"
//#include "questionnairelib/qutext.h"
//#include "questionnairelib/qutextedit.h"
//#include "questionnairelib/quverticalcontainer.h"
//#include "questionnairelib/questionnairefunc.h"
//#include "tasklib/task.h"
//#include "tasklib/taskfactory.h"

//using mathfunc::noneNullOrEmpty;
//using stringfunc::strseq;

//const QString GboGPrS::GBOGPRS_TABLENAME("gbo_goal_record");

//const int GOAL_CHILD = 1;
//const int GOAL_PARENT_CARER = 2;
//const int GOAL_OTHER = 3;

//const QString GOAL_CHILD_STR = "Child/young person";
//const QString GOAL_PARENT_CARER_STR = "Parent/carer";

//void initializeGboGPrS(TaskFactory& factory)
//{
//    static TaskRegistrar<GboGPrS> registered(factory);
//}


//GboGPrS::GboGPrS(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
//    Task(app, db, GBOGPRS_TABLENAME, false, false, false),  // ... anon, clin, resp
//    m_questionnaire(nullptr)
//{
//    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
//}

//// ============================================================================
//// Class info
//// ============================================================================

//QString GboGPrS::shortname() const
//{
//    return "GBO-GPrS";
//}


//QString GboGPrS::longname() const
//{
//    return tr("Goal Based Outcomes - Goal Progress Sheet");
//}


//QString GboGPrS::menusubtitle() const
//{
//    return tr("Goal progress tracking measurement");
//}


//// ============================================================================
//// Instance info
//// ============================================================================

//bool GboGPrS::isComplete() const
//{
//    return false;
//}

//QStringList GboGPrS::summary() const
//{
//    return QStringList{};
//}

//QStringList GboGPrS::detail() const
//{
//    QStringList detail;

//    detail.append(summary());

//    return detail;
//}

//OpenableWidget* GboGPrS::editor(const bool read_only)
//{
//    QuPagePtr page(new QuPage{});

//    page->setTitle(longname());

//    m_questionnaire = new Questionnaire(m_app, {page});
//    m_questionnaire->setReadOnly(read_only);
//    return m_questionnaire;
//}

//// ============================================================================
//// Task-specific calculations
//// ============================================================================
