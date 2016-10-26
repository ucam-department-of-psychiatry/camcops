#pragma once

// http://stackoverflow.com/questions/5653114/display-image-in-qt-to-fit-label-size
// http://stackoverflow.com/questions/8211982/qt-resizing-a-qlabel-containing-a-qpixmap-while-keeping-its-aspect-ratio
// ... hacked around a bit, because it wasn't using more size when offered
// http://stackoverflow.com/questions/24264320/qt-layouts-keep-widget-aspect-ratio-while-resizing/24264774

// Eventually this:
// http://stackoverflow.com/questions/452333/how-to-maintain-widgets-aspect-ratio-in-qt
// https://forum.qt.io/topic/29859/solved-trying-to-fix-aspect-ratio-of-a-widget-big-problems-with-layouts/5

// Consensus that setHeightForWidth doesn't work terribly well...

#include <QLabel>
#include <QPixmap>
#include <QResizeEvent>


class AspectRatioPixmapLabel : public QLabel
{
    // Image that retains its aspect ratio, for displaying photos.
    // Displays image UP TO its original size.

    Q_OBJECT
public:
    explicit AspectRatioPixmapLabel(QWidget* parent = nullptr);
    virtual int heightForWidth(int width) const override;
    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
    QPixmap scaledPixmap() const;
    void clear();
public slots:
    void setPixmap(const QPixmap& pixmap);
    void resizeEvent(QResizeEvent* event) override;
private:
    QPixmap m_pixmap;
};
