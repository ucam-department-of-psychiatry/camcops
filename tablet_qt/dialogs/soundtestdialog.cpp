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

#include "soundtestdialog.h"

#include <QAudioDevice>
#include <QAudioOutput>
#include <QMediaDevices>
#include <QMediaPlayer>

#include "common/textconst.h"
#include "dialogs/logbox.h"
#include "lib/soundfunc.h"
#include "lib/uifunc.h"

SoundTestDialog::SoundTestDialog(
    const QUrl& url, const int volume_percent, QWidget* parent
) :
    LogBox(parent, tr("Sound test"))
{
    soundfunc::makeMediaPlayer(m_player);
    if (!m_player) {
        uifunc::alert(TextConst::unableToCreateMediaPlayer());
        return;
    }
    connect(
        m_player.data(),
        &QMediaPlayer::mediaStatusChanged,
        this,
        &SoundTestDialog::mediaStatusChanged
    );
    // https://doc.qt.io/qt-6.5/qsharedpointer.html
    // Failing to use deleteLater() can cause crashes, as there may be
    // outstanding events relating to this object.
    statusMessage("Trying to play: " + url.toString());
    m_player->setSource(url);

    soundfunc::setVolume(m_player, volume_percent);

    m_player->play();
}

SoundTestDialog::~SoundTestDialog()
{
    // Unsure if necessary - but similar code in QuAudioPlayer was crashing.
    soundfunc::finishMediaPlayer(m_player);
}

void SoundTestDialog::mediaStatusChanged(const QMediaPlayer::MediaStatus status
)
{
    if (status == QMediaPlayer::EndOfMedia) {
        statusMessage("Finished");
        finish(true);
    }
}
