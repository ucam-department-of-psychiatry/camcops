#include "qudatetime.h"
#include <QDateTimeEdit>
#include "lib/uifunc.h"
#include "questionnaire.h"

// http://doc.qt.io/qt-5/qdatetime.html#toString
const QString DEFAULT_DATETIME_FORMAT = "dd MMM yyyy HH:mm";
const QString DEFAULT_DATE_FORMAT = "dd MMM yyyy";
const QString DEFAULT_TIME_FORMAT = "HH:mm";
const QDate PSEUDONULL_DATE(1752, 9, 14);  // 14 Sep 1752 is usual minimum (Gregorian calendar)
const QTime PSEUDONULL_TIME(0, 0, 0, 0);
const QDateTime PSEUDONULL_DATETIME(PSEUDONULL_DATE, PSEUDONULL_TIME);


QuDateTime::QuDateTime(FieldRefPtr fieldref) :
    m_fieldref(fieldref),
    m_editor(nullptr)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuDateTime::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuDateTime::fieldValueChanged);
    setMode(Mode::DefaultDateTime);
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
    setFromField();
    return QPointer<QWidget>(m_editor);
}


// It will show a NULL as yellow, but as soon as you edit the field,
// it un-NULLs it irreversibly. (You could use e.g. 14 Sep 1752 00:00 as a
// pseudo-NULL that you can enter, but that doesn't work when you want to
// enter midnight deliberately, and starting with 1752 just looks odd.)

void QuDateTime::widgetValueChanged(const QDateTime& datetime)
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
    m_fieldref->setValue(newvalue, this);
    emit elementValueChanged();
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
        const QSignalBlocker blocker(m_editor);
        m_editor->setDateTime(fieldref->valueDateTime());
        // NULL will be shown as 1 Jan 2000 00:00.
        // The yellow marker will disappear when that value is edited.
    }
}
