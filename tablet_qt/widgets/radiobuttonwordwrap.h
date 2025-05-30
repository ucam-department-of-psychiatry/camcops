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

/*
Based on CheckBoxWordWrap:
https://github.com/ThiBsc/qtCustomPlugins/tree/master/plugins/CheckBoxWordWrap
which has the following license:

MIT License

Copyright (c) 2018 Thibaut B.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// This is a workaround until QRadioButton supports word-wrap
// (https://bugreports.qt.io/browse/QTBUG-5370 for checkbox)

#pragma once

#include <QHBoxLayout>
#include <QRadioButton>

#include "clickablelabel.h"

class RadioButtonWordWrap : public QRadioButton
{
    Q_OBJECT

    Q_PROPERTY(bool wordwrap READ isWordWrap WRITE setWordWrap)
    Q_PROPERTY(QString text READ text WRITE setText)

public:
    RadioButtonWordWrap(QWidget* parent = Q_NULLPTR);
    RadioButtonWordWrap(const QString& text, QWidget* parent = Q_NULLPTR);
    ~RadioButtonWordWrap();
    bool isWordWrap() const;
    void setWordWrap(bool wordwrap);
    QString text() const;
    void setText(const QString& text);
    QSize sizeHint() const override;

private slots:
    void labelIsClicked();

protected:
    void resizeEvent(QResizeEvent* event) override;

private:
    void init();
    const int separation = 5;
    QHBoxLayout* m_main_layout;
    ClickableLabel* m_label;
};
