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

#pragma once
#include <QList>
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/quthermometeritem.h"

class ImageButton;


class QuThermometer : public QuElement
{
    // Offers a stack of images, allowing the user to select one (and
    // displaying an alternative image at the chosen location), such as for
    // something in the style of a distress thermometer.
    //
    // The thermometer operates on name/value pairs; the thing that gets stored
    // in the field is the value() part of the QuThermometerItem.

    Q_OBJECT
public:
    QuThermometer(FieldRefPtr fieldref,
                  const QVector<QuThermometerItem>& items);
    QuThermometer(FieldRefPtr fieldref,
                  std::initializer_list<QuThermometerItem> items);
    QuThermometer* setRescale(bool rescale, double rescale_factor,
                              bool adjust_for_dpi = true);
protected:
    void commonConstructor();
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int indexFromValue(const QVariant& value) const;
    QVariant valueFromIndex(int index) const;
protected slots:
    void clicked(int index);
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    QVector<QuThermometerItem> m_items;
    bool m_rescale;
    double m_rescale_factor;
    QPointer<QWidget> m_main_widget;
    QVector<QPointer<ImageButton>> m_active_widgets;
    QVector<QPointer<ImageButton>> m_inactive_widgets;
};
