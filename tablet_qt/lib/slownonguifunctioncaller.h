#pragma once
#include <QThread>
#include "dialogs/waitbox.h"
#include "threadworker.h"


class SlowNonGuiFunctionCaller : public QObject
{
    // Executes a function in blocking fashion, but in a separate thread,
    // while displaying an infinite-wait (uncertain-wait) progress dialogue
    // from the calling thread.
    //
    // Must be created from the GUI thread.
    //
    // DO NOT PERFORM GUI OPERATIONS IN THE WORKER FUNCTION.

    Q_OBJECT
public:
    SlowNonGuiFunctionCaller(ThreadWorker::PlainWorkerFunction func,
                             QWidget* parent,
                             const QString& text = "Operation in progress...",
                             const QString& title = "Please wait...");
    ~SlowNonGuiFunctionCaller();
protected:
    QThread m_worker_thread;
    ThreadWorker* m_worker;
    WaitBox m_waitbox;
};
