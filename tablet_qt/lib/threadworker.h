#pragma once
#include <functional>
#include <QObject>


class ThreadWorker : public QObject
{
    // Helper object for
    // Encapsulates the call to the expensive function.
    // The controller sets the ThreadWorker up in a separate thread.

    Q_OBJECT

public:
    using PlainWorkerFunction = std::function<void()>;

    ThreadWorker(PlainWorkerFunction func);

public slots:
    void work();

signals:
    void workComplete();

protected:
    PlainWorkerFunction m_plainfunc;
};
