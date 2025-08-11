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
#include <QLineEdit>  // for EchoMode

#include "db/fieldref.h"
#include "questionnairelib/quelement.h"
#include "widgets/validatinglineedit.h"

class QLineEdit;

class QuLineEdit : public QuElement
{
    // Offers a one-line text editor, for a string.
    // (For a bigger version, see QuTextEdit.)

    Q_OBJECT

public:
    // Constructor
    QuLineEdit(FieldRefPtr fieldref, bool allow_empty = true, QObject* parent = nullptr);

    // Sets the hint text (what's shown, greyed out, in the editor when the
    // line editor has no user-entered text in it).
    QuLineEdit* setHint(const QString& hint);

    // Sets the echo mode; e.g. show passwords as blobs.
    QuLineEdit* setEchoMode(QLineEdit::EchoMode echo_mode);

protected:
    // "Update our contents from the data in our field."
    virtual void setFromField();

    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire
    ) override;
    virtual FieldRefPtrList fieldrefs() const override;

    virtual QPointer<QValidator> getValidator();
    virtual Qt::InputMethodHints getInputMethodHints();

protected slots:
    // "The field's data has changed."
    virtual void fieldValueChanged(
        const FieldRef* fieldref, const QObject* originator = nullptr
    );
    virtual void focusLost();
    // Writes new data to our field.
    virtual void widgetTextChangedAndValid();

protected:
    FieldRefPtr m_fieldref;  // our field
    bool m_allow_empty;  // allow an empty field?
    QPointer<QValidator> m_validator;
    QString m_hint;  // hint text
    QPointer<ValidatingLineEdit> m_editor;  // our editor widget
    QLineEdit::EchoMode m_echo_mode;  // echo mode, as above
};
