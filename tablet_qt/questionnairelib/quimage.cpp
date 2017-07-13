/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/aspectratiopixmap.h"


QuImage::QuImage(const QString& filename, const QSize& size) :
    m_filename(filename),
    m_fieldref(nullptr),
    m_size(size)
{
    commonConstructor();
}


QuImage::QuImage(FieldRefPtr fieldref, const QSize& size) :
    m_filename(""),
    m_fieldref(fieldref),
    m_size(size)
{
    Q_ASSERT(m_fieldref);
    commonConstructor();
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuImage::valueChanged);
}


void QuImage::commonConstructor()
{
    m_label = nullptr;
    m_adjust_for_dpi = true;
    m_allow_shrink = true;
}


QuImage* QuImage::setAdjustForDpi(bool adjust_for_dpi)
{
    m_adjust_for_dpi = adjust_for_dpi;
    return this;
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
        image = uifunc::getPixmap(m_filename);
    }
    QSize size = m_adjust_for_dpi
            ? convert::convertSizeByDpi(m_size, uiconst::DPI, uiconst::DEFAULT_DPI)
            : m_size;
    if (size.isValid()) {
        image = image.scaled(size);
    }

    // Create widget
    m_label = new AspectRatioPixmap();
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
