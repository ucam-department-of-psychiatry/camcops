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


bool DiagnosticCodeFilter::filterAcceptsRow(int row,
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
    if (index.data().toString().contains(filterRegExp())) {
        return true;
    }

    // Permit if children are shown as well
    int rows = sourceModel()->rowCount(index);
    for (int r = 0; r < rows; r++) {
        if (filterAcceptsRow(r, index)) {
            return true;
        }
    }
    return false;
}


DiagnosticCodeSelector::DiagnosticCodeSelector(
        const QString& stylesheet,
        QSharedPointer<DiagnosticCodeSet> codeset,
        QModelIndex selected,
        QWidget* parent) :
    OpenableWidget(parent),
    m_codeset(codeset),
    m_treeview(nullptr),
    m_selection_model(nullptr),
    m_proxy_model(nullptr)
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
    // Proxy model
    // ========================================================================
    // http://doc.qt.io/qt-5/qsortfilterproxymodel.html#details

    m_proxy_model = QSharedPointer<DiagnosticCodeFilter>(
                new DiagnosticCodeFilter());
    m_proxy_model->setSourceModel(m_codeset.data());
    m_proxy_model->setSortCaseSensitivity(Qt::CaseInsensitive);
    m_proxy_model->sort(DiagnosticCode::COLUMN_CODE, Qt::AscendingOrder);
    m_proxy_model->setFilterCaseSensitivity(Qt::CaseInsensitive);
    m_proxy_model->setFilterKeyColumn(DiagnosticCode::COLUMN_DESCRIPTION);

    // ========================================================================
    // List view... a disguised tree view.
    // ========================================================================
    // We want to show all depths, not just the root nodes, and QListView
    // doesn't by default.
    // - You can make a QTreeView look like this:
    //   http://stackoverflow.com/questions/21564976
    //   ... but users can collapse/expand (and it collapses by itself) and
    //   is not ideal.
    // - The alternative is a proxy model that flattens properly for us (see
    //   same link).

    QListView* flatview = new QListView();
    flatview->setModel(m_proxy_model.data());
    flatview->setSelectionModel(m_selection_model.data());
    flatview->setWordWrap(true);
    flatview->scrollTo(selected);

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
    qDebug() << "selected:" << selected;
    QModelIndexList indexes = selected.indexes();
    qDebug() << "indexes:" << indexes;
    if (indexes.isEmpty()) {
        return;
    }
    QModelIndex index = indexes.at(0);
    qDebug() << "index:" << index;
    qDebug() << "index.row():" << index.row();
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


void DiagnosticCodeSelector::search()
{
    qDebug() << Q_FUNC_INFO;
}


void DiagnosticCodeSelector::searchTextEdited(const QString& text)
{
    m_proxy_model->setFilterFixedString(text);
}
