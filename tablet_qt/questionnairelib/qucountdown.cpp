#include "qucountdown.h"
#include <functional>
#include <QHBoxLayout>
#include <QLabel>
#include <QMediaPlayer>
#include <QPushButton>
#include <QTimer>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"


QuCountdown::QuCountdown(int time_s) :
    m_time_s(time_s),
    m_volume(UiConst::MAX_VOLUME),
    m_running(false)
{
}


QuCountdown::~QuCountdown()
{
    if (m_player) {
        m_player->stop();
    }
}


QuCountdown* QuCountdown::setVolume(int volume)
{
    m_volume = qBound(UiConst::MIN_VOLUME, volume, UiConst::MAX_VOLUME);
    if (m_player) {
        m_player->setVolume(m_volume);
    }
    return this;
}


QPointer<QWidget> QuCountdown::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
    QHBoxLayout* layout = new QHBoxLayout();
    widget->setLayout(layout);

    bool read_only = questionnaire->readOnly();

    m_start_button = new QPushButton(tr("Start"));
    layout->addWidget(m_start_button);
    m_stop_button = new QPushButton(tr("Stop"));
    layout->addWidget(m_stop_button);
    m_reset_button = new QPushButton(tr("Reset"));
    layout->addWidget(m_reset_button);
    m_label = new QLabel();
    int fontsize = questionnaire->fontSizePt(UiConst::FontSize::Normal);
    QString css = UiFunc::textCSS(fontsize, true);
    m_label->setStyleSheet(css);
    layout->addWidget(m_label);
    layout->addStretch();

    if (read_only) {
        m_start_button->setDisabled(true);
        m_stop_button->setDisabled(true);
        m_reset_button->setDisabled(true);
    } else {
        connect(m_start_button, &QPushButton::clicked,
                this, &QuCountdown::start);
        connect(m_stop_button, &QPushButton::clicked,
                this, &QuCountdown::stop);
        connect(m_reset_button, &QPushButton::clicked,
                this, &QuCountdown::reset);

        m_timer = new QTimer(widget);
        m_timer->setTimerType(Qt::PreciseTimer);  // ms accuracy
        connect(m_timer, &QTimer::timeout,
                this, &QuCountdown::tick);

        m_player = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                                &QObject::deleteLater);
        m_player->setMedia(QUrl(UiConst::SOUND_COUNTDOWN_FINISHED));
    }

    reset();

    return widget;
}


void QuCountdown::start()
{
    if (!m_timer) {
        return;
    }
    m_timer->start(1000);  // ms
    --m_whole_seconds_left;
    m_running = true;
    updateDisplay();
}


void QuCountdown::stop()
{
    if (!m_timer) {
        return;
    }
    m_timer->stop();
    m_running = false;
    updateDisplay();
}


void QuCountdown::reset()
{
    if (m_running) {
        stop();
    }
    m_whole_seconds_left = m_time_s;
    updateDisplay();
}


void QuCountdown::tick()
{
    --m_whole_seconds_left;
    if (m_whole_seconds_left < 0) {
        // Finished!
        qDebug() << "QuCountdown::tick() - finished";
        bong();
        stop();  // will call updateDisplay()
    } else {
        qDebug() << "QuCountdown::tick()" << m_whole_seconds_left
                 << "whole seconds left";
        updateDisplay();
    }
}


void QuCountdown::bong()
{
    if (!m_player) {
        return;
    }
    m_player->play();
}


void QuCountdown::updateDisplay()
{
    if (!m_label) {
        return;
    }
    QString text;
    if (m_whole_seconds_left < 0) {
        text = tr("FINISHED");
    } else {
        text = QString("%1 s").arg(m_whole_seconds_left);
        if (!m_running) {
            text += tr(" (not running)");
        }
    }
    m_label->setText(text);
}
