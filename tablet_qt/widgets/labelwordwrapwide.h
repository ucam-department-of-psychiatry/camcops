#pragma once
#include <QLabel>
#include <QMap>


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
    virtual void resizeEvent(QResizeEvent* event) override;

    // - resizeEvent() does the trick, but it isn't normally called when, for
    //   example, we set our text.

    bool event(QEvent* e) override;

public slots:
    void setText(const QString& text);

protected:
    QSize sizeOfTextWithoutWrap() const;
    void forceHeight();
    // Widgets shouldn't need to cache their size hints; that's done by layouts
    // for them. See http://kdemonkey.blogspot.co.uk/2013/11/understanding-qwidget-layout-flow.html
    // However, for performance...
    void clearCache();

protected:
    mutable QSize m_cached_unwrapped_text_size;
    mutable QSize m_cached_size_hint;
    mutable QSize m_cached_minimum_size_hint;
    mutable QMap<int, int> m_cached_height_for_width;
};
