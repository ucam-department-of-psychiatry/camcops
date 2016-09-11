#include "aspectratiopixmaplabel.h"
#include <QDebug>


AspectRatioPixmapLabel::AspectRatioPixmapLabel(QWidget* parent) :
    QLabel(parent)
{
    setScaledContents(false);
    setMinimumSize(1, 1);

    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Maximum);
    sp.setHeightForWidth(true);
    setSizePolicy(sp);
    updateGeometry();
}


void AspectRatioPixmapLabel::setPixmap(const QPixmap& pixmap)
{
    m_pixmap = pixmap;
    QLabel::setPixmap(scaledPixmap());
    updateGeometry();
}


int AspectRatioPixmapLabel::heightForWidth(int width) const
{
    int h = m_pixmap.isNull()
            ? height()
            : ((qreal)m_pixmap.height() * width) / m_pixmap.width();
    // qDebug() << Q_FUNC_INFO << "width" << width << "-> height" << h;
    return h;
}


QSize AspectRatioPixmapLabel::sizeHint() const
{
    // int w = this->width();
    // QSize hint = QSize(w, heightForWidth(w));
    QSize hint = m_pixmap.size();
    hint.rheight() = -1;
    // hint.rheight() = 1;
    // hint = QSize(50, 50);
    // hint = QSize(1, 1);
    // qDebug() << Q_FUNC_INFO << "pixmap size" << m_pixmap.size()
    //          << "size hint" << hint;
    return hint;

    // PROBLEM with AspectRatioPixmapLabel
    // If you have a 1920 x 1080 pixmap, then if you don't override sizeHint
    // you get something like a 640x380 default size. If you want the pixmap
    // to expand horizontally, you need to give a sizeHint.
    // However, if you give a sizeHint that's 1920 x 1080, the layout may
    // reduce the horizontal direction, but won't reduce the vertical
    // direction. Then, the *actual* image size is appropriately reduced
    // vertically by the resizeEvent() code, so you get a pixmap with
    // big top-and-bottom borders, because the displayed size is less than
    // the sizeHint.

    // Can you just return a width hint?
    // Well, you can, and that give the opposite problem - a right-hand border
    // with an image that's insufficiently sized.

    // This gets better if you enforce a size policy with
    // setHeightForWidth(true) set.

    // The problem may now be in VerticalScrollArea, having its vertical size
    // too large; not sure.
}


QPixmap AspectRatioPixmapLabel::scaledPixmap() const
{
    // qDebug() << Q_FUNC_INFO << "this->size()" << this->size();
    return m_pixmap.scaled(this->size(),
                      Qt::KeepAspectRatio, Qt::SmoothTransformation);
}


void AspectRatioPixmapLabel::resizeEvent(QResizeEvent* event)
{
    (void)event;
    if (!m_pixmap.isNull()) {
        QLabel::setPixmap(scaledPixmap());
    }
    updateGeometry();
}


void AspectRatioPixmapLabel::clear()
{
    // qDebug() << Q_FUNC_INFO;
    // If you set (1) a giant pixmap and then (2) a null pixmap, you can have
    // your size remain at the giant size.
    QPixmap blank(1, 1);
    QColor transparent(0, 0, 0, 0);
    blank.fill(transparent);
    setPixmap(blank);
}
