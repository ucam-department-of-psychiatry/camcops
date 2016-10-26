#pragma once
#include <functional>
#include <QMap>
#include <QObject>
class QDialog;


class KeyPressWatcher : public QObject
{
    Q_OBJECT
public:
    using CallbackFunction = std::function<void()>;
public:
    explicit KeyPressWatcher(QDialog* parent = nullptr);
    virtual bool eventFilter(QObject* obj, QEvent* event) override;
    void addKeyEvent(int key, const CallbackFunction& callback);
signals:
    void keypress(int key);
protected:
    QMap<int, CallbackFunction> m_map;
};
