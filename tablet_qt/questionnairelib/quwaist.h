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
#include "common/aliases_camcops.h"
#include "questionnairelib/qumeasurement.h"
#include "questionnairelib/quunitselector.h"

class QuWaist : public QuMeasurement
{
    // Waist circumference in centimetres question type with imperial
    // conversion
    Q_OBJECT

public:
    QuWaist(
        FieldRefPtr fieldref,
        QPointer<QuUnitSelector> unit_selector,
        bool mandatory = true
    );
    void setUpFields();

protected:
    virtual FieldRefPtrList getMetricFieldrefs() const;
    virtual FieldRefPtrList getImperialFieldrefs() const;

public slots:
    QVariant getCm() const;
    QVariant getIn() const;
    bool setCm(const QVariant& value);
    bool setIn(const QVariant& value);

protected:
    QVariant m_in;

    FieldRefPtr m_fr_cm;
    FieldRefPtr m_fr_in;

    QPointer<QuElement> buildMetricGrid();
    QPointer<QuElement> buildImperialGrid();

    void updateMetric();
    void updateImperial();
};
