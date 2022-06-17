/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/quunitselector.h"

class QuMass : public QuElement
{
    Q_OBJECT
public:
    QuMass(FieldRefPtr fieldref, QPointer<QuUnitSelector> unit_selector);
    void setUpFields();


public slots:
    void unitsChanged(int units);
    QVariant getKg() const;
    QVariant getSt() const;
    QVariant getLb() const;
    QVariant getOz() const;
    bool setKg(const QVariant& value);
    bool setSt(const QVariant& value);
    bool setLb(const QVariant& value);
    bool setOz(const QVariant& value);

protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;

    QVariant m_st;
    QVariant m_lb;
    QVariant m_oz;

    FieldRefPtr m_fieldref;
    QPointer<QuUnitSelector> m_unit_selector;
    FieldRefPtr m_fr_kg;
    FieldRefPtr m_fr_st;
    FieldRefPtr m_fr_lb;
    FieldRefPtr m_fr_oz;

    void updateMetric();
    void updateImperial();

private:
    QPointer<QuElement> m_metric_grid;
    QPointer<QuElement> m_imperial_grid;
};
