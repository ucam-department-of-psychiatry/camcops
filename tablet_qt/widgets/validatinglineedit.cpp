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

#include "validatinglineedit.h"

#include <QColor>
#include <QDialog>
#include <QLabel>
#include <QLineEdit>
#include <QPalette>
#include <QValidator>
#include <QWidget>

const QColor& GOOD_FOREGROUND = Qt::black;
const QColor& GOOD_BACKGROUND = Qt::green;
const QColor& BAD_FOREGROUND = Qt::white;
const QColor& BAD_BACKGROUND = Qt::red;

ValidatingLineEdit::ValidatingLineEdit(
    QValidator* validator, QWidget* parent, const QString& text
) :
    QVBoxLayout(parent)
{
    m_line_edit = new QLineEdit();
    m_line_edit->setValidator(validator);

    connect(
        m_line_edit,
        &QLineEdit::textChanged,
        this,
        &ValidatingLineEdit::textChanged
    );
    m_label = new QLabel();

    addWidget(m_line_edit);
    addWidget(m_label);
    setAlignment(Qt::AlignLeft | Qt::AlignTop);

    if (!text.isEmpty()) {
        m_line_edit->setText(text);
    }
}

void ValidatingLineEdit::textChanged()
{
    processChangedText();

    int pos = 0;
    QString text = m_line_edit->text().trimmed();

    m_state = m_line_edit->validator()->validate(text, pos);

    const QColor background = isValid() ? GOOD_BACKGROUND : BAD_BACKGROUND;
    const QColor foreground = isValid() ? GOOD_FOREGROUND : BAD_FOREGROUND;
    const QString feedback = isValid() ? tr("Valid") : tr("Invalid");

    QPalette palette;
    palette.setColor(QPalette::Base, background);
    palette.setColor(QPalette::Text, foreground);

    m_line_edit->setPalette(palette);
    m_label->setText(feedback);
    m_label->setAlignment(Qt::AlignRight);

    emit validated();
}

void ValidatingLineEdit::processChangedText()
{
    // May be implemented in base class to change the text
    // in some way before validation
}

QLineEdit* ValidatingLineEdit::getLineEdit()
{
    return m_line_edit;
}

QValidator::State ValidatingLineEdit::getState()
{
    return m_state;
}

bool ValidatingLineEdit::isValid()
{
    return m_state == QValidator::Acceptable;
}
