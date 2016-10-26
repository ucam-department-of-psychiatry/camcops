#include "aspectratiopixmaplabel.h"
#include <QDebug>
#include "common/uiconstants.h"


AspectRatioPixmapLabel::AspectRatioPixmapLabel(QWidget* parent) :
    QLabel(parent)
{
    setScaledContents(false);

    QSizePolicy sp(QSizePolicy::Maximum, QSizePolicy::Fixed);
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
            ? 0  // a bit arbitrary! width()? 0? 1?
            : ((qreal)m_pixmap.height() * width) / m_pixmap.width();
    // qDebug() << Q_FUNC_INFO << "width" << width << "-> height" << h;
    return h;
}


QSize AspectRatioPixmapLabel::sizeHint() const
{
    QSize hint = m_pixmap.size();
    // hint.rheight() = -1;
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


QSize AspectRatioPixmapLabel::minimumSizeHint() const
{
    return QSize(0, 0);
}


QPixmap AspectRatioPixmapLabel::scaledPixmap() const
{
    // qDebug() << Q_FUNC_INFO << "this->size()" << this->size();
    return m_pixmap.scaled(this->size(),
                      Qt::KeepAspectRatio, Qt::SmoothTransformation);
}


void AspectRatioPixmapLabel::resizeEvent(QResizeEvent* event)
{
    Q_UNUSED(event)
    if (!m_pixmap.isNull()) {
        QLabel::setPixmap(scaledPixmap());
        updateGeometry(); // WATCH OUT: any potential for infinite recursion?
    }
}


void AspectRatioPixmapLabel::clear()
{
    // qDebug() << Q_FUNC_INFO;
    // If you set (1) a giant pixmap and then (2) a null pixmap, you can have
    // your size remain at the giant size.
    QPixmap blank(1, 1);
    blank.fill(UiConst::BLACK_TRANSPARENT);
    setPixmap(blank);
}
