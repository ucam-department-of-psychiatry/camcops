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
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"

class FocusWatcher;
class GrowingPlainTextEdit;
class GrowingTextEdit;

// #define QUTEXTEDIT_USE_PLAIN_TEXT_EDITOR  // not resizing properly!


class QuTextEdit : public QuElement
{
    // Offers an expanding editor for entry of large quantities of text.
    // (For a smaller version, see QuLineEdit.)

    Q_OBJECT
public:
    QuTextEdit(FieldRefPtr fieldref, bool accept_rich_text = false);
    QuTextEdit* setAllowTabsInContent(bool allow_tabs_in_content);
    QuTextEdit* setHint(const QString& hint);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void widgetTextChanged();
    void textChanged();
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
    void widgetFocusChanged(bool in);
protected:
    FieldRefPtr m_fieldref;
    bool m_accept_rich_text;
    bool m_allow_tabs_in_content;
    QString m_hint;
#ifdef QUTEXTEDIT_USE_PLAIN_TEXT_EDITOR
    QPointer<GrowingPlainTextEdit> m_plain_editor;
#endif
    QPointer<GrowingTextEdit> m_rich_editor;
    bool m_ignore_widget_signal;
    QPointer<FocusWatcher> m_focus_watcher;
    QSharedPointer<QTimer> m_timer;
};
