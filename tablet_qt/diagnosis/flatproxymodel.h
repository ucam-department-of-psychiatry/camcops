#pragma once
#include <QMap>
#include <QAbstractProxyModel>


/*

This proxy model makes a flat model out of a tree, so we can use a QListView
for searching.

It also ensures we can't see/pick something marked as unselectable.

This is pretty basic; see

    http://stackoverflow.com/questions/21564976/how-to-create-a-proxy-model-that-would-flatten-nodes-of-a-qabstractitemmodel-int

but for more extensive things, Google also "FlatProxyModel"; there are others,
e.g.
    https://api.kde.org/bundled-apps-api/calligra-apidocs/plan/html/kptflatproxymodel_8h_source.html
    https://api.kde.org/bundled-apps-api/calligra-apidocs/plan/html/kptflatproxymodel_8cpp_source.html

However, also:

    http://www.qtcentre.org/threads/25884-Proxy-model-index-mapping

... you can't reimplement mapFromSource() and mapToSource() for
    QSortFilterProxyModel because it needs its own implementation; instead
    subclass QAbstractProxyModel to do the flattening, and either flatten
    something filtered or (in our case) filter something flattened.
*/

class FlatProxyModel : public QAbstractProxyModel
{
    Q_OBJECT

public:
    using QAbstractProxyModel::QAbstractProxyModel;

    virtual void setSourceModel(QAbstractItemModel* src_model) override;
    virtual QModelIndex mapFromSource(const QModelIndex& src_index) const override;
    virtual QModelIndex mapToSource(const QModelIndex& proxy_index) const override;
    virtual int columnCount(const QModelIndex& proxy_parent) const override;
    virtual int rowCount(const QModelIndex& proxy_parent) const override;
    virtual QModelIndex index(int proxy_row, int proxy_column,
                              const QModelIndex& proxy_parent) const override;
    virtual QModelIndex parent(const QModelIndex& proxy_child) const override;
    virtual bool hasChildren(const QModelIndex& proxy_parent) const override;

protected:
    int buildMap(QAbstractItemModel* src_model,
                 const QModelIndex& src_parent = QModelIndex(),
                 int proxy_row = 0);
protected slots:
    void sourceDataChanged(const QModelIndex& src_top_left,
                           const QModelIndex& src_bottom_right,
                           const QVector<int>& roles = QVector<int>());
protected:
    QMap<QModelIndex, int> m_row_from_src_index;
    QMap<int, QModelIndex> m_src_index_from_row;
};
