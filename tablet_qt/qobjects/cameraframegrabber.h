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

#pragma once
#include <QList>
#include <QVideoFrame>
#include <QVideoFrameFormat>
#include <QVideoSink>

class CameraFrameGrabber : public QVideoSink
{
    // Class to use a video surface as a camera's viewfinder, and grab a frame
    // from it.

    Q_OBJECT
public:
    explicit CameraFrameGrabber(QObject* parent = nullptr);
signals:
    void frameAvailable(QImage image);  // QImage is copy-on-write
    // ... https://stackoverflow.com/questions/8455887/stack-object-qt-signal-and-parameter-as-reference/18146433
};
