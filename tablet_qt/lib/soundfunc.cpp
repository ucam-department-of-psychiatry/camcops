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

#include "soundfunc.h"

#include <QAudioDevice>
#include <QAudioOutput>
#include <QDebug>
#include <QMediaDevices>
#include <QMediaPlayer>
#include <QObject>

#include "maths/mathfunc.h"

namespace soundfunc {

const QString UNABLE_TO_CREATE_MEDIA_PLAYER("Unable");

void makeMediaPlayer(QSharedPointer<QMediaPlayer>& player)
{
    // qDebug() << "Default QMediaPlayer() flags: "
    //          << static_cast<int>(QMediaPlayer::Flags());
    // default "flags" argument to QMediaPlayer() is 0, i.e. no flags set.

    qDebug() << "About to call QMediaPlayer()...";
    player = QSharedPointer<QMediaPlayer>(
        new QMediaPlayer(), &QObject::deleteLater
    );
    auto audio_output = new QAudioOutput();
    audio_output->setDevice(QMediaDevices::defaultAudioOutput());
    player->setAudioOutput(audio_output);
    // https://doc.qt.io/qt-6.5/qsharedpointer.html
    // Failing to use deleteLater() can cause crashes, as there may be
    // outstanding events relating to this object.
    // ... but it's not enough; see finishMediaPlayer().
    qDebug() << "... QMediaPlayer() has returned.";

    /*

    Near-crash; very long pause 2019-09-06. Looks like it relates to GStreamer:

        1   ??
        2   ??
        3   ??
        4   g_type_add_interface_static
        5   gst_bin_get_type
        6   ??
        7   g_option_context_parse
        8   gst_init_check
        9   gst_init
        10  QGstreamerPlayerServicePlugin::create(QString const&)
        11  QPluginServiceProvider::requestService(QByteArray const&,
                QMediaServiceProviderHint const&)
        12  QMediaPlayer::QMediaPlayer(QObject *, QFlags<QMediaPlayer::Flag>)
        13  soundfunc::makeMediaPlayer
        14  CardinalExpectationDetection::startTask
        ... <More>

    or

        1  sched_yield
        2  ??
        3  ??
        4  ??
        5  ??
        6  vaTerminate
        7  ??
        8  g_object_unref
        9  gst_object_replace
        10 ??
        11 ??
        12 ??
        13 gst_element_change_state
        14 ??
        15 QGstreamerVideoOverlay::QGstreamerVideoOverlay(QObject *,
                QByteArray const&)
        16 QGstreamerVideoWidgetControl::QGstreamerVideoWidgetControl(
                QObject *, QByteArray const&)
        17 QGstreamerPlayerService::QGstreamerPlayerService(QObject *)
        18 QGstreamerPlayerServicePlugin::create(QString const&)
        19 QPluginServiceProvider::requestService(QByteArray const&,
                QMediaServiceProviderHint const&)
        20 QMediaPlayer::QMediaPlayer(QObject *, QFlags<QMediaPlayer::Flag>)
        21 soundfunc::makeMediaPlayer
        22 CardinalExpectationDetection::startTask
        ... <More>

    This is potentially related to
    https://github.com/OpenBoard-org/OpenBoard/issues/4. On shrike:

        $ gst-inspect-1.0 --version

        gst-inspect-1.0 version 1.14.5
        GStreamer 1.14.5
        https://launchpad.net/distros/ubuntu/+source/gstreamer1.0

    */
}

void finishMediaPlayer(const QSharedPointer<QMediaPlayer>& player)
{
    // The following seems to prevent a crash (even with deleteLater set up by
    // the QSharedPointer<QMediaPlayer>(new ...) call) whereby ongoing events
    // try to go to a non-existing QMediaPlayer.
    // Looks like this is not an uncommon problem:
    //  https://www.google.com/?ion=1&espv=2#q=delete%20qmediaplayer%20crash
    // The crash comes from QMetaObject, from the Qt event loop.

    if (player) {
        player->stop();
    }
}

void setVolume(
    const QSharedPointer<QMediaPlayer>& player, const int volume_percent
)
{
    const qreal volume_proportion
        = mathfunc::intPercentToProportion(volume_percent);
    setVolume(player, volume_proportion);
}

void setVolume(
    const QSharedPointer<QMediaPlayer>& player, const double volume_proportion
)
{
    QAudioOutput* output = player->audioOutput();
    if (output) {
        output->setVolume(volume_proportion);  // argument range: 0 to 1
    }
}


}  // namespace soundfunc
