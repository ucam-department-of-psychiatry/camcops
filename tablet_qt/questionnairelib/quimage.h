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

#pragma once
#include "db/fieldref.h"
#include "quelement.h"

class AspectRatioPixmapLabel;


class QuImage : public QuElement
{
    // Displays an image (from a static filename or a field).
    // No user response offered.

    Q_OBJECT
public:
    QuImage(const QString& filename, const QSize& size = QSize());
    QuImage(FieldRefPtr fieldref, const QSize& size = QSize());
    // ... field provides raw image data
    // The default value of size takes the image's own size.
    QuImage* setSize(const QSize& size);
    QuImage* setAllowShrink(bool allow_shrink);
protected slots:
    void valueChanged(const FieldRef* fieldref);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected:
    QString m_filename;
    FieldRefPtr m_fieldref;
    QPointer<AspectRatioPixmapLabel> m_label;
    QSize m_size;
    bool m_allow_shrink;
};
