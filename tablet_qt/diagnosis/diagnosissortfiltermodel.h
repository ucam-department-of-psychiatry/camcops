#pragma once
#include <QSortFilterProxyModel>


class DiagnosisSortFilterModel : public QSortFilterProxyModel
{
    Q_OBJECT
public:
    using QSortFilterProxyModel::QSortFilterProxyModel;

    virtual bool filterAcceptsRow(int row,
                                  const QModelIndex& parent) const override;
};
