/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
#include "db/blobfieldref.h"
#include "questionnairelib/quelement.h"

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

    // Construct with a blank canvas.
    QuCanvas(BlobFieldRefPtr fieldref,
             const QSize& size = QSize(100, 100),
             bool allow_shrink = true,  // see setAllowShrink()
             QImage::Format format = QImage::Format_RGB32,  // internal image format
             const QColor& background_colour = Qt::white);

    // Construct with an image canvas.
    QuCanvas(BlobFieldRefPtr fieldref,
             const QString& template_filename,
             const QSize& size = QSize(),  // = take template's size
             bool allow_shrink = true);  // see setAllowShrink()

    // Adjust for the current DPI settings?
    QuCanvas* setAdjustForDpi(bool adjust_for_dpi);  // default is true
    // ... adjustment for DPI is a little more complex, because we have the
    //     back-end (database) image that should be independent of device
    //     resolution; therefore, we work with that, and allow the CanvasWidget
    //     to do the translation.

    // Sets the canvas background colour.
    QuCanvas* setBackgroundColour(const QColor& colour);

    // Sets the width of the border around the canvas.
    QuCanvas* setBorderWidth(int width);

    // Sets the colour of the border around the canvas.
    QuCanvas* setBorderColour(const QColor& colour);

    // If the widget is bigger than the canvas, what colour should we paint the
    // unused space?
    QuCanvas* setUnusedSpaceColour(const QColor& colour);

    // Set the colour of the user's "pen".
    QuCanvas* setPenColour(const QColor& colour);

    // Set the width of the user's "pen".
    QuCanvas* setPenWidth(int width);

    // Allow the canvas to be shrunk smaller than its standard size?
    // (May be helpful for large images on small screens.)
    // Default is true; see constructor.
    QuCanvas* setAllowShrink(bool allow_shrink);

protected:
    void commonConstructor();

    // Sets the widget state from our fieldref.
    void setFromField();

    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    virtual void closing() override;

    // Reset our widget.
    void resetWidget();

protected slots:
    // "Fieldref reports that the field's data has changed."
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator);

    // "Canvas widget reports that its image has changed (e.g. user has
    // drawn)."
    void imageChanged();

    // Called by imageChanged(), but after a short delay. Writes to fieldref.
    void completePendingFieldWrite();

    // Resets the canvas widget state and sets the fieldref value to NULL.
    void resetFieldToNull();

protected:
    BlobFieldRefPtr m_fieldref;
    QSize m_size;
    bool m_allow_shrink;
    QImage::Format m_format;
    bool m_adjust_display_for_dpi;
    QColor m_background_colour;
    int m_border_width_px;
    QColor m_border_colour;
    QColor m_unused_space_colour;
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
