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
#include "questionnairelib/quelement.h"

class QLabel;
class QMediaPlayer;
class QPushButton;
class QTimer;


class QuCountdown : public QuElement
{
    // Offers a countdown timer (which plays a sound on timeout), e.g. for
    // allowing the respondent a certain amount of time for a task.
    // Offers start/stop/reset controls.

    Q_OBJECT
public:
    QuCountdown(int time_s);
    virtual ~QuCountdown();
    QuCountdown* setVolume(int volume);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    void updateDisplay();
    void bong();
protected slots:
    void start();
    void stop();
    void reset();
    void tick();
protected:
    int m_time_s;
    int m_volume;
    bool m_running;
    QPointer<QPushButton> m_start_button;
    QPointer<QPushButton> m_stop_button;
    QPointer<QPushButton> m_reset_button;
    QPointer<QLabel> m_label;
    QSharedPointer<QTimer> m_timer;
    QSharedPointer<QMediaPlayer> m_player;  // not owned by other widgets
    double m_seconds_left;
};
