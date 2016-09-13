#include "diagnosticcodeselector.h"
#include <functional>
#include <QApplication>
#include <QDebug>
#include <QEvent>
#include <QHeaderView>
#include <QItemSelectionModel>
#include <QLineEdit>
#include <QListView>
#include <QModelIndex>
#include <QStackedWidget>
#include <QStandardItemModel>
#include <QTreeView>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "diagnosis/diagnosticcodeset.h"
#include "diagnosis/diagnosissortfiltermodel.h"
#include "diagnosis/flatproxymodel.h"
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
        QModelIndex selected,
        QWidget* parent) :
    OpenableWidget(parent),
    m_codeset(codeset),
    m_treeview(nullptr),
    m_selection_model(nullptr),
    m_flat_proxy_model(nullptr),
    m_diag_filter_model(nullptr),
    m_proxy_selection_model(nullptr)
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
    // Selection model
    // ========================================================================

    m_selection_model = QSharedPointer<QItemSelectionModel>(
                new QItemSelectionModel(m_codeset.data()));
    connect(m_selection_model.data(), &QItemSelectionModel::selectionChanged,
            this, &DiagnosticCodeSelector::selectionChanged);
    m_selection_model->select(selected, QItemSelectionModel::ClearAndSelect);

    // ========================================================================
    // Tree view
    // ========================================================================

    m_treeview = new QTreeView();
    m_treeview->setModel(m_codeset.data());
    m_treeview->setSelectionModel(m_selection_model.data());
    m_treeview->setWordWrap(true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_CODE, true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_DESCRIPTION, true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_FULLNAME, false);
    m_treeview->setSortingEnabled(false);
    m_treeview->scrollTo(selected);

    // ========================================================================
    // Search box
    // ========================================================================

    QLineEdit* lineedit = new QLineEdit();
    connect(lineedit, &QLineEdit::textEdited,
            this, &DiagnosticCodeSelector::searchTextEdited);

    // ========================================================================
    // Proxy models: (1) flatten (2) filter
    // ========================================================================
    // http://doc.qt.io/qt-5/qsortfilterproxymodel.html#details

    m_flat_proxy_model = QSharedPointer<FlatProxyModel>(
                new FlatProxyModel());
    m_flat_proxy_model->setSourceModel(m_codeset.data());

    m_diag_filter_model = QSharedPointer<DiagnosisSortFilterModel>(
                new DiagnosisSortFilterModel());
    m_diag_filter_model->setSourceModel(m_flat_proxy_model.data());
    m_diag_filter_model->setSortCaseSensitivity(Qt::CaseInsensitive);
    m_diag_filter_model->sort(DiagnosticCode::COLUMN_CODE, Qt::AscendingOrder);
    m_diag_filter_model->setFilterCaseSensitivity(Qt::CaseInsensitive);
    m_diag_filter_model->setFilterKeyColumn(DiagnosticCode::COLUMN_DESCRIPTION);

    // ========================================================================
    // Selection model for proxy model
    // ========================================================================

    m_proxy_selection_model = QSharedPointer<QItemSelectionModel>(
                new QItemSelectionModel(m_diag_filter_model.data()));
   connect(m_proxy_selection_model.data(), &QItemSelectionModel::selectionChanged,
           this, &DiagnosticCodeSelector::proxySelectionChanged);
   QModelIndex proxy_selected = proxyFromSource(selected);
   m_proxy_selection_model->select(proxy_selected,
                                   QItemSelectionModel::ClearAndSelect);

    // ========================================================================
    // List view, for search
    // ========================================================================
    // We want to show all depths, not just the root nodes, and QListView
    // doesn't by default.
    // - You can make a QTreeView look like this:
    //   http://stackoverflow.com/questions/21564976
    //   ... but users can collapse/expand (and it collapses by itself) and
    //   is not ideal.
    // - The alternative is a proxy model that flattens properly for us (see
    //   same link). We'll do that, and use a real QListView.

    QListView* flatview = new QListView();
    flatview->setModel(m_diag_filter_model.data());
    flatview->setSelectionModel(m_proxy_selection_model.data());
    flatview->setWordWrap(true);
    flatview->scrollTo(proxy_selected);

    // ========================================================================
    // Final assembly (with "this" as main widget)
    // ========================================================================

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addLayout(header_mainlayout);
    mainlayout->addWidget(m_treeview);
    mainlayout->addWidget(lineedit);
    mainlayout->addWidget(flatview);

    QWidget* topwidget = new QWidget();
    topwidget->setObjectName("menu_window_background");
    topwidget->setLayout(mainlayout);

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->setContentsMargins(UiConst::NO_MARGINS);
    toplayout->addWidget(topwidget);

    setLayout(toplayout);
}


void DiagnosticCodeSelector::selectionChanged(const QItemSelection& selected,
                                              const QItemSelection& deselected)
{
    (void)deselected;
    QModelIndexList indexes = selected.indexes();
    if (indexes.isEmpty()) {
        return;
    }
    QModelIndex index = indexes.at(0);
    newSelection(index);
}


void DiagnosticCodeSelector::newSelection(const QModelIndex& index)
{
    if (!index.isValid()) {
        return;
    }
    // Now, we want to get an index to potentially different columns of
    // the same object. Note that index.row() is NOT unique, it's just the row
    // number for a given parent.
    // To get a different column, we go via the parent back to the child:
    // http://doc.qt.io/qt-5/qmodelindex.html#details
    QModelIndex parent = index.parent();
    QModelIndex code_index = parent.child(
                index.row(), DiagnosticCode::COLUMN_CODE);
    QModelIndex description_index = parent.child(
                index.row(), DiagnosticCode::COLUMN_DESCRIPTION);
    QString code = code_index.data().toString();
    QString description = description_index.data().toString();

    emit codeChanged(code, description);
    emit finished();
}


void DiagnosticCodeSelector::proxySelectionChanged(
        const QItemSelection& proxy_selected,
        const QItemSelection& proxy_deselected)
{
    (void)proxy_deselected;
    QModelIndexList proxy_indexes = proxy_selected.indexes();
    if (proxy_indexes.isEmpty()) {
        return;
    }
    QModelIndex proxy_index = proxy_indexes.at(0);
    QModelIndex src_index = sourceFromProxy(proxy_index);
    newSelection(src_index);
}


void DiagnosticCodeSelector::search()
{
    qDebug() << Q_FUNC_INFO;
}


void DiagnosticCodeSelector::searchTextEdited(const QString& text)
{
    m_diag_filter_model->setFilterFixedString(text);
}


QModelIndex DiagnosticCodeSelector::sourceFromProxy(const QModelIndex& index)
{
    QModelIndex intermediate = m_diag_filter_model->mapToSource(index);
    return m_flat_proxy_model->mapToSource(intermediate);
}


QModelIndex DiagnosticCodeSelector::proxyFromSource(const QModelIndex& index)
{
    QModelIndex intermediate = m_flat_proxy_model->mapFromSource(index);
    return m_diag_filter_model->mapFromSource(intermediate);
}
