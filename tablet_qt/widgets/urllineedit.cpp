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

#include "urllineedit.h"

#include "qobjects/urlvalidator.h"
#include "widgets/validatinglineedit.h"

UrlLineEdit::UrlLineEdit(QWidget* parent) :
    ValidatingLineEdit(new UrlValidator(), parent)
{
}

void UrlLineEdit::processChangedText()
{
    QString initial_text = text();
    QString new_text = initial_text.trimmed();

    if (new_text != initial_text) {
        setTextBlockingSignals(new_text);
    }
}
