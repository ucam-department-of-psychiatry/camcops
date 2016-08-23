#pragma once
#include "quelement.h"
#include <QMediaPlayer>

class QAbstractButton;
class QWidget;


class QuAudioPlayer : public QuElement
{
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
