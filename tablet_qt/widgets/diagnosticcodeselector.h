#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "diagnosis/diagnosticcodeset.h"
#include "openablewidget.h"

class LabelWordWrapWide;
class QAbstractButton;
class QModelIndex;
class QStandardItemModel;
class QTreeView;
class QTreeWidgetItem;


class DiagnosticCodeSelector : public OpenableWidget
{
    Q_OBJECT
public:
    DiagnosticCodeSelector(const QString& stylesheet,
                           QSharedPointer<DiagnosticCodeSet> codeset,
                           int selected_index = DiagnosticCodeSet::INVALID,
                           QWidget* parent = nullptr);
signals:
    void codeChanged(const QString& code, const QString& description);
protected slots:
    void itemClicked(const QModelIndex &index);
    void search();
protected:
    void processClick(QTreeWidgetItem* listitem, bool secondary_gesture);
    // void changePage(int root_index);
    void select(const DiagnosticCode* dc);
    // void browseTo(const DiagnosticCode* dc);
    // void up();
protected:
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    QSharedPointer<QStandardItemModel> m_model;
    QPointer<QTreeView> m_treeview;
};
