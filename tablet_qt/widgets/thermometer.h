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

#include <QString>
#include <QStringList>
#include <QVector>
#include <QWidget>


class Thermometer : public QWidget
{
    // Represents clickable images/text in a vertical stack:
    //
    //      image0      text0
    //      image1      text1
    //      image2      text2
    //
    // and has two images (active + inactive) for each slot.
    // (It also applies a "being touched" colour.)
    //
    // - Scales up to the maximum size of the images/text.
    // - Aspect ratio of images is preserved.
    //
    // - No use yet for adding images on the fly.
    // - Fonts currently via stylesheets.
    // - No current support for gaps between images (generally the point is no gap).

    Q_OBJECT
public:

    // Constructor.
    explicit Thermometer(
            const QVector<QPixmap>& active_images,  // top to bottom
            const QVector<QPixmap>& inactive_images,  // top to bottom
            const QStringList* left_strings = nullptr,  // top to bottom
            const QStringList* right_strings = nullptr,  // top to bottom
            int left_string_scale = 1,  // arbitrary int representing "left text column" proportion
            int image_scale = 1,  // arbitrary int representing "image column" proportion
            int right_string_scale = 1,  // arbitrary int representing "right text column" proportion
            bool allow_deselection = true,  // allow images to be re-clicked to deselect them?
            bool read_only = false,  // read-only mode?
            bool rescale = false,  // rescale from images' intrinsic size?
            double rescale_factor = 1.0,  // if rescale: scale factor
            int text_gap_px = 4,  // gap between images and adjacent text
            QWidget* parent = nullptr);

    // Set the selected image (negative means "none selected") and update
    // the display accordingly.
    void setSelectedIndex(int selected_index);

    // Standard Qt widget overrides.
    virtual bool hasHeightForWidth() const override;
    virtual int heightForWidth(int width) const override;
    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;

signals:

    // "The user has changed the selection."
    void selectionIndexChanged(int index);

protected:

    // Describes a generic row of the "stack". All rows are column-aligned.
    struct DisplayInfo {
        bool scaling;  // image being scaled?
        double scale_factor;  // if scaling: image scale factor
        int row_left;  // x pos of the left of the whole row
        int lstring_width;  // width of the left string
        int image_width;  // width of the image
        int rstring_width;  // width of the right string
        int lstring_left;  // x pos of the left of the left string
        int image_left;  // x pos of the left of the image
        int lstring_right;  // x pos of the right of the left string
        int rstring_left;  // x pos of the left of the right string
        int rstring_right;  // x pos of the right of the right string
        int row_right;  // x pos of the right of the whole row
        int row_width;  // width of the whole row
    };

protected:

    // Standard Qt widget overrides.
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseReleaseEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
    virtual void paintEvent(QPaintEvent* event) override;

    // Update the display to indicate which image is being *touched*. The user
    // can touch lots (e.g. moving finger up/down on the stack) but until they
    // release their finger, the selection won't change. This handles the
    // finger-moving stuff.
    void setTouchedIndex(int touched_index);

    // Returns the rectangle for a given row, in its entirety.
    QRect rowRect(int row) const;

    // Returns the image rectangle for a given row.
    QRect imageRect(int row) const;

    // Fetches the top (y pos) and height of a given row.
    void getRowTopHeight(int row, int& top, int& height) const;

    // Returns a DisplayInfo object describing the layout of any row.
    DisplayInfo getDisplayInfo() const;

    // Returns the row number containing the screen coordinates specified, or
    // -1 if none do.
    int rowForPoint(const QPoint& pt) const;

protected:
    QVector<QPixmap> m_active_images;  // all active (selected) images, top to bottom
    QVector<QPixmap> m_inactive_images;  // all inactive (unselected) images, top to bottom
    int m_n_rows;  // number of rows (each with image + text)
    bool m_use_left_strings;  // show text on the left of the images?
    bool m_use_right_strings;  // show text on the right of the images?
    QStringList m_left_strings;  // list of "left" strings
    QStringList m_right_strings;  // list of "right" strings
    int m_left_string_scale;  // relative width of "left text" column
    int m_image_scale;  // relative width of "image" column
    int m_right_string_scale;  // relative width of "right text" column
    bool m_allow_deselection;  // allow returning to "none selected" state?
    bool m_read_only;  // read-only mode?
    bool m_rescale;  // rescale images?
    double m_rescale_factor;  // if rescale: by what factor?
    int m_text_gap_px;  // gap between images and adjacent text

    int m_selected_index;  // -1 for none selected, or zero-based index of selected row
    int m_touching_index;  // similarly, for row being touched now
    int m_start_touch_index;  // row in which the current touch began
    QVector<int> m_image_heights;  // heights of all images (top to bottom)
    int m_image_width;  // should be the same for all images
    QSize m_unscaled_total_size;  // total size before any image scaling
    int m_unscaled_lstring_width;  // width of "left string" column, before any image scaling
    int m_unscaled_rstring_width;  // width of "right string" column, before any image scaling
    QSize m_target_total_size;  // final target size
    double m_total_aspect_ratio;  // width / height
    QVector<QPixmap> m_active_touched_images;  // "selected and being touched" images
    QVector<QPixmap> m_inactive_touched_images;  // "unselected and being touched" images
};
