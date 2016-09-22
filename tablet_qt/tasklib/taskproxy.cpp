#include "taskproxy.h"
#include "taskfactory.h"


TaskProxy::TaskProxy(TaskFactory& factory)
{
    factory.registerTask(this);
}
