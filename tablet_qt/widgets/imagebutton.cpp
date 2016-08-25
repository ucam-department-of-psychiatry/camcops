#include "imagebutton.h"
#include <QPainter>
#include "common/uiconstants.h"
#include "lib/uifunc.h"


const int MAX_TEXT_WIDTH_PIXELS = 300;


ImageButton::ImageButton(QWidget* parent) :
    QPushButton(parent)
{
    commonConstructor(QSize());
}


ImageButton::ImageButton(const QString& normal_filename,
                         const QString& pressed_filename,
                         const QSize& size,
                         QWidget* parent) :
    QPushButton(parent)
{
    commonConstructor(size);
    setNormalImage(normal_filename, size);
    setPressedImage(pressed_filename, size);
    resizeIfNoSize();
}


ImageButton::ImageButton(const QString& base_filename,
                         bool filename_is_camcops_stem,
                         bool alter_unpressed_image,
                         bool disabled,
                         QWidget* parent) :
    QPushButton(parent)
{
    QSize size = UiConst::ICONSIZE;
    commonConstructor(size);
    setImages(base_filename, filename_is_camcops_stem, alter_unpressed_image,
              true, disabled);
    resizeIfNoSize();
}


void ImageButton::setImages(const QString& base_filename,
                            bool filename_is_camcops_stem,
                            bool alter_unpressed_image,
                            bool pressed_marker_behind,
                            bool disabled,
                            bool read_only)
{
    // Old way: use two images
    // setNormalImage(UiFunc::iconPngFilename(stem), size);
    // setPressedImage(UiFunc::iconTouchedPngFilename(stem), scale);

    // New way: use one image and apply the background(s) programmatically
    QString filename = filename_is_camcops_stem
            ? UiFunc::iconFilename(base_filename)
            : base_filename;
    QPixmap base = UiFunc::getPixmap(filename, m_image_size);
    if (disabled) {
        QPixmap img = UiFunc::makeDisabledIcon(base);
        setNormalImage(img, false);
        setPressedImage(img, false);
    } else if (read_only) {
        setNormalImage(base, false);
        setPressedImage(base, false);
    } else {
        QPixmap fore = alter_unpressed_image
                ? UiFunc::addUnpressedBackground(base)
                : base;
        setNormalImage(fore, false);
        QPixmap pressed = UiFunc::addPressedBackground(base,
                                                       pressed_marker_behind);
        setPressedImage(pressed, false);
    }
    resizeIfNoSize();
}


void ImageButton::commonConstructor(const QSize& size)
{
    m_image_size = size;
    setAsText(false);
}


void ImageButton::setNormalImage(const QString& filename, const QSize& size,
                                 bool cache)
{
    setNormalImage(UiFunc::getPixmap(filename, size, cache), false);
}


void ImageButton::setNormalImage(const QPixmap& pixmap, bool scale)
{
    m_normal_pixmap = pixmap;
    if (scale) {
        rescale(m_normal_pixmap);
    }
    update();
}


void ImageButton::setPressedImage(const QString& filename, const QSize& size,
                                  bool cache)
{
    setPressedImage(UiFunc::getPixmap(filename, size, cache), false);
}


void ImageButton::setPressedImage(const QPixmap& pixmap, bool scale)
{
    m_pressed_pixmap = pixmap;
    if (scale) {
        rescale(m_pressed_pixmap);
    }
    update();
}


void ImageButton::rescale(QPixmap& pm)
{
    pm = pm.scaled(m_image_size, Qt::IgnoreAspectRatio);
}


void ImageButton::resizeIfNoSize()
{
    if (m_image_size.isEmpty()) {
        m_image_size = m_normal_pixmap.size();
    }
}


void ImageButton::resizeImages(double factor)
{
    m_image_size = QSize(
        factor * m_normal_pixmap.size().width(),
        factor * m_normal_pixmap.size().height()
    );
    rescale(m_normal_pixmap);
    rescale(m_pressed_pixmap);
}


QSize ImageButton::sizeHint() const
{
    if (m_as_text) {
        // INELEGANT! Hard to get a button to word-wrap. ***
        // Alternative would be to derive from a QLabel that does word wrap.
        QSize size = QPushButton::sizeHint();
        if (size.width() > MAX_TEXT_WIDTH_PIXELS) {
            size.setWidth(MAX_TEXT_WIDTH_PIXELS);
        }
        return size;
    } else {
        return m_image_size;
    }
}


void ImageButton::setImageSize(const QSize &size, bool scale)
{
    m_image_size = size;
    if (scale) {
        rescale(m_normal_pixmap);
        rescale(m_pressed_pixmap);
    }
}


void ImageButton::setAsText(bool as_text)
{
    m_as_text = as_text;
    QSizePolicy sp(
        as_text ? QSizePolicy::Expanding : QSizePolicy::Fixed,
        as_text ? QSizePolicy::Expanding : QSizePolicy::Fixed
    );
    setSizePolicy(sp);
}


void ImageButton::paintEvent(QPaintEvent *e)
{
    if (m_as_text) {
        QPushButton::paintEvent(e);
        return;
    }
    QPainter p(this);
    QPixmap& pm = isDown() ? m_pressed_pixmap : m_normal_pixmap;
    p.drawPixmap(0, 0, pm);
}
