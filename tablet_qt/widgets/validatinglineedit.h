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
#include <QWidget>

class FocusWatcher;

class ValidatingLineEdit : public QWidget
{
    // One-line text editor with validation and visual feedback

    Q_OBJECT

public:
    ValidatingLineEdit(
        QValidator* validator = nullptr,
        const bool allow_empty = false,
        const bool read_only = false,
        const bool delayed = false,
        const bool vertical = true,
        QWidget* parent = nullptr
    );

    // If there is no validator, getState() will always return
    // QValidator:Acceptable
    // If there is a validator and validation has not yet been run, this will
    // be a null QVariant.
    // Otherwise the QVariant will contain a QValidator::State.
    QVariant getState();
    void validate();
    void addInputMethodHints(Qt::InputMethodHints hints);
    QString text() const;
    void setText(const QString& text);
    void setTextBlockingSignals(const QString& text);
    void setPlaceholderText(const QString& text);
    void setEchoMode(QLineEdit::EchoMode);
    int cursorPosition();
    void setPropertyMissing(bool missing, bool repolish = true);
    void resetValidatorFeedback();

protected:
    virtual void processChangedText();
    void setValidatorFeedback(const bool valid, const bool invalid);

protected slots:
    // "A key has been pressed."
    // In delayed mode initiates a delay (to prevent rapid typists from getting
    // cross); then calls textChanged().
    virtual void keystroke();

    // Validate and emit valid() or invalid() accordingly
    virtual void textChanged();

    // Finished editing and valid. Emit valid() to anything interested.
    virtual void widgetTextChangedAndValid();

    // "The widget has gained or lost focus."
    virtual void widgetFocusChanged(bool gaining_focus);

private:
    bool m_allow_empty;
    bool m_delayed;  // Delay validation by WRITE_DELAY_MS
    bool m_vertical;
    QLabel* m_label;
    QPointer<QLineEdit> m_line_edit;
    QVariant m_state;
    QSharedPointer<QTimer> m_timer;  // used for typing delay, as above
    QPointer<FocusWatcher> m_focus_watcher;  // used to detect focus change

signals:
    void focusLost();
    void invalid();
    void validated();
    void valid();

#ifdef Q_OS_ANDROID
    // Workaround problem where the cursor does not get updated properly
    // if the text is modified in a textChanged signal, such as where
    // ProquintLineEdit inserts dashes into the access key.

private:
    bool m_ignore_next_input_event = false;

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;
    void ignoreInputMethodEvents();
    void maybeIgnoreNextInputEvent();
#endif
};
