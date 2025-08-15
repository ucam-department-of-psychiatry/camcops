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
#endif
#include <QGuiApplication>
#include <QLabel>
#include <QLayout>
#include <QLineEdit>
#include <QPalette>
#include <QStyleHints>
#include <QTimer>
#include <QValidator>
#include <QWidget>

#include "common/uiconst.h"
#include "lib/filefunc.h"
#include "lib/timerfunc.h"
#include "lib/widgetfunc.h"
#include "qobjects/focuswatcher.h"

// #define DEBUG_VALIDATING_LINEEDIT

const int WRITE_DELAY_MS = 400;

ValidatingLineEdit::ValidatingLineEdit(
    QValidator* validator,
    const bool allow_empty,
    const bool read_only,
    const bool delayed,
    const bool vertical,
    QWidget* parent
) :
    QWidget(parent),
    m_allow_empty(allow_empty),
    m_delayed(delayed),
    m_vertical(vertical),
    m_focus_watcher(nullptr)
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif
    setStyleSheet(
        filefunc::textfileContents(uiconst::CSS_CAMCOPS_VALIDATINGLINEEDIT)
    );

    m_line_edit = new QLineEdit();

    QLayout* layout;

    if (vertical) {
        layout = new QVBoxLayout();
    } else {
        layout = new QHBoxLayout();
    }
    layout->setContentsMargins(0, 0, 0, 0);
    setLayout(layout);

    layout->addWidget(m_line_edit);

    if (!read_only) {
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

        // QLineEdit::textChanged: emitted whenever text changed but not when
        //      validator returns Invalid
        // QLineEdit::textEdited: NOT emitted when the widget's value is set
        //      programmatically.
        // QLineEdit::editingFinished: emitted when Return/Enter is pressed,
        //      or the editor loses focus. In the former case, only fires if
        //      validation is passed.
        // QLineEdit::inputRejected: emitted for example when a keypress
        //      results in a validator returning Invalid.
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
        if (m_vertical) {
            m_label->setAlignment(Qt::AlignRight);
        }
        auto style_hints = QGuiApplication::styleHints();
        auto label_name
            = QString("validatorfeedback%1")
                  .arg(
                      style_hints->colorScheme() == Qt::ColorScheme::Dark
                          ? "dark"
                          : "light"
                  );

        m_label->setObjectName(label_name);
        layout->addWidget(m_label);

        m_line_edit->setValidator(validator);

        resetValidatorFeedback();
    }

    if (!validator) {
        m_state = QValidator::Acceptable;
    }
}

void ValidatingLineEdit::addInputMethodHints(Qt::InputMethodHints hints)
{
    // It is recommended to OR with the existing hints here, even though
    // at the time of writing the default for QLineEdit appears to be ImhNone
    // i.e. zero.
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

QVariant ValidatingLineEdit::getState()
{
    return m_state;
}

void ValidatingLineEdit::widgetFocusChanged(const bool gaining_focus)
{
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

    emit focusLost();
}

void ValidatingLineEdit::validate()
{
#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << Q_FUNC_INFO;
#endif

    QString text = m_line_edit->text().trimmed();
    const QValidator* validator = m_line_edit->validator();

    if (validator) {
        if (text.isEmpty() && m_allow_empty) {
#ifdef DEBUG_VALIDATING_LINEEDIT
            qDebug() << "Allowed to be empty so valid";
#endif
            m_state = QValidator::Acceptable;
        } else {
            int pos = 0;
#ifdef DEBUG_VALIDATING_LINEEDIT
            qDebug() << "Running validator";
#endif
            m_state = validator->validate(text, pos);
        }
    }

    Q_ASSERT(m_state.isNull());

    const bool is_valid = m_state == QValidator::Acceptable;

    if (validator) {
        if (text.isEmpty()) {
            resetValidatorFeedback();
        } else {
            setValidatorFeedback(is_valid, !is_valid);
        }
    }

    if (is_valid) {
#ifdef DEBUG_VALIDATING_LINEEDIT
        qDebug() << "emit valid()";
#endif
        emit valid();
    } else {
#ifdef DEBUG_VALIDATING_LINEEDIT
        qDebug() << "emit invalid()";
#endif
        emit invalid();
    }

    emit validated();
}

void ValidatingLineEdit::resetValidatorFeedback()
{
    setValidatorFeedback(false, false);
}

void ValidatingLineEdit::setValidatorFeedback(
    const bool valid, const bool invalid
)
{
    // If both valid and invalid are false, there is no validation
    Q_ASSERT(!(valid && invalid));

    widgetfunc::setPropertyValid(m_line_edit, valid);
    widgetfunc::setPropertyInvalid(m_line_edit, invalid);

    QString feedback = QString("");
    const bool display_feedback = valid || invalid;

    if (display_feedback) {
        feedback = valid ? tr("Valid") : tr("Invalid");
    }

#ifdef DEBUG_VALIDATING_LINEEDIT
    qDebug() << "Feedback:" << feedback;
#endif

    m_label->setText(feedback);

    // Hide the label if it is to the right of the text box, otherwise the text
    // box looks oddly shorter.
    // If the label is below the text box, don't hide it, otherwise the
    // containing widget will jump around.
    const bool visible = display_feedback || m_vertical;
    m_label->setVisible(visible);
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
    m_line_edit->installEventFilter(this);
}

// Thanks to Axel Spoerl for this workaround for
// https://bugreports.qt.io/browse/QTBUG-115756
// On Android, the cursor does not get updated properly if a dash is appended
// Remove this when fixed (the change on that ticket was actually reverted due
// to a regression elsewhere).
bool ValidatingLineEdit::eventFilter(QObject* obj, QEvent* event)
{
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
    if (QGuiApplication::inputMethod()->isVisible()) {
        m_ignore_next_input_event = true;
    }
}
#endif
