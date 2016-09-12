#include "diagnosticcodeselector.h"
#include <functional>
#include <QApplication>
#include <QDebug>
#include <QEvent>
#include <QModelIndex>
#include <QStackedWidget>
#include <QStandardItemModel>
#include <QTreeView>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "widgets/imagebutton.h"
#include "widgets/labelwordwrapwide.h"

/*

- To enable the selection of a non-leaf node, if desired:

- Separating out single clicks and double clicks is confusing, in that the
  standard double-click delay is noticeable, and if you react to a single click
  at the end of that time, it looks like the software has a huge latency.

  - http://stackoverflow.com/questions/22142485
  - QApplication::doubleClickInterval()

- Better would be to have a "hold" gesture.

- However, the standard "install event filter" and eventFilter() function
  doesn't pick up what's needed from QListWidget. One probably has to use
  QListView (which also offers mousePressEvent, mouseMoveEvent,
  mouseReleaseEvent). However, this probably gets non-intuitive for users.

- Therefore, buttons for "choose me" and "drill down into me", with the default
  for touches in the non-button area being "drill down into me".

- Shoving buttons inside a QListWidget isn't great. So:
    http://stackoverflow.com/questions/4004705
  ... use a QTreeWidget, to get multiple columns
  ... at which point: it's a tree!

- Then the proper way to do filtering is with a QSortFilterProxyModel, using
  a QTreeView rather than a QTreeWidget.

*/

DiagnosticCodeSelector::DiagnosticCodeSelector(
        const QString& stylesheet,
        QSharedPointer<DiagnosticCodeSet> codeset,
        int selected_index,
        QWidget* parent) :
    OpenableWidget(parent),
    m_codeset(codeset),
    m_model(nullptr),
    m_treeview(nullptr)
{
    Q_ASSERT(m_codeset);

    setStyleSheet(stylesheet);

    // ========================================================================
    // Header
    // ========================================================================

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------

    Qt::Alignment button_align = Qt::AlignHCenter | Qt::AlignTop;

    // Cancel button
    QAbstractButton* cancel = new ImageButton(UiConst::CBS_CANCEL);
    connect(cancel, &QAbstractButton::clicked,
            this, &DiagnosticCodeSelector::finished);

    // Title
    LabelWordWrapWide* title_label = new LabelWordWrapWide(m_codeset->title());
    title_label->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);

    QAbstractButton* search = new ImageButton(UiConst::CBS_ZOOM);  // *** check icon is OK
    connect(cancel, &QAbstractButton::clicked,
            this, &DiagnosticCodeSelector::search);

    QHBoxLayout* header_toprowlayout = new QHBoxLayout();
    header_toprowlayout->addWidget(cancel, 0, button_align);
    header_toprowlayout->addWidget(title_label);  // default alignment fills whole cell
    header_toprowlayout->addWidget(search, 0, button_align);

    // ------------------------------------------------------------------------
    // Horizontal line
    // ------------------------------------------------------------------------
    QFrame* horizline = new QFrame();
    horizline->setObjectName("header_horizontal_line");
    horizline->setFrameShape(QFrame::HLine);
    horizline->setFrameShadow(QFrame::Plain);
    horizline->setLineWidth(UiConst::HEADER_HLINE_WIDTH);

    // ------------------------------------------------------------------------
    // Header assembly
    // ------------------------------------------------------------------------
    QVBoxLayout* header_mainlayout = new QVBoxLayout();
    header_mainlayout->addLayout(header_toprowlayout);
    header_mainlayout->addWidget(horizline);

    // ========================================================================
    // List widget
    // ========================================================================

    m_treeview = new QTreeView();
    connect(m_treeview, &QTreeView::clicked,
            this, &DiagnosticCodeSelector::itemClicked,
            Qt::UniqueConnection);

    // ========================================================================
    // Final assembly (with "this" as main widget)
    // ========================================================================

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addLayout(header_mainlayout);
    mainlayout->addWidget(m_treeview);

    QWidget* topwidget = new QWidget();
    topwidget->setObjectName("menu_window_background");
    topwidget->setLayout(mainlayout);

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->setContentsMargins(UiConst::NO_MARGINS);
    toplayout->addWidget(topwidget);

    setLayout(toplayout);

    // ========================================================================
    // Tree setup
    // ========================================================================

    m_model = QSharedPointer<QStandardItemModel>(new QStandardItemModel(this));
    m_model->setColumnCount(1);  // resizing >1 is tricky with tablet displays

    QTreeWidgetItem* selected_item = nullptr;
    int n = m_codeset->size();
    for (int i = 1; i < n; ++i) {  // SKIP ROOT
        qDebug() << "m_model->rowCount()" << m_model->rowCount();
        const DiagnosticCode* dc = m_codeset->at(i);
        if (dc->hasParent() && dc->parentIndex() > m_model->rowCount()) {
            // Note: we use ">" not ">=" because we're introducing an off-by-
            // one change
            qWarning() << Q_FUNC_INFO
                       << "Error: code is forward-referencing its parent";
            continue;
        }

        QStandardItem* ti = new QStandardItem();

        // *** bool selected = i == selected_index;
        /*
        ti->setSelected(selected);
        if (selected) {
            selected_item = ti;
        }
        */

        Qt::ItemFlags flags = Qt::ItemIsEnabled;
        if (dc->selectable()) {
            flags |= Qt::ItemIsSelectable;
        }
        ti->setFlags(flags);
        ti->setData(QVariant(i), Qt::UserRole);
        ti->setText(dc->fullname());

        QStandardItem* parent;
        if (dc->parentIsRoot()) {
            qDebug() << "appending row" << i << "to root";
            parent = m_model->invisibleRootItem();
        } else {
            int parent_index = dc->parentIndex() - 1;
            qDebug() << "appending row" << i << "to model item" << parent_index;
            // ... subtract one because we don't include the root.
            parent = m_model->item(parent_index);
        }
        parent->appendRow(ti);
    }

    m_treeview->setModel(m_model.data());
    m_treeview->setSortingEnabled(false);
    if (selected_item) {
        // *** // m_treeview->scrollTo(selected_item);
    }
    (void)selected_index;//***
}


void DiagnosticCodeSelector::itemClicked(const QModelIndex& index)
{
    // WHAT'S BEEN CHOSEN?
    QVariant v = index.data(Qt::UserRole);
    int dc_index = v.toInt();
    if (!m_codeset->isValidIndex(dc_index)) {
        qWarning() << Q_FUNC_INFO << "invalid dc_index selected:" << dc_index;
        return;
    }

    const DiagnosticCode* dc = m_codeset->at(dc_index);
    if (!dc) {
        qWarning() << Q_FUNC_INFO << "bad item";
        return;
    }

    select(dc);
}


void DiagnosticCodeSelector::select(const DiagnosticCode* dc)
{
    if (!dc || !dc->selectable()) {
        qWarning() << Q_FUNC_INFO << "can't select this item";
        return;
    }
    emit codeChanged(dc->code(), dc->description());
    emit finished();
}


void DiagnosticCodeSelector::search()
{
    qDebug() << Q_FUNC_INFO;
}
