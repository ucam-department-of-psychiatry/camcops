/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

    // How to display?
    enum Mode {
        DefaultDateTime,  // e.g. 2000 01 31 08:00
        DefaultDate,  // e.g. 2000 01 31
        DefaultTime,  // e.g. 08:00
        CustomDateTime,  // user-specified format as per http://doc.qt.io/qt-5/qdatetime.html#toString-2
        CustomDate,  // user-specified format as per http://doc.qt.io/qt-5/qdatetime.html#toString-2
        CustomTime,  // user-specified format as per http://doc.qt.io/qt-5/qdatetime.html#toString-2
    };
public:

    // Constructor.
    QuDateTime(FieldRefPtr fieldref);

    // Sets the mode, as above.
    QuDateTime* setMode(QuDateTime::Mode mode);

    // For the custom modes, sets the format string (for displaying the
    // date/time), and the input method hint mode (e.g. for Android keyboard:
    // "numbers-only keyboard" or similar).
    QuDateTime* setCustomFormat(
            const QString& format,
            Qt::InputMethodHints input_method_hint = Qt::ImhNone);

    // Offer a "set date/time to now" button? A common thing to set.
    QuDateTime* setOfferNowButton(bool offer_now_button);

    // Offer a "set date/time to null" option? A rare thing to want.
    QuDateTime* setOfferNullButton(bool offer_null_button);

protected:

    // Sets the widget state from our fieldref.
    void setFromField();

    virtual FieldRefPtrList fieldrefs() const override;
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;

protected slots:

    // "Internal widget says: date/time has been changed by the user."
    void widgetValueChanged(const QDateTime& datetime);

    // Set the field to a specific date/time. Optionally, tell the internal
    // widget to set itself to the same value.
    void setField(const QDateTime& datetime,
                  bool reset_this_widget = false);

    // "Fieldref reports that the field's data has changed."
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);

    // Set the field to the date/time now.
    void setToNow();

    // Set the field to null.
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
