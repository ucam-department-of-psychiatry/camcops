#include "master_test.h"
#include <QString>
#include "common/camcops_app.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


void testTask(CamcopsApp& app, const QString& tablename)
{
    Task* p_task = app.m_p_task_factory->build(tablename);
    if (!p_task) {
        qDebug() << "Failed to create task: " << qPrintable(tablename);
        return;
    }
    qDebug() << *p_task;
}


void runTests(CamcopsApp& app)
{
    testTask(app, "phq9");
}
