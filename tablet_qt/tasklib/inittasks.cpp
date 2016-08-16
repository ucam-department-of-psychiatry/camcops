#include "tasklib/inittasks.h"

#include "tasks/demoquestionnaire.h"
#include "tasks/phq9.h"


void InitTasks(TaskFactory& factory)
{
    // Change these lines to determine which tasks are available:

    initializeDemoQuestionnaire(factory);
    initializePhq9(factory);
}
