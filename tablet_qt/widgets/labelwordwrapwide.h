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

// #define LWWW_USE_RESIZE_FOR_HEIGHT  // bad, if you can avoid it using custom layouts

#define LWWW_USE_UNWRAPPED_CACHE  // seems OK on wombat
// #define LWWW_USE_QLABEL_CACHE  // not OK (wombat), even if cache cleared on every event
#define LWWW_USE_STYLE_CACHE  // seems OK on wombat

#include <QLabel>
#include <QMap>

#if defined(LWWW_USE_UNWRAPPED_CACHE) || defined(LWWW_USE_QLABEL_CACHE) || defined(LWWW_USE_STYLE_CACHE)
#define LWWW_USE_ANY_CACHE
#endif


class LabelWordWrapWide : public QLabel
{
    // Label that word-wraps its text, and prefers to be wide rather than tall.

    Q_OBJECT
public:
    explicit LabelWordWrapWide(const QString& text, QWidget* parent = nullptr);
    explicit LabelWordWrapWide(QWidget* parent = nullptr);
    void commonConstructor();

    virtual QSize sizeHint() const override;
    // ... "I would like to be very wide and not very tall."

    // - QLabel::heightForWidth() gives a sensible answer; no need to override.
    //   But sometimes helpful to see when it's being used:
    virtual bool hasHeightForWidth() const override;
    virtual int heightForWidth(int width) const override;

    // - QLabel::minimumSizeHint() gives a sensible answer (the size of the
    //   smallest individual word); no need to override.
    //   ... "I need to be big enough to contain my smallest word."
    //   ... EXCEPT that once resizeEvent() has used setFixedHeight(), it
    //       returns that as the minimum.
    //   ... and then it caches that.
    virtual QSize minimumSizeHint() const override;

    // - However, even with a size policy of Maximum/Fixed/hasHeightForWidth,
    //   the label's height does not increase as its width is decreased, unless
    //   you override resizeEvent().
#ifdef LWWW_USE_RESIZE_FOR_HEIGHT
    virtual void resizeEvent(QResizeEvent* event) override;
#endif

    // - resizeEvent() does the trick, but it isn't normally called when, for
    //   example, we set our text. So catch other events:
#ifdef LWWW_USE_ANY_CACHE
    bool event(QEvent* e) override;
#endif

public slots:
    void setText(const QString& text);

protected:
    int qlabelHeightForWidth(int width) const;
    QSize sizeOfTextWithoutWrap() const;
#ifdef LWWW_USE_RESIZE_FOR_HEIGHT
    void forceHeight();
#endif
    QSize extraSizeForCssOrLayout() const;

    // - Widgets shouldn't need to cache their size hints; that's done by layouts
    //   for them. See http://kdemonkey.blogspot.co.uk/2013/11/understanding-qwidget-layout-flow.html
    // - However, for performance... we'll cache some things.
    //   In particular, word-wrapping labels can get asked to calculate their
    //   width for a great many heights (sometimes repeatedly).
    // - Moreover, the application of stylesheets varies with time (so calls
    //   can be made prior to, and then after, application of
    //   stylesheets). So the caches must be cleared whenever things like that
    //   happen.
#ifdef LWWW_USE_ANY_CACHE
    void clearCache();
#endif

protected:
#ifdef LWWW_USE_UNWRAPPED_CACHE
    mutable QSize m_cached_unwrapped_text_size;
#endif
#ifdef LWWW_USE_STYLE_CACHE
    mutable QSize m_cached_extra_for_css_or_layout;
#endif
#ifdef LWWW_USE_QLABEL_CACHE
    mutable QMap<int, int> m_cached_qlabel_height_for_width;
#endif
};
