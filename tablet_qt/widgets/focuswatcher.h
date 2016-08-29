#pragma once
#include <QObject>

class QEvent;


class FocusWatcher : public QObject
{
    // http://stackoverflow.com/questions/17818059/what-is-the-signal-for-when-a-widget-loses-focus
    Q_OBJECT
public:
    explicit FocusWatcher(QObject* parent = nullptr);
    virtual bool eventFilter(QObject *obj, QEvent *event) override;
signals:
    void focusChanged(bool in);
};
