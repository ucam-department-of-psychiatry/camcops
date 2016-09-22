#pragma once
#include <QPointer>
#include "lib/fieldref.h"
#include "quelement.h"

class QDateTimeEdit;


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
    QuDateTime* setCustomFormat(const QString& format);
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
    bool m_offer_now_button;
    bool m_offer_null_button;

    QPointer<QDateTimeEdit> m_editor;
};
