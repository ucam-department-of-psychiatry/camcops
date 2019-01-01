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

    Q_OBJECT
public:
    explicit Thermometer(
            const QVector<QPixmap>& active_images,  // top to bottom
            const QVector<QPixmap>& inactive_images,  // top to bottom
            const QStringList* left_strings = nullptr,  // top to bottom
            const QStringList* right_strings = nullptr,  // top to bottom
            int left_string_scale = 1,  // arbitrary int representing proportion
            int image_scale = 1,  // arbitrary int representing proportion
            int right_string_scale = 1,  // arbitrary int representing proportion
            bool allow_deselection = true,
            bool read_only = false,
            bool rescale = false,
            double rescale_factor = 1.0,
            int text_gap_px = 4,  // gap between images and adjacent text
            QWidget* parent = nullptr);
    void setSelectedIndex(int selected_index);
    // - No use yet for adding images on the fly.
    // - Fonts currently via stylesheets.
    // - No current support for gaps between images (generally the point is no gap).

    virtual bool hasHeightForWidth() const override;
    virtual int heightForWidth(int width) const override;
    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;

signals:
    void selectionIndexChanged(int index);

protected:
    struct DisplayInfo {
        bool scaling;
        double scale_factor;
        int row_left;
        int lstring_width;
        int image_width;
        int rstring_width;
        int lstring_left;
        int image_left;
        int lstring_right;
        int rstring_left;
        int rstring_right;
        int row_right;
        int row_width;
    };

protected:
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseReleaseEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
    virtual void paintEvent(QPaintEvent* event) override;

    void setTouchedIndex(int touched_index);
    QRect rowRect(int row) const;
    QRect imageRect(int row) const;
    void getRowTopHeight(int row, int& top, int& height) const;
    DisplayInfo getDisplayInfo() const;
    int rowForPoint(const QPoint& pt) const;

protected:
    QVector<QPixmap> m_active_images;
    QVector<QPixmap> m_inactive_images;
    int m_n_rows;  // number of rows (each with image + text)
    bool m_use_left_strings;
    bool m_use_right_strings;
    QStringList m_left_strings;  // list of strings
    QStringList m_right_strings;  // list of strings
    int m_left_string_scale;
    int m_image_scale;
    int m_right_string_scale;
    bool m_allow_deselection;
    bool m_read_only;
    bool m_rescale;
    double m_rescale_factor;
    int m_text_gap_px;

    int m_selected_index;  // -1 for none selected, or zero-based index of selected row
    int m_touching_index;  // similarly
    int m_start_touch_index;
    QVector<int> m_image_heights;
    int m_image_width;  // should be the same for all images
    QSize m_unscaled_total_size;
    int m_unscaled_lstring_width;
    int m_unscaled_rstring_width;
    QSize m_target_total_size;
    double m_total_aspect_ratio;  // width / height
    QVector<QPixmap> m_active_touched_images;
    QVector<QPixmap> m_inactive_touched_images;
};
