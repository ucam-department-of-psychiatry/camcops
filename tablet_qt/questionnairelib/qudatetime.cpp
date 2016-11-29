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

#include "qudatetime.h"
#include <QDateTimeEdit>
#include <QHBoxLayout>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/imagebutton.h"

// http://doc.qt.io/qt-5/qdatetime.html#toString
const QString DEFAULT_DATETIME_FORMAT("dd MMM yyyy HH:mm");
const QString DEFAULT_DATE_FORMAT("dd MMM yyyy");
const QString DEFAULT_TIME_FORMAT("HH:mm");
// const QDate PSEUDONULL_DATE(1752, 9, 14);  // 14 Sep 1752 is usual minimum (Gregorian calendar)
const QDate PSEUDONULL_DATE(2000, 1, 1);  // ... but 1752 is a long way away from now...
const QTime PSEUDONULL_TIME(0, 0, 0, 0);
const QDateTime PSEUDONULL_DATETIME(PSEUDONULL_DATE, PSEUDONULL_TIME);


QuDateTime::QuDateTime(FieldRefPtr fieldref) :
    m_fieldref(fieldref),
    m_mode(Mode::DefaultDateTime),
    m_offer_now_button(false),
    m_offer_null_button(false),
    m_editor(nullptr)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuDateTime::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuDateTime::fieldValueChanged);
}


QuDateTime* QuDateTime::setMode(QuDateTime::Mode mode)
{
    m_mode = mode;
    return this;
}


QuDateTime* QuDateTime::setCustomFormat(const QString& format)
{
    m_custom_format = format;
    return this;
}


QuDateTime* QuDateTime::setOfferNowButton(bool offer_now_button)
{
    m_offer_now_button = offer_now_button;
    return this;
}


QuDateTime* QuDateTime::setOfferNullButton(bool offer_null_button)
{
    m_offer_null_button = offer_null_button;
    return this;
}


void QuDateTime::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
}


FieldRefPtrList QuDateTime::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


QPointer<QWidget> QuDateTime::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();

    QPointer<QWidget> widget = new QWidget();
    widget->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    QHBoxLayout* layout = new QHBoxLayout();
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);

    QString format;
    bool calendar = true;
    switch (m_mode) {
    case DefaultDateTime:
        format = DEFAULT_DATETIME_FORMAT;
        break;
    case DefaultDate:
        format = DEFAULT_DATE_FORMAT;
        break;
    case DefaultTime:
        format = DEFAULT_TIME_FORMAT;
        calendar = false;
        break;
    case CustomDateTime:
    case CustomDate:
        format = m_custom_format;
        break;
    case CustomTime:
        format = m_custom_format;
        calendar = false;
        break;
    }

    m_editor = new QDateTimeEdit();
    m_editor->setDisplayFormat(format);
    m_editor->setCalendarPopup(calendar);
    m_editor->setEnabled(!read_only);
    m_editor->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Expanding);
    // Fixed horizontal keeps the drop-down button close to the text.
    // Expanding vertical makes the drop-down button and spin buttons a
    // reasonable size (not too small).
    if (!read_only) {
        connect(m_editor.data(), &QDateTimeEdit::dateTimeChanged,
                this, &QuDateTime::widgetValueChanged);
    }
    layout->addWidget(m_editor);

    if (m_offer_now_button) {
        QAbstractButton* now_button = new ImageButton(UiConst::CBS_TIME_NOW);
        now_button->setEnabled(!read_only);
        if (!read_only) {
            connect(now_button, &QAbstractButton::clicked,
                    this, &QuDateTime::setToNow);
        }
        layout->addWidget(now_button);
    }

    if (m_offer_null_button) {
        QAbstractButton* null_button = new ImageButton(UiConst::CBS_DELETE);
        null_button->setEnabled(!read_only);
        if (!read_only) {
            connect(null_button, &QAbstractButton::clicked,
                    this, &QuDateTime::setToNull);
        }
        layout->addWidget(null_button);
    }

    layout->addStretch();

    setFromField();
    return widget;
}


// It will show a NULL as yellow, but as soon as you edit the field,
// it un-NULLs it irreversibly. (You could use e.g. 14 Sep 1752 00:00 as a
// pseudo-NULL that you can enter, but that doesn't work when you want to
// enter midnight deliberately, and starting with 1752 just looks odd.)

void QuDateTime::widgetValueChanged(const QDateTime& datetime)
{
    setField(datetime, false);
}


void QuDateTime::setField(const QDateTime& datetime, bool reset_this_widget)
{
    QVariant newvalue = datetime;
    switch (m_mode) {
    case DefaultDateTime:
    case CustomDateTime:
        newvalue.convert(QVariant::DateTime);
        break;
    case DefaultDate:
    case CustomDate:
        newvalue.convert(QVariant::Date);
        break;
    case DefaultTime:
    case CustomTime:
        newvalue.convert(QVariant::Time);
        break;
    }
    bool changed = m_fieldref->setValue(newvalue, reset_this_widget ? nullptr : this);
    if (changed) {
        emit elementValueChanged();
    }
}


void QuDateTime::setToNow()
{
    setField(QDateTime::currentDateTime(), true);
}


void QuDateTime::setToNull()
{
    setField(QDateTime(), true);
}


void QuDateTime::fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator)
{
    if (!m_editor) {
        return;
    }
    // Missing?
    UiFunc::setPropertyMissing(m_editor, fieldref->missingInput());
    if (originator != this) {
        // Value
        QDateTime display_value = fieldref->valueDateTime();
        if (!display_value.isValid()) {
            display_value = PSEUDONULL_DATETIME;
            // because QDateTimeEdit::setDateTime() will ignore invalid values
        }
        const QSignalBlocker blocker(m_editor);
        m_editor->setDateTime(display_value);
        // NULL will be shown as the pseudonull value.
        // The yellow marker will disappear when that value is edited.
    }
}
