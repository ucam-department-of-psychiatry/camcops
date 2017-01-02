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
#include <QLayout>
#include <QHash>
#include <QVector>
// #include <limits.h>


class BoxLayoutHfwItem;
class QQLayoutStruct;

class BoxLayoutHfw : public QLayout
{
    // Modification of QBoxLayout (and its simple children QVBoxLayout and
    // QHBoxLayout) to support height-for-width properly.
    //
    // Other notable modifications:
    // - the "private" (PIMPL) method is removed
    //
    // HOWEVER: UPSHOT: I HAVE FAILED TO GET THIS TO WORK.
    // The main problem is that layout attributes like minimumSize() are used
    // by owning widgets to set layout size, and they do not adequately convey
    // simultaneously "I'm happy to be only 20 pixels high if I can be 100
    // wide" and "if I'm 20 pixels wide, I must be at least 100 pixels high",
    // i.e. a dynamic minimum height.
    // It is possible, though? Some things suggest yes:
    // - http://stackoverflow.com/questions/24264320/qt-layouts-keep-widget-aspect-ratio-while-resizing
    // - ? Google for "public qlayout" heightforwidth
    // - http://qt.shoutwiki.com/wiki/How_to_create_flexible_Portrait_-_Landscape_rotation_layout_in_Qt


    Q_OBJECT
public:
    enum Direction { LeftToRight, RightToLeft, TopToBottom, BottomToTop,
                     Down = TopToBottom, Up = BottomToTop };
    struct Margins {  // RNC
        Margins() : m_set(false), m_left(0), m_top(0), m_right(0), m_bottom(0) {}
        Margins(int left, int top, int right, int bottom) {
            set(left, top, right, bottom);
        }
        void set(int left, int top, int right, int bottom) {
            m_left = left;
            m_top = top;
            m_right = right;
            m_bottom = bottom;
            m_set = true;
        }
        bool isSet() const { return m_set; }
        QSize extra() const { return QSize(m_left + m_right, m_top + m_bottom); }
        int removeLeftRightMargins(int w) { return w - (m_left + m_right); }
        bool m_set;
        int m_left;
        int m_top;
        int m_right;
        int m_bottom;
    };
    struct HfwInfo {  // RNC
        int m_hfw_height;
        int m_hfw_min_height;
        int hfw(const Margins& margins) { return m_hfw_height + margins.m_top + margins.m_bottom; }
        int minhfw(const Margins& margins) { return m_hfw_min_height + margins.m_top + margins.m_bottom; }
    };
    struct GeomInfo {  // RNC
        QVector<QQLayoutStruct> m_geom_array;  // set by setupGeom(), read by getHfwInfo() and setGeometry()
        QSize m_size_hint;  // returned by sizeHint(), calculated by setupGeom()
        QSize m_min_size;  // returned by minimumSize(), calculated by setupGeom()
        QSize m_max_size;  // returned by maximumSize(), calculated by setupGeom()
        int m_left_margin, m_top_margin, m_right_margin, m_bottom_margin;  // set by setupGeom(), read by effectiveMargins()
        Qt::Orientations m_expanding;  // returned by expandingDirections(), calculated by setupGeom()
        bool m_has_hfw;  // returned by hasHeightForWidth(), calculated by setupGeom()
    };

public:
    explicit BoxLayoutHfw(Direction, QWidget *parent = Q_NULLPTR);

    ~BoxLayoutHfw();

    Direction direction() const;
    void setDirection(Direction);

    void addSpacing(int size);
    void addStretch(int stretch = 0);
    void addSpacerItem(QSpacerItem* spacerItem);
    void addWidget(QWidget* widget, int stretch = 0,
                   Qt::Alignment alignment = Qt::Alignment());
    void addLayout(QLayout* layout, int stretch = 0);
    void addStrut(int size);
    void addItem(QLayoutItem* item) override;

    void insertSpacing(int index, int size);
    void insertStretch(int index, int stretch = 0);
    void insertSpacerItem(int index, QSpacerItem* spacer_item);
    void insertWidget(int index, QWidget* widget, int stretch = 0,
                      Qt::Alignment alignment = Qt::Alignment());
    void insertLayout(int index, QLayout* layout, int stretch = 0);
    void insertItem(int index, QLayoutItem* item);

    int spacing() const;
    void setSpacing(int spacing);

    bool setStretchFactor(QWidget* w, int stretch);
    bool setStretchFactor(QLayout* l, int stretch);
    void setStretch(int index, int stretch);
    int stretch(int index) const;

    QSize sizeHint() const override;
    QSize minimumSize() const override;
    QSize maximumSize() const override;

    bool hasHeightForWidth() const override;
    int heightForWidth(int width) const override;
    int minimumHeightForWidth(int width) const override;

    Qt::Orientations expandingDirections() const override;
    void invalidate() override;
    QLayoutItem *itemAt(int index) const override;
    QLayoutItem *takeAt(int index) override;
    int count() const override;
    void setGeometry(const QRect& rect) override;

private:
    // Disable copy-constructor and copy-assignment-operator:
    BoxLayoutHfw(BoxLayoutHfw const&) = delete;
    void operator=(BoxLayoutHfw const& x) = delete;

protected:
    void setDirty();
    void deleteAll();
    GeomInfo getGeomInfo(const QRect& layout_rect = QRect()) const;
    HfwInfo getHfwInfo(int layout_width) const;
    Margins effectiveMargins(const Margins& contents_margins) const;
    QLayoutItem* replaceAt(int index, QLayoutItem* item);
    // bool updateParentGeometry() const;  // RNC
    void partialInvalidate();  // RNC
    void fullInvalidate();  // RNC
    QRect getContentsRect(const QRect& layout_rect) const;  // RNC
    QVector<QRect> getChildRects(const QRect& contents_rect,
                                 const QVector<QQLayoutStruct>& a) const;  // RNC
    Direction getVisualDir() const;  // RNC
    QRect getCurrentMostLikelyRect() const;  // RNC
    void clearCaches();  // RNC
    const Margins& getContentsMarginsAndCache() const;
    const Margins& getEffectiveMargins() const;

protected:
    QList<BoxLayoutHfwItem*> m_list;
    Direction m_dir;
    int m_spacing;

    mutable QHash<int, HfwInfo> m_hfw_cache;  // RNC; the int is width
    mutable QHash<QRect, GeomInfo> m_geom_cache;  // RNC
    mutable Margins m_contents_margins;  // RNC
    mutable Margins m_effective_margins;  // RNC
    bool m_invalidate_due_to_self;  // RNC

    // mutable bool m_dirty;  // set by invalidate(), cleared by setupGeom(), used by lots to prevent unnecessary calls to setupGeom()
    // mutable int m_cached_layout_width;  // set by setupGeom()
    // mutable int m_cached_layout_height;  // set by setupGeom()

    // mutable int m_hfw_width;  // cached value used by heightForWidth() to prevent unnecessary recalculation
    // mutable int m_hfw_height;  // returned by heightForWidth(), calculated by calcHfw()
    // mutable int m_hfw_min_height;  // returned by minimumHeightForWidth(), calculated by calcHfw()

    // ------------------------------------------------------------------------
    // Selected bits from QLayoutPrivate:
    // ------------------------------------------------------------------------
protected:
    bool checkWidget(QWidget* widget) const;
    bool checkLayout(QLayout* other_layout) const;
    static QWidgetItem* createWidgetItem(const QLayout* layout, QWidget* widget);
    static QSpacerItem* createSpacerItem(const QLayout* layout, int w, int h,
                                         QSizePolicy::Policy h_policy = QSizePolicy::Minimum,
                                         QSizePolicy::Policy v_policy = QSizePolicy::Minimum);
};
