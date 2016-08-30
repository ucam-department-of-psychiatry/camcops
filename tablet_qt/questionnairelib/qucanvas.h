#pragma once
#include <QImage>
#include "lib/fieldref.h"
#include "quelement.h"

class QLabel;


class QuCanvas : public QuElement
{
    Q_OBJECT
public:
    QuCanvas(FieldRefPtr fieldref, const QSize& size,
             QImage::Format format, const QColor& background_colour,
             const QColor& pen_colour);
    QuCanvas(FieldRefPtr fieldref, const QString& template_filename,
             const QColor& pen_colour);
    void setFromField();
    bool mono() const;
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    void reset();
protected slots:
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
protected:
    FieldRefPtr m_fieldref;
    QSize m_size;
    QImage::Format m_format;
    QColor m_background_colour;
    QColor m_pen_colour;
    QString m_template_filename;
    bool m_using_template;

    QImage m_template_img;
    QImage m_img;
    QPointer<QLabel> m_label;
};
