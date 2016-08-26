#pragma once
#include <QSize>
#include "lib/fieldref.h"
#include "quelement.h"

class BooleanWidget;


class QuBoolean : public QuElement
{
    Q_OBJECT
public:
    QuBoolean(const QString& text, FieldRefPtr fieldref);
    QuBoolean(const QString& filename, const QSize& size,
              FieldRefPtr fieldref);  // default QSize() => "the file's size"
    QuBoolean* setContentClickable(bool clickable = true);
    QuBoolean* setIndicatorOnLeft(bool indicator_on_left = true);
    QuBoolean* setBigIndicator(bool big = true);
    QuBoolean* setBigText(bool big = true);
    QuBoolean* setBold(bool bold = true);
    QuBoolean* setItalic(bool italic = true);
    QuBoolean* setAllowUnset(bool allow_unset = true);
    QuBoolean* setAsTextButton(bool as_text_button = true);
    QuBoolean* setVAlign(Qt::Alignment alignment);  // horizontal part will be ignored
    void setFromField();
protected slots:
    void clicked();
    void valueChanged(const FieldRef* fieldref);
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected:
    QString m_text;
    QString m_image_filename;
    QSize m_image_size;
    FieldRefPtr m_fieldref;
    bool m_content_clickable;
    bool m_indicator_on_left;
    bool m_big_indicator;
    bool m_big_text;
    bool m_bold;
    bool m_italic;
    bool m_allow_unset;
    bool m_as_text_button;
    Qt::Alignment m_alignment;
    QPointer<BooleanWidget> m_indicator;
};
