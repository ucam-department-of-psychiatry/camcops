#include "tasksorter.h"


TaskSorter::TaskSorter()
{
    // could use this to implement specific sorting methods; see
    // https://forum.qt.io/topic/4877/sorting-a-qlist-with-a-comparator/4
}


bool TaskSorter::operator()(const TaskPtr& left, const TaskPtr& right) const
{
    // Implements: LEFT < RIGHT ?
    // Sort by date/time (descending), then taskname (ascending)
    QDateTime l_when = left->valueDateTime(
        DbConst::CREATION_TIMESTAMP_FIELDNAME);
    QDateTime r_when = right->valueDateTime(
        DbConst::CREATION_TIMESTAMP_FIELDNAME);
    if (l_when != r_when) {
        return l_when > r_when;  // descending
    } else {
        QString l_name = left->shortname();
        QString r_name = right->shortname();
        return l_name < r_name; // ascending
    }
}
