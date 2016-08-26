#pragma once
#include <QMap>
#include <QSlider>
#include <QStyle>

class QKeyEvent;
class QMouseEvent;

// Tick marks vanish on a styled QSlider. So:
// http://stackoverflow.com/questions/27531542/tick-marks-disappear-on-styled-qslider
// ... and then modification including labels, and making it work with
// vertical sliders.


class TickSlider : public QSlider
{
    Q_OBJECT
public:
    TickSlider(QWidget *parent = nullptr);
    TickSlider(Qt::Orientation orientation, QWidget *parent = nullptr);
    virtual void setTickColor(const QColor& colour);
    virtual void setTickThickness(int thickness);
    virtual void setTickLength(int length);
    virtual void setTickLabelGap(int gap);
    virtual void setInterlabelGap(int gap);
    virtual void setGapToSlider(int gap);

    virtual void setReadOnly(bool read_only);
    virtual bool readOnly() const;

    virtual void paintEvent(QPaintEvent *ev) override;
    virtual QSize sizeHint() const override;

    virtual void setTickLabelPosition(QSlider::TickPosition position);
    virtual QSlider::TickPosition tickLabelPosition() const;

    virtual void addTickLabel(int position, const QString& text);
    virtual void setTickLabels(const QMap<int, QString>& labels);
    virtual void addDefaultTickLabels();

    virtual void setReverseHorizontalLabels(bool reverse);
    virtual void setReverseVerticalLabels(bool reverse);

    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseDoubleClickEvent(QMouseEvent *event) override;
    virtual void mouseReleaseEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
    virtual void keyPressEvent(QKeyEvent* event) override;
    virtual void keyReleaseEvent(QKeyEvent* event) override;


protected:
    void commonConstructor();
    QSize biggestLabel() const;
    QStyle::SubControls getHoverControl() const;

protected:
    bool m_read_only;
    QColor m_tick_colour;
    int m_tick_thickness;
    int m_tick_length;
    int m_tick_label_gap;
    int m_min_interlabel_gap;
    int m_gap_to_slider;
    bool m_reverse_horizontal_labels;
    bool m_reverse_vertical_labels;
    TickPosition m_label_position;
    QMap<int, QString> m_tick_labels;
};
