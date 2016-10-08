#pragma once
#include <QObject>

class QEvent;


class FocusWatcher : public QObject
{
    // Object to watch for change of focus on another widget.
    // - If you ARE a widget, you can overload QWidget::focusOutEvent().
    // - If you OWN a widget, use this. (You can't connect to the widget's
    //   QWidget::focusOutEvent(), because that's protected.)

    // http://stackoverflow.com/questions/17818059/what-is-the-signal-for-when-a-widget-loses-focus
    Q_OBJECT
public:
    explicit FocusWatcher(QObject* parent = nullptr);
    virtual bool eventFilter(QObject *obj, QEvent *event) override;
signals:
    void focusChanged(bool in);
};
