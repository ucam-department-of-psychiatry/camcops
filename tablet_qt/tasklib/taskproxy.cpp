#include "taskproxy.h"
#include "tasklib/taskfactory.h"


TaskProxy::TaskProxy(TaskFactory& factory)
{
    factory.registerTask(this);
}
