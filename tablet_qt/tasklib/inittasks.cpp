#include "tasks/phq9.h"
#include "common/camcops_app.h"


void InitTasks(TaskFactory& factory)
{
    // Change these lines to determine which tasks are available:

    initializePhq9(factory);
}
