/*
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

#include "quimage.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/aspectratiopixmaplabel.h"


QuImage::QuImage(const QString& filename, const QSize& size) :
    m_filename(filename),
    m_fieldref(nullptr),
    m_label(nullptr),
    m_size(size),
    m_allow_shrink(true)
{
}


QuImage::QuImage(FieldRefPtr fieldref, const QSize& size) :
    m_filename(""),
    m_fieldref(fieldref),
    m_label(nullptr),
    m_size(size),
    m_allow_shrink(true)
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


QuImage* QuImage::setAllowShrink(bool allow_shrink)
{
    m_allow_shrink = allow_shrink;
    return this;
}


QPointer<QWidget> QuImage::makeWidget(Questionnaire* questionnaire)
{
    Q_UNUSED(questionnaire);

    // Fetch image
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

    // Create widget
    m_label = new AspectRatioPixmapLabel();
    if (!m_allow_shrink) {
        m_label->setFixedSize(image.size());
    }
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
