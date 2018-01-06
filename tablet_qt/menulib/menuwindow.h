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

#define MENUWINDOW_USE_HFW_LISTWIDGET  // good
// #define MENUWINDOW_USE_HFW_LAYOUT  // bad; window contains scroll area, which gets too short

#include <QPointer>
#include <QSharedPointer>
#include <QVector>
#include "common/aliases_camcops.h"
#include "core/camcopsapp.h"  // for LockState
#include "layouts/layouts.h"
#include "menulib/menuitem.h"
#include "widgets/heightforwidthlistwidget.h"
#include "widgets/openablewidget.h"

class MenuHeader;
class Questionnaire;
class QListWidget;
class QListWidgetItem;


class MenuWindow : public OpenableWidget
{
    Q_OBJECT

public:
    MenuWindow(CamcopsApp& app, const QString& title,
               const QString& icon = "", bool top = false);
    // Derived constructors should be LIGHTWEIGHT, as
    // MenuItem::MenuItem(MenuProxyPtr, CamcopsApp&) will create an INSTANCE
    // to get the title/subtitle.
    // ... note that we can't have a virtual static function (as we would in
    // Python: a classmethod that can be overridden), so title etc.
    // can't be static.
    // ... Note also that destroying and recreating the menu header etc.
    // seem to lead to dangers and loose signals (well, doubled signals --
    // possibly because we were connecting signals during a signal call), so we
    // do need to create those.

    // If it's cheap, populate m_items in the constructor.
    // If it's expensive (e.g. task lists), override build() to do:
    // (a) populate m_items;
    // (b) call MenuWindow::build();
    // (c) +/- any additional work (e.g. signals/slots).
    void setIcon(const QString& icon);
    virtual void build() override;  // called by framework prior to opening

    QString title() const;
    QString subtitle() const;
    QString icon() const;
    int currentIndex() const;
    TaskPtr currentTask() const;
    PatientPtr currentPatient() const;

protected:
    void reloadStyleSheet();
    void loadStyleSheet();

signals:
    void offerAdd(bool offer_add);
    void offerView(bool offer_view);
    void offerEditDelete(bool offer_edit, bool offer_delete);
    void offerFinishFlag(bool offer_finish_flag);

public slots:
    void menuItemSelectionChanged();
    void menuItemClicked(QListWidgetItem *item);
    void lockStateChanged(CamcopsApp::LockState lockstate);
    virtual void viewItem();
    virtual void editItem();
    virtual void deleteItem();
    void debugLayout();

protected:
    void viewTask();
    void editTask();
    void editTaskConfirmed(const TaskPtr& task);
    void deleteTask();
    void toggleFinishFlag();
    void connectQuestionnaireToTask(OpenableWidget* widget, Task* task);
    void complainTaskNotOfferingEditor();

protected:
    CamcopsApp& m_app;
    QString m_title;
    QString m_subtitle;
    QString m_icon;
    bool m_top;
    QVector<MenuItem> m_items;
#ifdef MENUWINDOW_USE_HFW_LAYOUT
    QPointer<VBoxLayout> m_mainlayout;
#else
    QPointer<QVBoxLayout> m_mainlayout;
#endif
    QPointer<MenuHeader> m_p_header;
#ifdef MENUWINDOW_USE_HFW_LISTWIDGET
    QPointer<HeightForWidthListWidget> m_p_listwidget;
#else
    QPointer<QListWidget> m_p_listwidget;
#endif
};
