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

#pragma once
#include <QImage>
#include "db/fieldref.h"
#include "quelement.h"

class CanvasWidget;
class QLabel;
class QTimer;
class Spacer;


class QuCanvas : public QuElement
{
    // Element controlling an image field, onto which the user can draw,
    // either from a blank canvas or from a starting image. Allows image reset.

    Q_OBJECT
public:
    QuCanvas(FieldRefPtr fieldref,
             const QSize& size = QSize(100, 100),
             bool allow_shrink = true,
             QImage::Format format = QImage::Format_RGB32,
             const QColor& background_colour = Qt::white);
    QuCanvas(FieldRefPtr fieldref,
             const QString& template_filename,
             const QSize& size = QSize(),  // = take template's size
             bool allow_shrink = true);
    QuCanvas* setPenColour(const QColor& pen_colour);
    QuCanvas* setPenWidth(int pen_width);
    QuCanvas* setAllowShrink(bool allow_shrink);
protected:
    void commonConstructor();
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void closing() override;
    void resetWidget();
protected slots:
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);
    void imageChanged();
    void completePendingFieldWrite();
    void resetFieldToNull();
protected:
    FieldRefPtr m_fieldref;
    QSize m_size;
    bool m_allow_shrink;
    QImage::Format m_format;
    QColor m_background_colour;
    QColor m_pen_colour;
    int m_pen_width;
    QString m_template_filename;
    bool m_using_template;

    QPointer<CanvasWidget> m_canvas;
    QPointer<QLabel> m_missing_indicator;
    QPointer<Spacer> m_no_missing_indicator;
    QSharedPointer<QTimer> m_timer;
    bool m_field_write_pending;
};
