#pragma once
#include <QScrollArea>
#include <QSize>


// http://forum.qt.io/topic/13374/solved-qscrollarea-vertical-scroll-only/4

class VerticalScrollArea : public QScrollArea
{
    // Contains objects in a vertical scroll area.

    Q_OBJECT
public:
    explicit VerticalScrollArea(QWidget* parent = nullptr);
    virtual bool eventFilter(QObject* o, QEvent* e);
    virtual QSize sizeHint() const override;
protected:
    bool m_updating_geometry;
};
