#pragma once
#include <QModelIndex>
#include <QPointer>
#include <QSharedPointer>
#include "openablewidget.h"

class DiagnosticCodeSet;
class DiagnosisSortFilterModel;
class FlatProxyModel;
class LabelWordWrapWide;

class QAbstractButton;
class QItemSelection;
class QItemSelectionModel;
class QLabel;
class QLineEdit;
class QListView;
class QModelIndex;
class QStandardItemModel;
class QTreeView;


class DiagnosticCodeSelector : public OpenableWidget
{
    Q_OBJECT
public:
    DiagnosticCodeSelector(const QString& stylesheet,
                           QSharedPointer<DiagnosticCodeSet> codeset,
                           QModelIndex selected = QModelIndex(),
                           QWidget* parent = nullptr);
signals:
    void codeChanged(const QString& code, const QString& description);
protected slots:
    void selectionChanged(const QItemSelection& selected,
                          const QItemSelection& deselected);
    void proxySelectionChanged(const QItemSelection& proxy_selected,
                               const QItemSelection& proxy_deselected);
    void searchTextEdited(const QString& text);
    void toggleSearch();
protected:
    void newSelection(const QModelIndex& index);
    QModelIndex sourceFromProxy(const QModelIndex& index);
    QModelIndex proxyFromSource(const QModelIndex& index);
    void setSearchAppearance();
protected:
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    QPointer<QTreeView> m_treeview;
    QPointer<QListView> m_flatview;
    QPointer<QLineEdit> m_lineedit;
    QPointer<QLabel> m_heading_tree;
    QPointer<QLabel> m_heading_search;
    QSharedPointer<QItemSelectionModel> m_selection_model;
    QSharedPointer<FlatProxyModel> m_flat_proxy_model;
    QSharedPointer<DiagnosisSortFilterModel> m_diag_filter_model;
    QSharedPointer<QItemSelectionModel> m_proxy_selection_model;
    bool m_searching;
};
