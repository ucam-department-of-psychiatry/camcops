#pragma once
#include "quelement.h"

class QLabel;
class QMediaPlayer;
class QPushButton;
class QTimer;


class QuCountdown : public QuElement
{
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
    QPointer<QTimer> m_timer;
    QSharedPointer<QMediaPlayer> m_player;  // not owned by other widgets
    int m_whole_seconds_left;
};
