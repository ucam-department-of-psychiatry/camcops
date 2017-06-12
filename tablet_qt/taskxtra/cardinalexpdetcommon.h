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

#pragma once
#include <QString>
#include <QUrl>

namespace cardinalexpdetcommon
{

extern const QString AUDITORY_BACKGROUND;
extern const QStringList AUDITORY_CUES;
extern const QStringList AUDITORY_TARGETS;
extern const QString VISUAL_BACKGROUND;
extern const QStringList VISUAL_CUES;
extern const QStringList VISUAL_TARGETS;

extern const int MODALITY_AUDITORY;
extern const int MODALITY_VISUAL;

extern const int SOUNDTEST_VOLUME;
extern const QString SOUNDTEST_TITLE;
extern const QString SOUNDTEST_SUBTITLE;

extern const QString TX_CONFIG_VISUAL_TARGET_DURATION_S;

QUrl urlFromStem(const QString& stem);

}  // namespace cardinalexpdetcommon
