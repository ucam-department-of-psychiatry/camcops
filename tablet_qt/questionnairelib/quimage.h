#pragma once
#include "db/fieldref.h"
#include "quelement.h"

class QLabel;


class QuImage : public QuElement
{
    // Displays an image (from a static filename or a field).
    // No user response offered.

    Q_OBJECT
public:
    QuImage(const QString& filename, const QSize& size = QSize());
    QuImage(FieldRefPtr fieldref, const QSize& size = QSize());
    // ... field provides raw image data
    // The default value of size takes the image's own size.
    QuImage* setSize(const QSize& size);
protected slots:
    void valueChanged(const FieldRef* fieldref);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_filename;
    FieldRefPtr m_fieldref;
    QPointer<QLabel> m_label;
    QSize m_size;
};
