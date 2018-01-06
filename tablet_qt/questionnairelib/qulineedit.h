/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once
#include <QLineEdit>  // for EchoMode
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"

class FocusWatcher;
class QLineEdit;


class QuLineEdit : public QuElement
{
    // Offers a one-line text editor, for a string.
    // (For a bigger version, see QuTextEdit.)

    Q_OBJECT
public:
    QuLineEdit(FieldRefPtr fieldref);
    QuLineEdit* setHint(const QString& hint);
    QuLineEdit* setEchoMode(QLineEdit::EchoMode echo_mode);
protected:
    virtual void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void extraLineEditCreation(QLineEdit* editor);  // override to specialize
protected slots:
    virtual void keystroke();
    virtual void widgetTextChangedMaybeValid();
    virtual void widgetTextChangedAndValid();
    virtual void fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator = nullptr);
    virtual void widgetFocusChanged(bool in);
protected:
    FieldRefPtr m_fieldref;
    QString m_hint;
    QPointer<QLineEdit> m_editor;
    QPointer<FocusWatcher> m_focus_watcher;
    QSharedPointer<QTimer> m_timer;
    QLineEdit::EchoMode m_echo_mode;
};
