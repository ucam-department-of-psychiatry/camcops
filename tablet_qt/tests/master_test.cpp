#include "master_test.h"
#include <QString>
#include "common/camcops_app.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


void test_task(CamcopsApp& app, const QString& tablename)
{
    Task* task = app.m_pTaskFactory->build(tablename);
    if (!task) {
        qDebug() << "Failed to create task: " << qPrintable(tablename);
        return;
    }
    qDebug() << *task;
}

void run_tests(CamcopsApp& app)
{
    test_task(app, "phq9");
}
