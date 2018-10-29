/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_PAINTING
// #define DEBUG_VERY_VERBOSE
// #define DEBUG_FULL_REPAINT
// #define DEBUG_INTERACTION

#include "thermometer.h"
#include <QDebug>
#include <QPainter>
#include <QPaintEvent>
#include <QRegion>
#include "graphics/graphicsfunc.h"
#include "lib/sizehelpers.h"
#include "lib/uifunc.h"

const int UNSELECTED = -1;


Thermometer::Thermometer(const QVector<QPixmap>& active_images,
                         const QVector<QPixmap>& inactive_images,
                         const QStringList* left_strings,
                         const QStringList* right_strings,
                         int left_string_scale,
                         int image_scale,
                         int right_string_scale,
                         bool allow_deselection,
                         bool read_only,
                         bool rescale,
                         double rescale_factor,
                         int text_gap_px,
                         QWidget* parent) :
    QWidget(parent),
    m_active_images(active_images),
    m_inactive_images(inactive_images),
    m_left_string_scale(left_string_scale),
    m_image_scale(image_scale),
    m_right_string_scale(right_string_scale),
    m_allow_deselection(allow_deselection),
    m_read_only(read_only),
    m_rescale(rescale),
    m_rescale_factor(rescale_factor),
    m_text_gap_px(text_gap_px),
    m_selected_index(UNSELECTED),
    m_touching_index(UNSELECTED),
    m_start_touch_index(UNSELECTED)
{
    // Set basic parameters.
    m_n_rows = m_active_images.length();
    if (m_n_rows == 0) {
        uifunc::stopApp("No rows to Thermometer");
    }
    if (m_inactive_images.length() != m_n_rows) {
        uifunc::stopApp("Wrong inactive_images length to Thermometer");
    }
    m_use_left_strings = left_strings != nullptr;
    if (left_strings) {
        m_left_strings = *left_strings;
        if (m_left_strings.length() != m_n_rows) {
            uifunc::stopApp("Wrong left_strings length to Thermometer");
        }
        if (m_left_string_scale <= 0) {
            uifunc::stopApp("Thermometer: left_string_scale <= 0 "
                            "but there are left strings");
        }
    }
    m_use_right_strings = right_strings != nullptr;
    if (right_strings) {
        m_right_strings = *right_strings;
        if (m_right_strings.length() != m_n_rows) {
            uifunc::stopApp("Wrong right_strings length to Thermometer");
        }
        if (m_right_string_scale <= 0) {
            uifunc::stopApp("Thermometer: right_string_scale <= 0 "
                            "but there are right strings");
        }
    }
    if (m_image_scale <= 0) {
        uifunc::stopApp("Image scale values to Thermometer must be >0");
    }
    if (m_left_string_scale < 0 ||
            m_right_string_scale < 0) {
        uifunc::stopApp("Negative string scale values to Thermometer");
    }

    // Fetch image heights etc.
    m_image_width = m_active_images.at(0).width();
    m_unscaled_total_size.rheight() = 0;
    const double total_scale =
            m_left_string_scale + m_image_scale + m_right_string_scale;
    m_unscaled_total_size.rwidth() = static_cast<int>(
            m_image_width * total_scale / static_cast<double>(m_image_scale));
    m_unscaled_lstring_width = static_cast<int>(
                static_cast<double>(m_left_string_scale) *
                static_cast<double>(m_unscaled_total_size.width()) /
                total_scale);
    m_unscaled_rstring_width = static_cast<int>(
                static_cast<double>(m_left_string_scale) *
                static_cast<double>(m_unscaled_total_size.width()) /
                total_scale);

    const bool pressed_marker_behind = false;  // colour on top
    for (int i = 0; i < m_n_rows; ++i) {
        const QPixmap& active_image = m_active_images.at(i);
        const QPixmap& inactive_image = m_inactive_images.at(i);
        const int active_image_height = active_image.height();
        m_image_heights.append(active_image_height);
        m_unscaled_total_size.rheight() += active_image_height;
        if (inactive_image.height() != active_image_height) {
               qWarning()
                    << Q_FUNC_INFO
                    << "image at index" << i
                    << "has active image height" << active_image_height
                    << "but inactive image height" << inactive_image.height()
                    << "- may look strange!";
        }
        if (active_image.width() != m_image_width) {
            qWarning()
                    << Q_FUNC_INFO
                    << "active image" << i
                    << "has discrepant width of" << active_image.width()
                    << "versus initial one of" << m_image_width;
        }
        if (inactive_image.width() != m_image_width) {
            qWarning()
                    << Q_FUNC_INFO
                    << "inactive image" << i
                    << "has discrepant width of" << inactive_image.width()
                    << "versus initial one of" << m_image_width;
        }
        m_active_touched_images.append(
            uifunc::addPressedBackground(active_image, pressed_marker_behind));
        m_inactive_touched_images.append(
            uifunc::addPressedBackground(inactive_image, pressed_marker_behind));
    }
    if (m_rescale) {
        m_target_total_size = QSize(
            static_cast<int>(m_rescale_factor *
                             static_cast<double>(m_unscaled_total_size.width())),
            static_cast<int>(m_rescale_factor *
                             static_cast<double>(m_unscaled_total_size.height()))
        );
    } else {
        m_target_total_size = m_unscaled_total_size;
    }
    m_total_aspect_ratio =
            static_cast<double>(m_unscaled_total_size.width()) /
            static_cast<double>(m_unscaled_total_size.height());

    // Set Qt size policy
    // setSizePolicy(sizehelpers::maximumFixedHFWPolicy());
    setSizePolicy(sizehelpers::maximumMaximumHFWPolicy());
}


void Thermometer::setSelectedIndex(int selected_index)
{
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO << selected_index;
#endif
    const int old_selected_index = m_selected_index;
    if (selected_index < 0) {
        m_selected_index = UNSELECTED;
    } else if (selected_index < m_n_rows) {
        m_selected_index = selected_index;
    } else {
        qWarning()
                 << Q_FUNC_INFO
                << "Bad index:" << selected_index
                << "but number of rows is" << m_n_rows;
        m_selected_index = UNSELECTED;
    }
    if (m_selected_index == old_selected_index) {
        // Nothing to do
#ifdef DEBUG_INTERACTION
        qDebug()
            << Q_FUNC_INFO
            << "Nothing to do; m_selected_index unchanged at"
            << m_selected_index;
#endif
        return;
    }

    // Tell clients
    emit selectionIndexChanged(m_selected_index);

    // Trigger refresh
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO
             << "repainting for m_selected_index" << m_selected_index;
#endif
#ifdef DEBUG_FULL_REPAINT
    repaint();
#else
    QRegion redraw_region;
    if (old_selected_index != UNSELECTED) {
        redraw_region += imageRect(old_selected_index);
    }
    if (m_selected_index != UNSELECTED) {
        redraw_region += imageRect(m_selected_index);
    }
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << "redraw_region" << redraw_region;
#endif
    if (!redraw_region.isEmpty()) {
        repaint(redraw_region);
    }
#endif
}


void Thermometer::setTouchedIndex(int touched_index)
{
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO << touched_index;
#endif
    const int old_touching_index = m_touching_index;
    if (touched_index < 0) {
        m_touching_index = UNSELECTED;
    } else if (touched_index < m_n_rows) {
        m_touching_index = touched_index;
    } else {
        qWarning()
                 << Q_FUNC_INFO
                << "Bad index:" << touched_index
                << "but number of rows is" << m_n_rows;
        m_touching_index = UNSELECTED;
    }
    if (m_touching_index == old_touching_index) {
        // Nothing to do
#ifdef DEBUG_INTERACTION
        qDebug()
            << Q_FUNC_INFO
            << "Nothing to do; m_touching_index unchanged at"
            << m_touching_index;
#endif
        return;
    }

    // Trigger refresh
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO
             << "repainting for m_touching_index" << m_touching_index;
#endif
#ifdef DEBUG_FULL_REPAINT
    repaint();
#else
    QRegion redraw_region;
    if (old_touching_index != UNSELECTED) {
        redraw_region += imageRect(old_touching_index);
    }
    if (m_touching_index != UNSELECTED) {
        redraw_region += imageRect(m_touching_index);
    }
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << "redraw_region" << redraw_region;
#endif
    if (!redraw_region.isEmpty()) {
        repaint(redraw_region);
    }
#endif
}


bool Thermometer::hasHeightForWidth() const
{
    return true;
}


int Thermometer::heightForWidth(const int width) const
{
    // We work this based on aspect ratio, which is width/height.
    const int hfw = static_cast<int>(
        static_cast<double>(width) / m_total_aspect_ratio
    );
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO << "width" << width << "-> hfw" << hfw;
#endif
    return hfw;
}


QSize Thermometer::sizeHint() const
{
    return m_target_total_size;
}


QSize Thermometer::minimumSizeHint() const
{
    return QSize(0, 0);
}


Thermometer::DisplayInfo Thermometer::getDisplayInfo() const
{
    DisplayInfo d;
    const QRect cr = contentsRect();
    d.scaling = cr.size() != m_unscaled_total_size;
    d.scale_factor = d.scaling
            ? (static_cast<double>(cr.width()) /
               static_cast<double>(m_unscaled_total_size.width()))
            : 1.0;
    d.lstring_width = d.scaling
            ? static_cast<int>(
                  static_cast<double>(m_unscaled_lstring_width) *
                  d.scale_factor)
            : m_unscaled_lstring_width;
    d.image_width = d.scaling
            ? static_cast<int>(
                  static_cast<double>(m_image_width) *
                  d.scale_factor)
            : m_image_width;
    d.rstring_width = d.scaling
            ? static_cast<int>(
                  static_cast<double>(m_unscaled_rstring_width) *
                  d.scale_factor)
            : m_unscaled_rstring_width;

    // Iterate through rows
    d.lstring_left = cr.left();
    d.image_left = d.lstring_left + d.lstring_width;
    d.lstring_right = d.image_left - m_text_gap_px;
    d.rstring_left = d.image_left + d.image_width + m_text_gap_px;
    d.rstring_right = d.image_left + d.image_width + d.rstring_width;

    d.row_left = d.lstring_left;
    d.row_right = d.rstring_right;
    d.row_width = d.rstring_right - d.lstring_left;

    return d;
}


void Thermometer::getRowTopHeight(int row, int& top, int& height) const
{
    if (row == UNSELECTED || row >= m_n_rows) {
        qWarning() << Q_FUNC_INFO << "Bad row parameter";
        return;
    }
    DisplayInfo d = getDisplayInfo();
    const QRect cr = contentsRect();
    int t = cr.top();
    for (int r = 0; r < m_n_rows; ++r) {
        const int row_height = d.scaling
                ? static_cast<int>(
                      static_cast<double>(m_image_heights.at(r)) *
                      d.scale_factor)
                : m_image_heights.at(r);
        if (r == row) {
            // Write back results
            top = t;
            height = row_height;
            return;
        }
        // Ready for next row:
        t += row_height;
    }
    qWarning() << Q_FUNC_INFO << "Should not get here!";
}


QRect Thermometer::rowRect(int row) const
{
    if (row == UNSELECTED || row >= m_n_rows) {
        qWarning() << Q_FUNC_INFO << "Bad row parameter";
        return QRect();
    }
    DisplayInfo d = getDisplayInfo();
    int row_top;
    int row_height;
    getRowTopHeight(row, row_top, row_height);
    return QRect(d.row_left, row_top, d.row_width, row_height);
}


QRect Thermometer::imageRect(int row) const
{
    if (row == UNSELECTED || row >= m_n_rows) {
        qWarning() << Q_FUNC_INFO << "Bad row parameter";
        return QRect();
    }
    DisplayInfo d = getDisplayInfo();
    int row_top;
    int row_height;
    getRowTopHeight(row, row_top, row_height);
    return QRect(d.image_left, row_top, d.image_width, row_height);
}


void Thermometer::paintEvent(QPaintEvent* event)
{
#ifdef DEBUG_PAINTING
    qDebug() << Q_FUNC_INFO;
#endif
    QPainter painter(this);
    DisplayInfo d = getDisplayInfo();
    const QRect cr = contentsRect();
    const QRegion redraw_region = event->region();
    const Qt::Alignment leftstring_align = Qt::AlignRight | Qt::AlignVCenter;
    const Qt::Alignment rightstring_align = Qt::AlignLeft | Qt::AlignVCenter;

#ifdef DEBUG_PAINTING
    qDebug()
        << Q_FUNC_INFO
        << "contentsRect()" << cr
        << "scaling" << d.scaling
        << "scale_factor" << d.scale_factor
        << "lstring_width" << d.lstring_width
        << "image_width" << d.image_width
        << "lstring_left" << d.lstring_left
        << "image_left" << d.image_left
        << "lstring_right" << d.lstring_right
        << "rstring_left" << d.rstring_left;
#endif

    int top = cr.top();
    for (int row = 0; row < m_n_rows; ++row) {
        const int row_height = d.scaling
                ? static_cast<int>(
                      static_cast<double>(m_image_heights.at(row)) *
                      d.scale_factor)
                : m_image_heights.at(row);
        // const int bottom = top + image_height;
        const int vertical_midpoint = top + row_height / 2;

#ifdef DEBUG_VERY_VERBOSE
        qDebug()
            << "row" << row
            << "image_height" << row_height
            << "vertical_midpoint" << vertical_midpoint;
#endif

        // Draw left string: vertically centred...
        if (m_use_left_strings) {
            const QRect leftstring_rect(d.lstring_left, top,
                                        d.lstring_width, row_height);
            if (redraw_region.contains(leftstring_rect)) {
                graphicsfunc::drawText(
                    painter,
                    QPoint(d.lstring_right, vertical_midpoint),
                    leftstring_align,
                    m_left_strings.at(row)
                    // bounding rectangle? Not sure. Probably OK without (text
                    // will overlap when scaled very small)
                );
            }
        }

        // Draw image
        const QSize displaysize(d.image_width, row_height);
        const QRect dest_imagerect(QPoint(d.image_left, top), displaysize);
        if (redraw_region.contains(dest_imagerect)) {
            const bool touching = m_touching_index == row;
            const bool selected = m_selected_index == row;
            const QPixmap& image = selected
                        ? (touching ? m_active_touched_images.at(row)
                                    : m_active_images.at(row))
                        : (touching ? m_inactive_touched_images.at(row)
                                    : m_inactive_images.at(row));
            if (d.scaling) {
                const QRect source_all_image(QPoint(0, 0), image.size());
                painter.drawPixmap(dest_imagerect, image, source_all_image);
            } else {
                painter.drawPixmap(d.image_left, top, image);
            }
        }

        // Draw right string
        if (m_use_right_strings) {
            const QRect rightstring_rect(d.rstring_left, top,
                                         d.rstring_width, row_height);
            if (redraw_region.contains(rightstring_rect)) {
                graphicsfunc::drawText(
                    painter,
                    QPoint(d.rstring_left, vertical_midpoint),
                    rightstring_align,
                    m_right_strings.at(row)
                    // bounding rectangle? Not sure. Probably OK without (text
                    // will overlap when scaled very small)
                );
            }
        }

        // Ready for next row:
        top += row_height;
    }
}


int Thermometer::rowForPoint(const QPoint& pt) const
{
    // Which row is this event in?
    for (int r = 0; r < m_n_rows; ++r) {
        const QRect row_rect = rowRect(r);
        if (row_rect.contains(pt)) {
            return r;
        }
    }
    return UNSELECTED;
}


void Thermometer::mousePressEvent(QMouseEvent* event)
{
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO << event;
#endif
    if (m_read_only) {
        return;
    }
    // Which row is this event in?
    int in_row = rowForPoint(event->pos());

    if (in_row != UNSELECTED) {
        // User has clicked in a row. Start of a new touch.
        setTouchedIndex(in_row);
        m_start_touch_index = in_row;
    }
}


void Thermometer::mouseReleaseEvent(QMouseEvent* event)
{
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO << event;
#endif
    if (m_read_only) {
        return;
    }
    int in_row = rowForPoint(event->pos());
    // User has released mouse in a row.
    setTouchedIndex(UNSELECTED);
    // If it's the same row they started in, that's a selection toggle.
    if (in_row == m_start_touch_index) {
        const bool was_selected = m_selected_index == in_row;
#ifdef DEBUG_INTERACTION
        qDebug() << Q_FUNC_INFO
                 << "toggle selection; was_selected" << was_selected;
#endif
        setSelectedIndex(was_selected && m_allow_deselection
                         ? UNSELECTED
                         : in_row);
    }
}


void Thermometer::mouseMoveEvent(QMouseEvent* event)
{
#ifdef DEBUG_INTERACTION
    qDebug() << Q_FUNC_INFO << event;
#endif
    if (m_read_only) {
        return;
    }
    int in_row = rowForPoint(event->pos());
    // Moved. Still touching.
    // May or may not be in the row that they *started* touching.
    if (in_row == m_start_touch_index) {
        setTouchedIndex(in_row);
    } else {
        setTouchedIndex(UNSELECTED);
    }
}


// ignore QEvent::MouseButtonDblClick for now

