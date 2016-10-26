#pragma once
#include <QSize>
#include "db/fieldref.h"
#include "quelement.h"

class BooleanWidget;


class QuBoolean : public QuElement
{
    // Element to control a single Boolean field.
    // Displays text or an image, in addition to the response widget.

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
protected:
    void commonConstructor();
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void clicked();
    void fieldValueChanged(const FieldRef* fieldref);
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
    QPointer<BooleanWidget> m_indicator;
};
