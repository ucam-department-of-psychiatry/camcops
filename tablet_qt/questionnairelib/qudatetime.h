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
#include <QPointer>
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"

class QDateTimeEdit;
class QCalendarWidget;


class QuDateTime : public QuElement
{
    // Manual or calendar-assisted date/time entry.

    Q_OBJECT
public:
    enum Mode {
        DefaultDateTime,
        DefaultDate,
        DefaultTime,
        CustomDateTime,
        CustomDate,
        CustomTime,
    };
public:
    QuDateTime(FieldRefPtr fieldref);
    QuDateTime* setMode(QuDateTime::Mode mode);
    QuDateTime* setCustomFormat(
            const QString& format,
            Qt::InputMethodHints input_method_hint = Qt::ImhNone);
    QuDateTime* setOfferNowButton(bool offer_now_button);
    QuDateTime* setOfferNullButton(bool offer_null_button);
protected:
    void setFromField();
    virtual FieldRefPtrList fieldrefs() const override;
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void widgetValueChanged(const QDateTime& datetime);
    void setField(const QDateTime& datetime,
                  bool reset_this_widget = false);
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
    void setToNow();
    void setToNull();
protected:
    FieldRefPtr m_fieldref;
    Mode m_mode;
    QString m_custom_format;
    Qt::InputMethodHints m_custom_input_method_hint;
    bool m_offer_now_button;
    bool m_offer_null_button;

    QPointer<QDateTimeEdit> m_editor;
    QPointer<QCalendarWidget> m_calendar_widget;
};
