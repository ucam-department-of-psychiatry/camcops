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

#ifdef Q_OS_ANDROID
#include <QEvent>
#include <QGuiApplication>
#endif

#include <QLabel>
#include <QLayout>
#include <QLineEdit>
#include <QPalette>
#include <QTimer>
#include <QValidator>
#include <QWidget>

#include "common/uiconst.h"
#include "lib/filefunc.h"
#include "lib/timerfunc.h"
#include "lib/widgetfunc.h"
#include "qobjects/focuswatcher.h"

#define DEBUG_VALIDATING_LINEEDIT

const int WRITE_DELAY_MS = 400;

ValidatingLineEdit::ValidatingLineEdit(
    QValidator* validator, const bool read_only, const bool delayed, const bool vertical, QWidget* parent
) :
    QWidget(parent),
    m_delayed(delayed),
    m_focus_watcher(nullptr)
{
    m_line_edit = new QLineEdit();
    m_line_edit->setStyleSheet(filefunc::textfileContents(uiconst::CSS_CAMCOPS_VALIDATINGLINEEDIT));

    QLayout* layout;

    if (vertical) {
        layout = new QVBoxLayout();
        // layout->setAlignment(Qt::AlignLeft | Qt::AlignTop);
    } else {
        layout = new QHBoxLayout();
    }
    layout->setContentsMargins(0, 0, 0, 0);
    setLayout(layout);

    layout->addWidget(m_line_edit);

#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif

    if (!read_only and validator) {
        if (delayed) {
            timerfunc::makeSingleShotTimer(m_timer);
            connect(
                m_timer.data(),
                &QTimer::timeout,
                this,
                &ValidatingLineEdit::textChanged
            );
            connect(
                m_line_edit,
                &QLineEdit::textChanged,
                this,
                &ValidatingLineEdit::keystroke
            );
        } else {
            connect(
                m_line_edit,
                &QLineEdit::textChanged,
                this,
                &ValidatingLineEdit::textChanged
            );
        }

        // QLineEdit::textChanged: emitted whenever text changed.
        // QLineEdit::textEdited: NOT emitted when the widget's value is set
        //      programmatically.
        // QLineEdit::editingFinished: emitted when Return/Enter is pressed,
        //      or the editor loses focus. In the former case, only fires if
        //      validation is passed.
        connect(
            m_line_edit,
            &QLineEdit::editingFinished,
            this,
            &ValidatingLineEdit::widgetTextChangedAndValid
        );

        // So, if we lose focus without validation, how are we going to revert
        // to something sensible?
        m_focus_watcher = new FocusWatcher(m_line_edit.data());
        connect(
            m_focus_watcher.data(),
            &FocusWatcher::focusChanged,
            this,
            &ValidatingLineEdit::widgetFocusChanged
        );

        m_label = new QLabel();
        if (vertical) {
            m_label->setAlignment(Qt::AlignRight);
        }
        layout->addWidget(m_label);

        m_line_edit->setValidator(validator);
    }
}

void ValidatingLineEdit::addInputMethodHints(Qt::InputMethodHints hints)
{
    auto existing_hints = m_line_edit->inputMethodHints();
    m_line_edit->setInputMethodHints(existing_hints | hints);
}

void ValidatingLineEdit::keystroke()
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_delayed);

    m_timer->start(WRITE_DELAY_MS);
}

void ValidatingLineEdit::widgetTextChangedAndValid()
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    if (m_delayed) {
        m_timer->stop();
    }

    emit valid();
}

void ValidatingLineEdit::textChanged()
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    processChangedText();
    validate();
}

void ValidatingLineEdit::processChangedText()
{
    // May be implemented in derived class to change the text
    // in some way before validation
}

QValidator::State ValidatingLineEdit::getState()
{
    return m_state;
}

bool ValidatingLineEdit::isValid() const
{
    return m_state == QValidator::Acceptable;
}

void ValidatingLineEdit::widgetFocusChanged(const bool gaining_focus)
{
    // If focus is leaving the widget, and its state is duff, reset the value.
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    if (gaining_focus) {
        return;
    }

    if (m_delayed) {
        m_timer->stop();  // just in case it's running
    }

    validate();

    if (!isValid()) {
        // Something duff
#ifdef DEBUG_VALIDATING_LINEEDIT
        qDebug() << "Resetting";
#endif
        emit reset();
    }

    resetValidatorFeedback();
}

void ValidatingLineEdit::validate()
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    const QValidator* validator = m_line_edit->validator();
    if (!validator) {
#ifdef DEBUG_VALIDATING_LINEEDIT
        qDebug() << "No validator";
#endif
        return;
    }

    QString text = m_line_edit->text().trimmed();

    if (text.isEmpty()) {
        resetValidatorFeedback();
    } else {
        runValidation(text);
    }

    emit validated();
}

void ValidatingLineEdit::resetValidatorFeedback()
{
    widgetfunc::setPropertyValid(m_line_edit, false);
    widgetfunc::setPropertyInvalid(m_line_edit, false);

    m_label->setText("");
}

void ValidatingLineEdit::runValidation(QString& text)
{
    const QValidator* validator = m_line_edit->validator();
    int pos = 0;

    qDebug() << "Validating: " << text;

    m_state = validator->validate(text, pos);

    const bool is_valid = isValid();
    const QString feedback = is_valid ? tr("Valid") : tr("Invalid");

#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << feedback;
#endif

    widgetfunc::setPropertyValid(m_line_edit, is_valid);
    widgetfunc::setPropertyInvalid(m_line_edit, !is_valid);

    m_label->setText(feedback);

    if (is_valid) {
        emit valid();

        return;
    }

    emit invalid();
}

QString ValidatingLineEdit::text() const
{
    return m_line_edit->text();
}

void ValidatingLineEdit::setTextBlockingSignals(const QString& text)
{
    // Now we're detecting textChanged, we have to block signals for this:
    const QSignalBlocker blocker(m_line_edit);

    setText(text);
}

void ValidatingLineEdit::setText(const QString& text)
{
    m_line_edit->setText(text);
}

void ValidatingLineEdit::setPlaceholderText(const QString& text)
{
    m_line_edit->setPlaceholderText(text);
}

void ValidatingLineEdit::setEchoMode(QLineEdit::EchoMode mode)
{
    m_line_edit->setEchoMode(mode);
}

int ValidatingLineEdit::cursorPosition()
{
    return m_line_edit->cursorPosition();
}

void ValidatingLineEdit::setPropertyMissing(bool missing, bool repolish)
{
    widgetfunc::setPropertyMissing(m_line_edit, missing, repolish);
}

#ifdef Q_OS_ANDROID
void ValidatingLineEdit::ignoreInputMethodEvents()
{
    qDebug() << Q_FUNC_INFO;

    m_line_edit->installEventFilter(this);
}

// Thanks to Axel Spoerl for this workaround for
// https://bugreports.qt.io/browse/QTBUG-115756
// On Android, the cursor does not get updated properly if a dash is appended
// Remove this when fixed (the change on that ticket was actually reverted due
// to a regression elsewhere).
bool ValidatingLineEdit::eventFilter(QObject* obj, QEvent* event)
{
    qDebug() << Q_FUNC_INFO;

    if (obj != m_line_edit || event->type() != QEvent::InputMethod) {
        return false;
    }

    if (m_ignore_next_input_event) {
        m_ignore_next_input_event = false;
        event->ignore();
        return true;
    }

    return false;
}

void ValidatingLineEdit::maybeIgnoreNextInputEvent()
{
    qDebug() << Q_FUNC_INFO;

    if (QGuiApplication::inputMethod()->isVisible()) {
        m_ignore_next_input_event = true;
    }
}
#endif
