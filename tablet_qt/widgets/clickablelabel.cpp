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

#include "clickablelabel.h"
#include <QApplication>
#include <QDebug>
#include <QLabel>
#include <QMouseEvent>
#include <QStyleOptionButton>
#include <QVBoxLayout>
// #include "common/cssconst.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"


ClickableLabel::ClickableLabel(const QString& text, QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(text, this))
{
    commonConstructor();
}


ClickableLabel::ClickableLabel(QWidget* parent) :
    QPushButton(parent),
    m_label(new QLabel(this))
{
    commonConstructor();
}


void ClickableLabel::commonConstructor()
{
    m_label->setMouseTracking(false);
    m_label->setTextInteractionFlags(Qt::NoTextInteraction);
    m_label->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    // m_label->setObjectName(CssConst::DEBUG_GREEN);

    m_layout = new QVBoxLayout();
    m_layout->setContentsMargins(UiConst::NO_MARGINS);

    m_layout->addWidget(m_label);

    setLayout(m_layout);
    // Default size policy is (QSizePolicy::Preferred, QSizePolicy::Preferred);
    // see qwidget.cpp
    setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Fixed);
}


void ClickableLabel::setTextFormat(Qt::TextFormat format)
{
    Q_ASSERT(m_label);
    m_label->setTextFormat(format);
}


void ClickableLabel::setWordWrap(bool on)
{
    Q_ASSERT(m_label);
    m_label->setWordWrap(on);
    updateGeometry();
}


void ClickableLabel::setAlignment(Qt::Alignment alignment)
{
    Q_ASSERT(m_label);
    Q_ASSERT(m_layout);
    m_label->setAlignment(alignment);
    m_layout->setAlignment(m_label, alignment);
}


void ClickableLabel::setOpenExternalLinks(bool open)
{
    Q_ASSERT(m_label);
    m_label->setOpenExternalLinks(open);
}


void ClickableLabel::setPixmap(const QPixmap& pixmap)
{
    Q_ASSERT(m_label);
    m_label->setPixmap(pixmap);
    setFixedSize(pixmap.size());
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    updateGeometry();
}


QSize ClickableLabel::sizeHint() const
{
    Q_ASSERT(m_label);
    QStyleOptionButton opt;
    initStyleOption(&opt);  // protected
    return UiFunc::pushButtonSizeHintFromContents(this, &opt,
                                                  m_label->sizeHint());
}
