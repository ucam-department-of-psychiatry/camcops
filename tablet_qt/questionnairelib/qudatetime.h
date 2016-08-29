#pragma once
#include <QPointer>
#include "lib/fieldref.h"
#include "quelement.h"

class QDateTimeEdit;


class QuDateTime : public QuElement
{
    Q_OBJECT;
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
    void setFromField();
protected:
    virtual FieldRefPtrList fieldrefs() const override;
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void widgetValueChanged(const QDateTime& datetime);
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
protected:
    FieldRefPtr m_fieldref;
    Mode m_mode;
    QString m_custom_format;
    QPointer<QDateTimeEdit> m_editor;
};
