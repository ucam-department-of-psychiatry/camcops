#include "tasks/phq9.h"
#include "common/camcops_app.h"


void InitTasks(TaskFactory& factory)
{
    // Change these lines to determine which tasks are available:

    InitializePhq9(factory);
}
