/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

/*
Based on CheckBoxWordWrap:
https://github.com/ThiBsc/qtCustomPlugins/tree/master/plugins/CheckBoxWordWrap
which has the following license:

MIT License

Copyright (c) 2018 Thibaut B.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include "radiobuttonwordwrap.h"

#include <QHBoxLayout>
#include <QStyle>
#include <QStyleOptionButton>
#include <QWidget>

#include "clickablelabel.h"

RadioButtonWordWrap::RadioButtonWordWrap(QWidget* parent) :
    QRadioButton(parent),
    m_main_layout(new QHBoxLayout(this)),
    m_label(new ClickableLabel(this))
{
    init();
}

RadioButtonWordWrap::RadioButtonWordWrap(
    const QString& text, QWidget* parent
) :
    QRadioButton(parent),
    m_main_layout(new QHBoxLayout(this)),
    m_label(new ClickableLabel(text, this))
{
    init();
}

RadioButtonWordWrap::~RadioButtonWordWrap()
{
    delete m_label;
    delete m_main_layout;
}

bool RadioButtonWordWrap::isWordWrap() const
{
    return m_label->wordWrap();
}

void RadioButtonWordWrap::setWordWrap(bool wordwrap)
{
    m_label->setWordWrap(wordwrap);
}

QString RadioButtonWordWrap::text() const
{
    return m_label->text();
}

void RadioButtonWordWrap::setText(const QString& text)
{
    m_label->setText(text);
}

QSize RadioButtonWordWrap::sizeHint() const
{
    QFontMetrics fm(m_label->font());
    QRect r = m_label->rect();
    r.setLeft(r.left() + m_label->indent() + separation);
    QRect bRect = fm.boundingRect(
        r,
        int(Qt::AlignLeft | Qt::AlignVCenter | Qt::TextWordWrap),
        m_label->text()
    );
    QSize ret = QSize(QWidget::sizeHint().width(), bRect.height());

    return ret;
}

void RadioButtonWordWrap::labelIsClicked()
{
    setChecked(!isChecked());
}

void RadioButtonWordWrap::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    updateGeometry();
}

void RadioButtonWordWrap::init()
{
    setLayout(m_main_layout);
    QStyleOptionButton opt;
    initStyleOption(&opt);
    int indicator_width = style()->pixelMetric(
        QStyle::PixelMetric::PM_IndicatorWidth, &opt, this
    );

    m_main_layout->setContentsMargins(0, 0, 0, 0);
    m_main_layout->addWidget(m_label);
    m_label->setIndent(indicator_width + separation);
    m_label->setWordWrap(true);

    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Minimum);
    connect(m_label, SIGNAL(clicked()), this, SLOT(labelIsClicked()));
}
