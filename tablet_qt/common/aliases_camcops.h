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

#pragma once

#include <QList>
#include <QSharedPointer>
#include <QWeakPointer>

// Phase 1:

class CamcopsApp;

class DatabaseObject;
using DatabaseObjectPtr = QSharedPointer<DatabaseObject>;

class DiagnosticCodeSet;
using DiagnosticCodeSetPtr = QSharedPointer<DiagnosticCodeSet>;

class DiagnosisItemBase;
using DiagnosisItemBasePtr = QSharedPointer<DiagnosisItemBase>;

class FieldRef;
using FieldRefPtr = QSharedPointer<FieldRef>;
using FieldRefPtrList = QList<FieldRefPtr>;

class Patient;
using PatientPtr = QSharedPointer<Patient>;
using PatientPtrList = QList<PatientPtr>;

class QuElement;
using QuElementPtr = QSharedPointer<QuElement>;

class Questionnaire;
using QuestionnairePtr = QSharedPointer<Questionnaire>;

class QuPage;
using QuPagePtr = QSharedPointer<QuPage>;

class StoredVar;
using StoredVarPtr = QSharedPointer<StoredVar>;

class Task;
using TaskPtr = QSharedPointer<Task>;
using TaskWeakPtr = QWeakPointer<Task>;
using TaskPtrList = QList<TaskPtr>;

class TaskFactory;
using TaskFactoryPtr = QSharedPointer<TaskFactory>;

// Phase 2, using things from Phase 1:

using GridRowDefinition = QPair<QString, QuElementPtr>;
using GridRowDefinitionRawPtr = QPair<QString, QuElement*>;
