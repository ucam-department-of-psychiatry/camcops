/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once
#include <QModelIndex>
#include <QPointer>
#include <QSharedPointer>
#include "common/aliases_camcops.h"
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
    // Offers both a tree browser and a search box for diagnostic codes.

    Q_OBJECT
public:
    DiagnosticCodeSelector(const QString& stylesheet,
                           DiagnosticCodeSetPtr codeset,
                           const QModelIndex& selected = QModelIndex(),
                           QWidget* parent = nullptr);
signals:
    void codeChanged(const QString& code, const QString& description);
protected slots:
    void selectionChanged(const QItemSelection& selected,
                          const QItemSelection& deselected);
    void proxySelectionChanged(const QItemSelection& proxy_selected,
                               const QItemSelection& proxy_deselected);
    void searchItemClicked(const QModelIndex& index);
    void treeItemClicked(const QModelIndex& index);
    void searchTextEdited(const QString& text);
    // void toggleSearch();
    void goToSearch();
    void goToTree();
    void debugLayout();
protected:
    void itemChosen(const QModelIndex& index);
    QModelIndex sourceFromProxy(const QModelIndex& index);
    QModelIndex proxyFromSource(const QModelIndex& index);
    void setSearchAppearance();
protected:
    DiagnosticCodeSetPtr m_codeset;
    QPointer<QTreeView> m_treeview;  // for exploring
    QPointer<QListView> m_flatview;  // for searching
    QPointer<QLineEdit> m_search_lineedit;
    QPointer<QLabel> m_heading_tree;
    QPointer<QLabel> m_heading_search;
    QPointer<QAbstractButton> m_search_button;
    QPointer<QAbstractButton> m_tree_button;
    QSharedPointer<QItemSelectionModel> m_selection_model;
    QSharedPointer<FlatProxyModel> m_flat_proxy_model;
    QSharedPointer<DiagnosisSortFilterModel> m_diag_filter_model;
    QSharedPointer<QItemSelectionModel> m_proxy_selection_model;
    bool m_searching;
};
