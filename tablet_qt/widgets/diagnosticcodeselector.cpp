#include "diagnosticcodeselector.h"
#include <QDebug>
#include <QListWidget>
#include <QStackedWidget>
#include <QVBoxLayout>
#include "common/uiconstants.h"


DiagnosticCodeSelector::DiagnosticCodeSelector(
        QSharedPointer<DiagnosticCodeSet> codeset,
        int selected_index,
        QWidget* parent) :
    OpenableWidget(parent),
    m_codeset(codeset),
    m_selected_index(selected_index)
{
    Q_ASSERT(m_codeset);

    //*** cf. MenuWindow
    //*** with search button [search box replaces title]

    // *** setStyleSheet(m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_MENU));
    // *** setObjectName("menu_window_outer_object");

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->setContentsMargins(UiConst::NO_MARGINS);
    setLayout(toplayout);

    QWidget* topwidget = new QWidget();
    topwidget->setObjectName("menu_window_background");
    toplayout->addWidget(topwidget);

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    topwidget->setLayout(mainlayout);

    // ========================================================================
    // Header
    // ========================================================================

    // *** MenuHeader* header = new MenuHeader(this, m_app, m_top, m_title, m_icon);
    // *** mainlayout->addWidget(header);

    // *** connect "up" button to upFrom(
    // *** connect "cancel" button to finished()

    // ========================================================================
    // List widget
    // ========================================================================

    m_listwidget = new QListWidget();
    mainlayout->addWidget(m_listwidget);

    int root_index = 0;
    if (selected_index != DiagnosticCodeSet::INVALID) {
        root_index = m_codeset->parentIndexOf(selected_index);
    }
    changePage(root_index);
}


void DiagnosticCodeSelector::changePage(int root_index)
{
    m_root_index = root_index;
    qDebug() << Q_FUNC_INFO << m_root_index;
    const DiagnosticCode* root_item = m_codeset->item(m_root_index);
    if (!root_item) {
        qCritical() << Q_FUNC_INFO << "Bad pointer";
        return;
    }
    QString title = root_item->fullname();
    QList<const DiagnosticCode*> items = m_codeset->children(m_root_index);
    qDebug() << Q_FUNC_INFO << title;
    for (auto dc : items) {
        qDebug() << Q_FUNC_INFO << dc;
        int index = dc->index();
        QString text = dc->fullname();
        QListWidgetItem* listitem = new QListWidgetItem(text, m_listwidget);
        listitem->setData(Qt::UserRole, QVariant(index));
    }
}


void DiagnosticCodeSelector::clicked(int index)
{
    const DiagnosticCode* item = m_codeset->item(index);
    if (!item) {
        return;
    }
    // Single-click: browse (if has children) or select (if leaf node)
    if (item->hasChildren()) {
        browseTo(item);
    } else {
        select(item);
    }
}


void DiagnosticCodeSelector::doubleClicked(int index)
{
    const DiagnosticCode* item = m_codeset->item(index);
    if (!item) {
        return;
    }
    // Double-click: select, if selectable; browse if not.
    if (item->selectable()) {
        select(item);
    } else {
        browseTo(item);
    }
}


void DiagnosticCodeSelector::select(const DiagnosticCode* item)
{
    if (!item || !item->selectable()) {
        qWarning() << Q_FUNC_INFO << "can't select this item";
        return;
    }
    emit codeChanged(item->code(), item->description());
}


void DiagnosticCodeSelector::browseTo(const DiagnosticCode* item)
{
    if (!item || !item->hasChildren()) {
        qWarning() << Q_FUNC_INFO << "can't browse to this item";
        return;
    }
    changePage(item->index());
}


void DiagnosticCodeSelector::up()
{
    const DiagnosticCode* root = m_codeset->item(m_root_index);
    if (!root || root->parentIndex() == DiagnosticCodeSet::INVALID) {
        qWarning() << Q_FUNC_INFO << "can't go up from this item";
        return;
    }
    const DiagnosticCode* parent = m_codeset->item(root->parentIndex());
    browseTo(parent);
}
