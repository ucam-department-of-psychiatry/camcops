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

#include "proquintlineedit.h"

#include <QString>

#include "qobjects/proquintvalidator.h"
#include "widgets/validatinglineedit.h"

ProquintLineEdit::ProquintLineEdit(QWidget* parent) :
    ValidatingLineEdit(new ProquintValidator(), parent)
{
    addInputMethodHints(
        Qt::ImhSensitiveData | Qt::ImhNoAutoUppercase | Qt::ImhNoPredictiveText
    );
    m_old_text = "";

#ifdef Q_OS_ANDROID
    ignoreInputMethodEvents();
#endif
}

void ProquintLineEdit::processChangedText()
{
    // Automatically strip white space and insert the dashes, because it's a
    // pain having to do that on a mobile on-screen keyboard
    QString initial_text = text();
    const bool cursor_at_end = (cursorPosition() == initial_text.length());
    QString new_text = initial_text.trimmed();

    // Only add a dash when cursor is at the end and we're not deleting...
    if (cursor_at_end && new_text.startsWith(m_old_text)) {
        //                  1111111
        //        01234567890123456
        //        kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov-t
        //            ^     ^     ^                               ^
        // Len        5    11    17 ...                          49
        // Prev dash -1     5    11

        // ...or beyond the maximum length
        const int max_len = 8 * 6 + 1;  // 8 groups of 5-and-dash, then check
        if (new_text.length() < max_len) {
            int prev_dash_pos = new_text.lastIndexOf('-');
            if ((new_text.length() - prev_dash_pos) == 6) {
                new_text += '-';
            }
        }
    }

    // Set text will put the cursor to the end so only set it if it has changed
    if (new_text != initial_text) {
#ifdef Q_OS_ANDROID
        maybeIgnoreNextInputEvent();
#endif
        setText(new_text);
    }

    m_old_text = new_text;
}
