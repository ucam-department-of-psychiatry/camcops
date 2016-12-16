/*
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
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QPair>
#include <QStack>
#include "diagnosticcodeset.h"

class CamcopsApp;


class Icd10 : public DiagnosticCodeSet
{
    Q_OBJECT

public:
    Icd10(const CamcopsApp& app, QObject* parent = nullptr);

    using CodeDescriptionPair = QPair<QString, QString>;
    using DepthItemPair = QPair<int, DiagnosticCode*>;
private:
    void addIcd10Codes(const QList<QString>& codes);
    void addIndividualIcd10Code(const QString& code, const QString& desc,
                                bool show_code_in_full_name = true);
    void addSubcodes(const QString& basecode,
                     const QString& basedesc,
                     const QList<CodeDescriptionPair>& level1);
    void addSubcodes(const QString& basecode,
                     const QString& basedesc,
                     const QList<CodeDescriptionPair>& level1,
                     const QList<CodeDescriptionPair>& level2);

    QStack<DepthItemPair> m_creation_stack;  // depth, pointer (of parents)

    void addDementia(const QString& basecode, const QString& basedesc);
    void addSubstance(const QString& basecode, const QString& basedesc);
    void addSchizophrenia(const QString& basecode, const QString& basedesc);
    void addSelfHarm(const QString& basecode, const QString& basedesc);

    static const QList<QString> BASE_CODES;
    static const QList<CodeDescriptionPair> DEMENTIA_L1;
    static const QList<CodeDescriptionPair> DEMENTIA_L2;
    static const QList<CodeDescriptionPair> SUBSTANCE_L1;
    static const QList<CodeDescriptionPair> SCHIZOPHRENIA_L1;
    static const QList<CodeDescriptionPair> SELFHARM_L1;
    static const QList<CodeDescriptionPair> SELFHARM_L2;
};
