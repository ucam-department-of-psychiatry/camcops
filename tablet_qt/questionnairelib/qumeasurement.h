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
#include "questionnairelib/quunitselector.h"

class QuMeasurement : public QuElement
{
    Q_OBJECT
public:
    QuMeasurement(FieldRefPtr fieldref, QPointer<QuUnitSelector> unit_selector);

public slots:
    void unitsChanged(int units);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual FieldRefPtrList getMetricFieldrefs() const = 0;
    virtual FieldRefPtrList getImperialFieldrefs() const = 0;
    virtual void updateMetric() = 0;
    virtual void updateImperial() = 0;
    virtual QPointer<QuElement> buildMetricGrid() = 0;
    virtual QPointer<QuElement> buildImperialGrid() = 0;
    virtual void setUpFields() = 0;
    QVariant getFieldrefValue() const;
    bool setFieldrefValue(const QVariant& value);

private:
    FieldRefPtr m_fieldref;
    QPointer<QuUnitSelector> m_unit_selector;
    QPointer<QuElement> m_metric_grid;
    QPointer<QuElement> m_imperial_grid;
};
