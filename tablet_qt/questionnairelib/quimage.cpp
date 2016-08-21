#include "quimage.h"
#include <QLabel>
#include "lib/uifunc.h"
#include "questionnaire.h"


QuImage::QuImage(const QString& filename) :
    m_filename(filename),
    m_fieldref(nullptr)
{
}


QuImage::QuImage(FieldRefPtr fieldref) :
    m_filename(""),
    m_fieldref(fieldref)
{
}


QPointer<QWidget> QuImage::makeWidget(Questionnaire* questionnaire)
{
    (void)questionnaire;
    QLabel* label = new QLabel();
    QPixmap image;
    if (m_fieldref) {
        QByteArray data = m_fieldref->valueByteArray();
        image.loadFromData(data);
    } else {
        image = getPixmap(m_filename);
        // could also use image.load(filename)
    }
    label->setFixedSize(image.size());
    label->setPixmap(image);
    return QPointer<QWidget>(label);
}
