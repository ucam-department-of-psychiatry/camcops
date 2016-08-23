#include "quboolean.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QWidget>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"


QuBoolean::QuBoolean(const QString& text, FieldRefPtr fieldref) :
    m_text(text),
    m_fieldref(fieldref)
{
    commonConstructor();
}


QuBoolean::QuBoolean(const QString &filename, const QSize &size,
                     FieldRefPtr fieldref) :
    m_image_filename(filename),
    m_image_size(size),
    m_fieldref(fieldref)
{
    commonConstructor();
}


void QuBoolean::commonConstructor()
{
    m_content_clickable = true;
    m_indicator_on_left = true;  // due to LabelWordWrap, better as true
    m_big_indicator = true;  // finger-sized; standard...
    m_big_text = false;
    m_bold = false;
    m_italic = false;
    m_allow_unset = false;
    m_as_text_button = false;
    m_alignment = Qt::AlignTop;
    m_indicator = nullptr;
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuBoolean::valueChanged);
}


QuBoolean* QuBoolean::setContentClickable(bool clickable)
{
    m_content_clickable = clickable;
    return this;
}


QuBoolean* QuBoolean::setIndicatorOnLeft(bool indicator_on_left)
{
    m_indicator_on_left = indicator_on_left;
    return this;
}


QuBoolean* QuBoolean::setBigIndicator(bool big)
{
    m_big_indicator = big;
    return this;
}


QuBoolean* QuBoolean::setBigText(bool big)
{
    m_big_text = big;
    return this;
}


QuBoolean* QuBoolean::setBold(bool bold)
{
    m_bold = bold;
    return this;
}


QuBoolean* QuBoolean::setItalic(bool italic)
{
    m_italic = italic;
    return this;
}


QuBoolean* QuBoolean::setMandatory(bool mandatory)
{
    m_mandatory = mandatory;
    return this;
}


QuBoolean* QuBoolean::setAllowUnset(bool allow_unset)
{
    m_allow_unset = allow_unset;
    return this;
}


QuBoolean* QuBoolean::setAsTextButton(bool as_text_button)
{
    m_as_text_button = as_text_button;
    return this;
}


QuBoolean* QuBoolean::setVAlign(Qt::Alignment alignment)
{
    m_alignment = alignment;
    return this;
}


QPointer<QWidget> QuBoolean::makeWidget(Questionnaire *questionnaire)
{
    bool read_only = questionnaire->readOnly();
    QPointer<QWidget> widget = new QWidget();
    QHBoxLayout* layout = new QHBoxLayout();
    Qt::Alignment layout_alignment = Qt::AlignLeft | Qt::AlignTop;
    layout->setAlignment(layout_alignment);
    widget->setLayout(layout);

    // Label
    ClickableLabel* label;
    if (!m_text.isEmpty()) {
        // Text label
        label = new LabelWordWrapWide(m_text);
        int fontsize = questionnaire->fontSizePt(m_big_text ? UiConst::FontSize::Big
                                                       : UiConst::FontSize::Normal);
        QString css = UiFunc::textCSS(fontsize, m_bold, m_italic);
        label->setStyleSheet(css);
        Qt::Alignment alignment = UiFunc::combineAlignment(Qt::AlignLeft,
                                                           m_alignment);
        label->setAlignment(alignment);
    } else {
        // Image label
        QPixmap image = UiFunc::getPixmap(m_image_filename, m_image_size);
        label = new ClickableLabel();
        label->setFixedSize(image.size());
        label->setPixmap(image);
    }

    // Indicator
    m_indicator = new BooleanWidget();
    m_indicator->setSize(m_big_indicator);
    m_indicator->setReadOnly(read_only);
    m_indicator->setAppearance(BooleanWidget::Appearance::CheckRed);

    // Whole thing
    if (m_indicator_on_left) {
        layout->addWidget(m_indicator);
        layout->addWidget(label);
    } else {
        layout->addWidget(label);
        layout->addWidget(m_indicator);
    }
    // To align things in a QHBoxLayout, align the widgets within the layout:
    //      layout->setAlignment(widget, alignment)
    // not the layout:
    //      layout->setAlignment(alignment)
    layout->setAlignment(label, layout_alignment);
    layout->setAlignment(m_indicator, layout_alignment);
    layout->addStretch();

    if (!read_only) {
        connect(m_indicator, &BooleanWidget::clicked,
                this, &QuBoolean::clicked);
        if (m_content_clickable) {
            label->setClickable(true);
            connect(label, &ClickableLabel::clicked,
                    this, &QuBoolean::clicked);
        }
    }

    setFromField();

    return widget;
}


void QuBoolean::setFromField()
{
    valueChanged(m_fieldref->value());
}


void QuBoolean::clicked()
{
    qDebug() << "QuBooleanText::clicked()";
    QVariant value = m_fieldref->value();
    QVariant newvalue;
    if (value.isNull()) {  // NULL -> true
        newvalue = true;
    } else if (value.toBool()) {  // true -> false
        newvalue = false;
    } else {  // false -> either NULL or true
        newvalue = m_allow_unset ? QVariant() : true;
    }
    m_fieldref->setValue(newvalue);  // Will trigger valueChanged
}


void QuBoolean::valueChanged(const QVariant &value)
{
    qDebug().nospace() << "QuBooleanText: receiving valueChanged: this="
                       << this  << ", value=" << value;
    if (!m_indicator) {
        qDebug() << "... NO INDICATOR";
        return;
    }
    m_indicator->setValue(value, m_mandatory);
}
