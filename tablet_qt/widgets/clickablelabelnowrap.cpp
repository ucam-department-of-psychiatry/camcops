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

#include "clickablelabelnowrap.h"
#include <QApplication>
#include <QDebug>
#include <QLabel>
#include <QMouseEvent>
#include <QStyleOptionButton>
#include "common/uiconstants.h"
#include "lib/uifunc.h"

#ifdef USE_HFW_LAYOUT
#include "widgets/vboxlayouthfw.h"
#else
#include <QVBoxLayout>
#endif


ClickableLabelNoWrap::ClickableLabelNoWrap(const QString& text, QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(text, this))
{
    commonConstructor();
}


ClickableLabelNoWrap::ClickableLabelNoWrap(QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(this))
{
    commonConstructor();
}


void ClickableLabelNoWrap::commonConstructor()
{
    m_label->setMouseTracking(false);
    m_label->setTextInteractionFlags(Qt::NoTextInteraction);
    m_label->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    // m_label->setObjectName(CssConst::DEBUG_GREEN);

#ifdef USE_HFW_LAYOUT
    m_layout = new VBoxLayoutHfw();
#else
    m_layout = new QVBoxLayout();
#endif
    m_layout->setContentsMargins(UiConst::NO_MARGINS);

    m_layout->addWidget(m_label);

    setLayout(m_layout);
    // Default size policy is (QSizePolicy::Preferred, QSizePolicy::Preferred);
    // see qwidget.cpp
    setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Fixed);
}


void ClickableLabelNoWrap::setTextFormat(Qt::TextFormat format)
{
    Q_ASSERT(m_label);
    m_label->setTextFormat(format);
}


void ClickableLabelNoWrap::setWordWrap(bool on)
{
    Q_ASSERT(m_label);
    m_label->setWordWrap(on);
    updateGeometry();
}


void ClickableLabelNoWrap::setAlignment(Qt::Alignment alignment)
{
    Q_ASSERT(m_label);
    Q_ASSERT(m_layout);
    m_label->setAlignment(alignment);
    m_layout->setAlignment(m_label, alignment);
}


void ClickableLabelNoWrap::setOpenExternalLinks(bool open)
{
    Q_ASSERT(m_label);
    m_label->setOpenExternalLinks(open);
}


void ClickableLabelNoWrap::setPixmap(const QPixmap& pixmap)
{
    Q_ASSERT(m_label);
    m_label->setPixmap(pixmap);
    setFixedSize(pixmap.size());
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    updateGeometry();
}


QSize ClickableLabelNoWrap::sizeHint() const
{
    Q_ASSERT(m_label);
    QStyleOptionButton opt;
    initStyleOption(&opt);  // protected
    QSize base_size = m_label->sizeHint();
    return base_size + UiFunc::pushButtonExtraSizeRequired(this, &opt,
                                                           base_size);
}
