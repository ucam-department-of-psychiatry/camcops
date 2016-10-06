#include "threadworker.h"


ThreadWorker::ThreadWorker(PlainWorkerFunction func) :
    m_plainfunc(func)
{
}


void ThreadWorker::work()
{
    m_plainfunc();  // the expensive operation
    emit workComplete();
}
