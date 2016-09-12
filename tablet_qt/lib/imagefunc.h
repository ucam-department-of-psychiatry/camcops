#pragma once
#include <QImage>

class QVideoFrame;


namespace ImageFunc {
    QImage imageFromVideoFrame(const QVideoFrame& buffer);
}
