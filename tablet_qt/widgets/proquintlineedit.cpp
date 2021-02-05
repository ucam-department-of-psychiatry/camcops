/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QString>

#include "qobjects/proquintvalidator.h"
#include "widgets/validatinglineedit.h"

#include "proquintlineedit.h"

ProquintLineEdit::ProquintLineEdit(QWidget* parent) :
    ValidatingLineEdit(new ProquintValidator(), parent)
{
    getLineEdit()->setInputMethodHints(Qt::ImhSensitiveData |
                                       Qt::ImhNoAutoUppercase |
                                       Qt::ImhNoPredictiveText);
    m_old_text = "";
};


void ProquintLineEdit::processChangedText()
{
    // Automatically strip white space and insert the dashes, because it's a
    // pain having to do that on a mobile on-screen keyboard
    auto line_edit = getLineEdit();

    QString initial_text = line_edit->text();

    const bool cursor_at_end = (line_edit->cursorPosition() == initial_text.length());

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
        if (new_text.length() < 49) {
            int prev_dash_pos = new_text.lastIndexOf('-');
            if ((new_text.length() - prev_dash_pos) == 6) {
                new_text += '-';
            }
        }
    }

    // Set text will put the cursor to the end so only set it if it has changed
    if (new_text != initial_text) {
        line_edit->setText(new_text);
    }

    m_old_text = new_text;
}
