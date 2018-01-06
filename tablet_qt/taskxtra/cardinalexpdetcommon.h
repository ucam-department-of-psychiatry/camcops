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
#include <QColor>
#include <QPen>
#include <QPointF>
#include <QRectF>
#include <QString>
#include <QUrl>
#include "graphics/buttonconfig.h"
#include "graphics/textconfig.h"

namespace cardinalexpdetcommon
{

extern const int N_CUES_PER_MODALITY;
extern const qreal MIN_INTENSITY;
extern const qreal MAX_INTENSITY;

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

extern const QString TX_AUDITORY_TARGET_0;
extern const QString TX_AUDITORY_TARGET_0_SHORT;
extern const QString TX_AUDITORY_TARGET_1;
extern const QString TX_AUDITORY_TARGET_1_SHORT;
extern const QString TX_VISUAL_TARGET_0;
extern const QString TX_VISUAL_TARGET_0_SHORT;
extern const QString TX_VISUAL_TARGET_1;
extern const QString TX_VISUAL_TARGET_1_SHORT;

extern const qreal SCENE_WIDTH;
extern const qreal SCENE_HEIGHT;
extern const QRectF SCENE_RECT;
extern const QPointF SCENE_CENTRE;
extern const qreal STIM_SIDE;
extern const QRectF VISUAL_STIM_RECT;
extern const QRectF START_BUTTON_RECT;
extern const QPointF PROMPT_CENTRE;
extern const qreal RESPONSE_BUTTON_TOP;
extern const qreal RESPONSE_BUTTON_HEIGHT;
extern const qreal RESPONSE_BUTTON_WIDTH;
extern const QRectF NO_BUTTON_RECT;
extern const QRectF YES_BUTTON_RECT;
extern const QRectF ABORT_BUTTON_RECT;
extern const QRectF THANKS_BUTTON_RECT;

// Graphics: other
extern const QColor SCENE_BACKGROUND;
extern const int BORDER_WIDTH_PX;
extern const QColor BUTTON_BACKGROUND;
extern const QColor TEXT_COLOUR;
extern const QColor BUTTON_PRESSED_BACKGROUND;
extern const QColor ABORT_BUTTON_BACKGROUND;
extern const qreal TEXT_SIZE_PX;
extern const int BUTTON_RADIUS;
extern const int PADDING;
extern const Qt::Alignment BUTTON_TEXT_ALIGN;
extern const Qt::Alignment TEXT_ALIGN;
extern const QColor EDGE_COLOUR;
extern const QPen BORDER_PEN;
extern const ButtonConfig BASE_BUTTON_CONFIG;
extern const ButtonConfig ABORT_BUTTON_CONFIG;
extern const ButtonConfig CONTINUE_BUTTON_CONFIG;
extern const TextConfig BASE_TEXT_CONFIG;


QUrl urlFromStem(const QString& stem);
QString filenameFromStem(const QString& stem);

}  // namespace cardinalexpdetcommon
