#include "quimage.h"
#include <QLabel>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"


QuImage::QuImage(const QString& filename, const QSize& size) :
    m_filename(filename),
    m_fieldref(nullptr),
    m_label(nullptr),
    m_size(size)
{
}


QuImage::QuImage(FieldRefPtr fieldref, const QSize& size) :
    m_filename(""),
    m_fieldref(fieldref),
    m_label(nullptr),
    m_size(size)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuImage::valueChanged);
}


QuImage* QuImage::setSize(const QSize& size)
{
    m_size = size;
    return this;
}


QPointer<QWidget> QuImage::makeWidget(Questionnaire* questionnaire)
{
    Q_UNUSED(questionnaire)
    m_label = new QLabel();
    QPixmap image;
    if (m_fieldref && m_fieldref->valid()) {
        QByteArray data = m_fieldref->valueByteArray();
        image.loadFromData(data);
    } else {
        image = UiFunc::getPixmap(m_filename);
    }
    if (m_size.isValid()) {
        image = image.scaled(m_size);
    }
    m_label->setFixedSize(image.size());
    m_label->setPixmap(image);
    return QPointer<QWidget>(m_label);
}


void QuImage::valueChanged(const FieldRef* fieldref)
{
    if (!m_label) {
        return;
    }
    QPixmap image;
    image.loadFromData(fieldref->valueByteArray());
    m_label->setPixmap(image);
}
