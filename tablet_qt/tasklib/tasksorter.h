#pragma once
#include "task.h"


class TaskSorter
{
public:
    TaskSorter();
    bool operator()(const TaskPtr& left, const TaskPtr& right) const;
};
