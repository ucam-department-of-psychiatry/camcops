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

#include <QPointer>
#include "core/camcopsapp.h"
#include "questionnairelib/qupage.h"
#include "widgets/basewidget.h"

class ImageButton;
class QAbstractButton;
class QLabel;
class QPushButton;


class QuestionnaireHeader : public BaseWidget
{
    // Provides a questionnaire's title and its control buttons (e.g. page
    // movement, cancellation).

    Q_OBJECT
public:
    QuestionnaireHeader(QWidget* parent, const QString& title,
                        bool read_only, bool jump_allowed, bool within_chain,
                        const QString& css_name, bool debug_allowed = false);
    void setButtons(bool previous, bool next, bool finish);
    void setFinishButtonIcon(const QString& base_filename);
signals:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
    void debugLayout();
protected:
    QString m_title;
    QPointer<QPushButton> m_button_debug;
    QPointer<QAbstractButton> m_button_jump;
    QPointer<QAbstractButton> m_button_previous;
    QPointer<QAbstractButton> m_button_next;
    QPointer<ImageButton> m_button_finish;
    QPointer<QLabel> m_icon_no_next;
};
