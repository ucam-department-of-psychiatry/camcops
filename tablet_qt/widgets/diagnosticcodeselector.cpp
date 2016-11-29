/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

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
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "diagnosis/diagnosticcodeset.h"
#include "diagnosis/diagnosissortfiltermodel.h"
#include "diagnosis/flatproxymodel.h"
#include "widgets/horizontalline.h"
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
    m_flatview(nullptr),
    m_lineedit(nullptr),
    m_heading_tree(nullptr),
    m_heading_search(nullptr),
    m_search_button(nullptr),
    m_tree_button(nullptr),
    m_selection_model(nullptr),
    m_flat_proxy_model(nullptr),
    m_diag_filter_model(nullptr),
    m_proxy_selection_model(nullptr),
    m_searching(false)
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
    title_label->setObjectName(CssConst::TITLE);

    m_search_button = new ImageButton(UiConst::CBS_ZOOM);  // *** ICON: remove "+" from centre of magnifying glass
    connect(m_search_button.data(), &QAbstractButton::clicked,
            this, &DiagnosticCodeSelector::goToSearch);

    m_tree_button = new ImageButton(UiConst::CBS_CHOOSE_PAGE);  // *** ICON: tree view
    connect(m_tree_button.data(), &QAbstractButton::clicked,
            this, &DiagnosticCodeSelector::goToTree);

    QHBoxLayout* header_toprowlayout = new QHBoxLayout();
    header_toprowlayout->addWidget(cancel, 0, button_align);
    header_toprowlayout->addWidget(title_label);  // default alignment fills whole cell
    header_toprowlayout->addWidget(m_search_button, 0, button_align);
    header_toprowlayout->addWidget(m_tree_button, 0, button_align);

    // ------------------------------------------------------------------------
    // Horizontal line
    // ------------------------------------------------------------------------
    HorizontalLine* horizline = new HorizontalLine(UiConst::HEADER_HLINE_WIDTH);
    horizline->setObjectName(CssConst::HEADER_HORIZONTAL_LINE);

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

    m_heading_tree = new QLabel(tr("Explore as tree:"));
    m_heading_tree->setObjectName(CssConst::HEADING);

    m_treeview = new QTreeView();
    m_treeview->setModel(m_codeset.data());
    m_treeview->setSelectionModel(m_selection_model.data());
    if (m_treeview->header()) {
        m_treeview->header()->close();
    }
    m_treeview->setWordWrap(true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_CODE, true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_DESCRIPTION, true);
    m_treeview->setColumnHidden(DiagnosticCode::COLUMN_FULLNAME, false);
    m_treeview->setSortingEnabled(false);
    m_treeview->scrollTo(selected);

    // ========================================================================
    // Search box
    // ========================================================================

    m_lineedit = new QLineEdit();
    connect(m_lineedit, &QLineEdit::textEdited,
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

    m_heading_search = new QLabel(tr("Search diagnoses:"));
    m_heading_search->setObjectName(CssConst::HEADING);

    m_flatview = new QListView();
    m_flatview->setModel(m_diag_filter_model.data());
    m_flatview->setSelectionModel(m_proxy_selection_model.data());
    m_flatview->setWordWrap(true);
    m_flatview->scrollTo(proxy_selected);

    // ========================================================================
    // Final assembly (with "this" as main widget)
    // ========================================================================

    setSearchAppearance();

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addLayout(header_mainlayout);
    mainlayout->addWidget(m_heading_tree);
    mainlayout->addWidget(m_treeview);
    mainlayout->addWidget(m_heading_search);
    mainlayout->addWidget(m_lineedit);
    mainlayout->addWidget(m_flatview);

    QWidget* topwidget = new QWidget();
    topwidget->setObjectName(CssConst::MENU_WINDOW_BACKGROUND);
    topwidget->setLayout(mainlayout);

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->setContentsMargins(UiConst::NO_MARGINS);
    toplayout->addWidget(topwidget);

    setLayout(toplayout);
}


void DiagnosticCodeSelector::selectionChanged(const QItemSelection& selected,
                                              const QItemSelection& deselected)
{
    Q_UNUSED(deselected)
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
    Q_UNUSED(proxy_deselected)
    QModelIndexList proxy_indexes = proxy_selected.indexes();
    if (proxy_indexes.isEmpty()) {
        return;
    }
    QModelIndex proxy_index = proxy_indexes.at(0);
    QModelIndex src_index = sourceFromProxy(proxy_index);
    newSelection(src_index);
}


//void DiagnosticCodeSelector::toggleSearch()
//{
//    m_searching = !m_searching;
//    setSearchAppearance();
//}


void DiagnosticCodeSelector::goToSearch()
{
    m_searching = true;
    setSearchAppearance();
}


void DiagnosticCodeSelector::goToTree()
{
    m_searching = false;
    setSearchAppearance();
}


void DiagnosticCodeSelector::setSearchAppearance()
{
    m_tree_button->setVisible(m_searching);
    m_search_button->setVisible(!m_searching);

    m_heading_tree->setVisible(!m_searching);
    m_treeview->setVisible(!m_searching);

    m_flatview->setVisible(m_searching);
    m_flatview->setVisible(m_searching);
    m_heading_search->setVisible(m_searching);

    update();
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
