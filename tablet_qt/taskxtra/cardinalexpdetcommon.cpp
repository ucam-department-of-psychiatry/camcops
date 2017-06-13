/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "cardinalexpdetcommon.h"
#include <QObject>
#include "lib/uifunc.h"

#define TR(stringname, text) const QString stringname(QObject::tr(text))


namespace cardinalexpdetcommon
{

const QString AUDITORY_BACKGROUND("A_background.wav");
const QStringList AUDITORY_CUES{
    "A_cue_00_pluck.wav",
    "A_cue_01_river.wav",
    "A_cue_02_bird.wav",
    "A_cue_03_morse.wav",
    "A_cue_04_cymbal.wav",
    "A_cue_05_match.wav",
    "A_cue_06_metal.wav",
    "A_cue_07_bach.wav",
};
const QStringList AUDITORY_TARGETS{
    "A_target_0_tone.wav",
    "A_target_1_voice.wav",
};
const QString VISUAL_BACKGROUND("V_background.png");
const QStringList VISUAL_CUES{
    "V_cue_00.png",
    "V_cue_01.png",
    "V_cue_02.png",
    "V_cue_03.png",
    "V_cue_04.png",
    "V_cue_05.png",
    "V_cue_06.png",
    "V_cue_07.png",
};
const QStringList VISUAL_TARGETS{
    "V_target_0_circle.png",
    "V_target_1_word.png",
};

const int MODALITY_AUDITORY = 0;
const int MODALITY_VISUAL = 1;

const int SOUNDTEST_VOLUME = 100;
TR(SOUNDTEST_TITLE, "Sound test for Cardinal RN / Expectation–Detection task");
TR(SOUNDTEST_SUBTITLE,
   "Plays the auditory background sound. (Use maximum device volume. "
   "Should be 60.0 dB(A).)");

TR(TX_CONFIG_VISUAL_TARGET_DURATION_S,
   "Visual target duration (s) (e.g. 1.0):");


QUrl urlFromStem(const QString& stem)
{
    return uifunc::resourceUrl(QString("/expdet/%1").arg(stem));
}


QString filenameFromStem(const QString& stem)
{
    return uifunc::resourceFilename(QString("/expdet/%1").arg(stem));
}


}  // namespace cardinalexpdetcommon
