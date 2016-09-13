#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "diagnosis/diagnosticcodeset.h"
#include "openablewidget.h"

class DiagnosisProxyModel;
class LabelWordWrapWide;
class QAbstractButton;
class QItemSelection;
class QItemSelectionModel;
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
    void searchTextEdited(const QString& text);
    void search();
protected:
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    QPointer<QTreeView> m_treeview;
    QSharedPointer<QItemSelectionModel> m_selection_model;
    QSharedPointer<DiagnosticCodeFilter> m_proxy_model;
};
