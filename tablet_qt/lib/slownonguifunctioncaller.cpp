#include "slownonguifunctioncaller.h"
#include "widgets/waitbox.h"


SlowNonGuiFunctionCaller::SlowNonGuiFunctionCaller(ThreadWorker::PlainWorkerFunction func,
                               QWidget* parent,
                               const QString& text,
                               const QString& title) :
    m_worker_thread(),
    m_worker(new ThreadWorker(func)),
    m_waitbox(parent, text, title)
{
    m_worker->moveToThread(&m_worker_thread);
    connect(&m_worker_thread, &QThread::started, // 1
            m_worker, &ThreadWorker::work);  // 2
    connect(m_worker, &ThreadWorker::workComplete, // 3
            &m_waitbox, &WaitBox::accept);  // 4
    connect(&m_worker_thread, &QThread::finished,  // 5
            m_worker, &QObject::deleteLater);  // 6
    m_worker_thread.start();
    m_waitbox.exec();  // blocks until its accept()/reject() called (e.g. 4)
}


SlowNonGuiFunctionCaller::~SlowNonGuiFunctionCaller()
{
    m_worker_thread.quit();
    m_worker_thread.wait();
}
