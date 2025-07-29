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

#pragma once
#include <QLabel>
#include <QLineEdit>
#include <QPointer>
#include <QValidator>
#include <QVBoxLayout>

class ValidatingLineEdit : public QVBoxLayout
{
    // One-line text editor with validation and visual feedback

    Q_OBJECT

public:
    ValidatingLineEdit(
        QValidator* validator = nullptr,
        QWidget* parent = nullptr,
        const QString& text = ""
    );

    ValidatingLineEdit(QValidator* validator, const QString& text = "") :
        ValidatingLineEdit(validator, nullptr, text)
    {
    }

    void textChanged();
    QValidator::State getState();
    bool isValid();
    QPointer<QLineEdit> getLineEdit();

protected:
    virtual void processChangedText();

private:
    QLabel* m_label;
    QPointer<QLineEdit> m_line_edit;
    QValidator::State m_state;

signals:
    void validated();
};
