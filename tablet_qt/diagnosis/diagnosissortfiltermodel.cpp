#include "diagnosissortfiltermodel.h"


bool DiagnosisSortFilterModel::filterAcceptsRow(
        int row,
        const QModelIndex& parent) const
{
    // Filter modification that accepts parents whose children meet the filter
    // criteria. (Note that calling setFilterFixedString correctly affects
    // filterRegExp(); see qsortfilterproxymodel.cpp).

    // http://doc.qt.io/qt-5/qsortfilterproxymodel.html#filterAcceptsRow
    // http://www.qtcentre.org/threads/46471-QTreeView-Filter

    QModelIndex index = sourceModel()->index(row, 0, parent);

    if (!index.isValid()) {
        return false;
    }

    // Remove rows that are not selectable.
    if (!(index.flags() & Qt::ItemIsSelectable)) {
        return false;
    }

    // Otherwise, if it matches our search criteria, we're good:
    if (index.data().toString().contains(filterRegExp())) {
        return true;
    }

    /*
    // For tree models, but not for flat models:

    // Permit if children are shown as well
    int nrows = sourceModel()->rowCount(index);
    for (int r = 0; r < nrows; ++r) {
        if (filterAcceptsRow(r, index)) {
            return true;
        }
    }
    */

    return false;
}
