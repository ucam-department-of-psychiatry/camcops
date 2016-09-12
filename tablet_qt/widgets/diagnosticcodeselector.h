#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "diagnosis/diagnosticcodeset.h"
#include "openablewidget.h"

class QListWidget;


class DiagnosticCodeSelector : public OpenableWidget
{
    Q_OBJECT
public:
    DiagnosticCodeSelector(QSharedPointer<DiagnosticCodeSet> codeset,
                           int selected_index = DiagnosticCodeSet::INVALID,
                           QWidget* parent = nullptr);
signals:
    void codeChanged(const QString& code, const QString& description);
protected:
    void changePage(int root_index);
    void clicked(int index);
    void doubleClicked(int index);
    void select(const DiagnosticCode* item);
    void browseTo(const DiagnosticCode* item);
    void up();
protected:
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    int m_selected_index;
    QPointer<QListWidget> m_listwidget;
    int m_root_index;
};
