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

#include "soundfunc.h"
#include <QMediaPlayer>
#include "maths/mathfunc.h"

namespace soundfunc {


void makeMediaPlayer(QSharedPointer<QMediaPlayer>& player)
{
    player = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                          &QObject::deleteLater);
    // http://doc.qt.io/qt-5/qsharedpointer.html
    // Failing to use deleteLater() can cause crashes, as there may be
    // outstanding events relating to this object.
    // ... but it's not enough; see finishMediaPlayer().
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


void setVolume(const QSharedPointer<QMediaPlayer>& player,
               const int volume_percent)
{
    player->setVolume(volume_percent);
}


void setVolume(const QSharedPointer<QMediaPlayer>& player,
               const double volume_proportion)
{
    player->setVolume(mathfunc::proportionToIntPercent(volume_proportion));
}


}  // namespace soundfunc
