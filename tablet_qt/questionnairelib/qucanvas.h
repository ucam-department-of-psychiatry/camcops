#pragma once
#include <QImage>
#include "lib/fieldref.h"
#include "quelement.h"

class CanvasWidget;
class QLabel;
class QTimer;


class QuCanvas : public QuElement
{
    Q_OBJECT
public:
    QuCanvas(FieldRefPtr fieldref,
             const QSize& size = QSize(100, 100),
             QImage::Format format = QImage::Format_RGB32,
             const QColor& background_colour = Qt::white);
    QuCanvas(FieldRefPtr fieldref,
             const QString& template_filename,
             const QSize& size = QSize());  // = take template's size
    QuCanvas* setPenColour(const QColor& pen_colour);
    QuCanvas* setPenWidth(int pen_width);
    void setFromField();
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void closing() override;
    void resetWidget();
protected slots:
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
    void imageChanged();
    void completePendingFieldWrite();
    void resetFieldToNull();
protected:
    FieldRefPtr m_fieldref;
    QSize m_size;
    QImage::Format m_format;
    QColor m_background_colour;
    QColor m_pen_colour;
    int m_pen_width;
    QString m_template_filename;
    bool m_using_template;

    QPointer<CanvasWidget> m_canvas;
    QPointer<QLabel> m_missing_indicator;
    QSharedPointer<QTimer> m_timer;
    bool m_field_write_pending;
};
