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
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quelement.h"

class QuUnitSelector : public QuElement
{
    // Used with QuMeasurement to switch between metric and imperial units
    Q_OBJECT

public:
    QuUnitSelector(NameValueOptions options);
    void setUpFields();

public slots:
    void fieldChanged();
    QVariant getUnits() const;
    bool setUnits(const QVariant& value);  // returns: changed?

signals:
    void unitsChanged(int units);

protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire
    ) override;

    int m_units;
    FieldRefPtr m_fr_units;

private:
    NameValueOptions m_options;
};
