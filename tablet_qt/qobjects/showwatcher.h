#pragma once
#include <QObject>


class ShowWatcher : public QObject
{
    // Object to watch for a showEvent() on a widget.
    // If you ARE a QWidget, you can overload QWidget::showEvent() instead.
    // If you OWN a QWidget, you can use this.
    // The ShowWatcher is OWNED BY and WATCHES the same thing.
    Q_OBJECT
public:
    explicit ShowWatcher(QObject* parent = nullptr,
                         bool debug_layout = false);
    virtual bool eventFilter(QObject* obj, QEvent* event) override;
signals:
    void showing();
protected:
    bool m_debug_layout;
};
