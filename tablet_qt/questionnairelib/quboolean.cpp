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

#include "quboolean.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QWidget>
// #include "common/cssconst.h"
#include "lib/uifunc.h"
#include "questionnairelib/mcqfunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/booleanwidget.h"
#include "widgets/clickablelabel.h"
#include "widgets/clickablelabelwordwrapwide.h"
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
    m_indicator = nullptr;
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuBoolean::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuBoolean::fieldValueChanged);
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


QPointer<QWidget> QuBoolean::makeWidget(Questionnaire *questionnaire)
{
    bool read_only = questionnaire->readOnly();

    QPointer<QWidget> widget = new QWidget();
    widget->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);

    QHBoxLayout* layout = new QHBoxLayout();
    layout->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(layout);
    // To align things in a QHBoxLayout, align the widgets within the layout:
    //      layout->setAlignment(widget, alignment)
    // not the layout:
    //      layout->setAlignment(alignment)

    // Label
    QWidget* labelwidget = nullptr;
    if (!m_text.isEmpty() && !m_as_text_button) {
        // Text label
        if (!read_only && m_content_clickable) {
            ClickableLabelWordWrapWide* label = new ClickableLabelWordWrapWide(m_text);
            connect(label, &ClickableLabelWordWrapWide::clicked,
                    this, &QuBoolean::clicked);
            labelwidget = label;
        } else {
            LabelWordWrapWide* label = new LabelWordWrapWide(m_text);
            labelwidget = label;
        }
        int fontsize = questionnaire->fontSizePt(
            m_big_text ? UiConst::FontSize::Big : UiConst::FontSize::Normal);
        QString css = UiFunc::textCSS(fontsize, m_bold, m_italic);
        labelwidget->setStyleSheet(css);
        // needs_stretch stays false (or we'll prevent the text expanding)
    } else if (!m_image_filename.isEmpty()) {
        // Image label
        QPixmap image = UiFunc::getPixmap(m_image_filename, m_image_size);
        if (!read_only && m_content_clickable) {
            ClickableLabel* label = new ClickableLabel();
            label->setPixmap(image);
            connect(label, &ClickableLabel::clicked,
                    this, &QuBoolean::clicked);
            labelwidget = label;
        } else {
            QLabel* label = new QLabel();
            label->setFixedSize(image.size());
            label->setPixmap(image);
            labelwidget = label;
        }
    }
    // otherwise... no label, just the indicator

    // Indicator
    m_indicator = new BooleanWidget();
    m_indicator->setSize(m_big_indicator);
    m_indicator->setBold(m_bold);
    m_indicator->setReadOnly(read_only);
    if (m_as_text_button) {
        m_indicator->setAppearance(BooleanWidget::Appearance::Text);
        m_indicator->setText(m_text);
    } else {
        m_indicator->setAppearance(BooleanWidget::Appearance::CheckRed);
    }
    if (!read_only) {
        connect(m_indicator, &BooleanWidget::clicked,
                this, &QuBoolean::clicked);
    }

    // Whole thing
    if (labelwidget) {
        if (m_indicator_on_left) {
            layout->addWidget(m_indicator);
            layout->addWidget(labelwidget);
        } else {
            layout->addWidget(labelwidget);
            layout->addWidget(m_indicator);
        }
        layout->setAlignment(labelwidget, Qt::AlignVCenter);
    } else {
        // Just the indicator
        layout->addWidget(m_indicator);
    }
    layout->addStretch();
    layout->setAlignment(m_indicator, Qt::AlignTop);

    setFromField();

    return widget;
}


void QuBoolean::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


void QuBoolean::clicked()
{
    McqFunc::toggleBooleanField(m_fieldref.data(), m_allow_unset);
    emit elementValueChanged();
}


void QuBoolean::fieldValueChanged(const FieldRef* fieldref)
{
    if (!m_indicator) {
        qDebug() << "... NO INDICATOR";
        return;
    }
    m_indicator->setValue(fieldref->value(), fieldref->mandatory());
}


FieldRefPtrList QuBoolean::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
