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
#include <QMediaPlayer>
#include "questionnairelib/quelement.h"

class QAbstractButton;
class QWidget;


class QuAudioPlayer : public QuElement
{
    // Element to play audio.
    // Offers a play/stop button, +/- a volume control.

    Q_OBJECT
public:
    QuAudioPlayer(const QString& url);
    virtual ~QuAudioPlayer();
    QuAudioPlayer* setVolume(int volume);
    QuAudioPlayer* setOfferVolumeControl(bool offer_volume_control = true);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual void closing();
protected slots:
    void play();
    void stop();
    void mediaStatusChanged(QMediaPlayer::MediaStatus status);
public slots:
    void setVolumeNoReturn(int volume);
protected:
    QString m_url;
    int m_volume;
    bool m_offer_volume_control;
    QPointer<QAbstractButton> m_button_speaker;
    QPointer<QAbstractButton> m_button_speaker_playing;
    QSharedPointer<QMediaPlayer> m_player;  // not owned by other widgets
    bool m_playing;
};
