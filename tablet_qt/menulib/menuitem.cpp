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

// #define DEBUG_VERBOSE

#include "menuitem.h"
#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPushButton>
#include <QScopedPointer>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
#include "lib/convert.h"
#include "lib/datetimefunc.h"  // for SHORT_DATETIME_FORMAT
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "menu/choosepatientmenu.h"
#include "menu/singletaskmenu.h"
#include "menulib/htmlinfowindow.h"
#include "menulib/menuwindow.h"
#include "tasklib/taskfactory.h"
// #include "widgets/heightforwidthlayoutcontainer.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/openablewidget.h"

const int STRETCH_3COL_WTASKNAME_TASKNAME = 1;
const int STRETCH_3COL_WTASKNAME_TIMESTAMP = 2;
const int STRETCH_3COL_WTASKNAME_SUMMARY = 7;

const int STRETCH_3COL_WPATIENT_PATIENT = 3;
const int STRETCH_3COL_WPATIENT_TIMESTAMP = 2;
const int STRETCH_3COL_WPATIENT_SUMMARY = 7;

const int STRETCH_2COL_TIMESTAMP = 2;
const int STRETCH_2COL_SUMMARY = 8;


MenuItem::MenuItem() :
    m_title("?")
{
    setDefaults();
}


MenuItem::MenuItem(const QString& title) :
    m_title(title)
{
    // this constructor used for placeholders for not-implemented stuff
    setDefaults();
    m_implemented = false;
}


MenuItem::MenuItem(const QString& title, const MenuItem::ActionFunction& func,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_func = func;
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(const QString& title,
                   const MenuItem::OpenableWidgetMaker& func,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_openable_widget_maker = func;
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(MenuProxyPtr p_menuproxy, CamcopsApp& app)
    // m_title: below
{
    setDefaults();
    m_p_menuproxy = p_menuproxy;

    QScopedPointer<MenuWindow> mw(m_p_menuproxy->create(app));
    m_title = mw->title();
    m_subtitle = mw->subtitle();
    m_icon = mw->icon();
}


MenuItem::MenuItem(const ChoosePatientMenuItem& choose_patient,
                   CamcopsApp& app)
{
    // We do some more of the work for the client, since "choose patient"
    // appears on lots of menus.
    Q_UNUSED(choose_patient);  // it's just a marker object
    // You can't call another constructor directly, so...

    setDefaults();
    m_p_menuproxy = MenuProxyPtr(new MenuProxy<ChoosePatientMenu>);

    QScopedPointer<MenuWindow> mw(m_p_menuproxy->create(app));
    m_title = mw->title();
    m_subtitle = mw->subtitle();
    m_icon = mw->icon();
}


MenuItem::MenuItem(const TaskMenuItem& taskmenuitem, CamcopsApp& app)
    // m_title: below
{
    setDefaults();
    m_task_tablename = taskmenuitem.tablename;

    TaskPtr task = app.taskFactory()->create(m_task_tablename);
    if (task == nullptr) {
        m_title = tr("UNKNOWN TASK") + ": " + taskmenuitem.tablename;
        m_implemented = false;
        return;
    }
    m_title = task->menutitle();
    m_subtitle = task->menusubtitle();
    m_crippled = task->isCrippled();
    if (task->isAnonymous()) {
        m_icon = UiFunc::iconFilename(UiConst::ICON_ANONYMOUS);
    }
}


MenuItem::MenuItem(const QString& title, const HtmlMenuItem& htmlmenuitem,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_html = htmlmenuitem;  // extra
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(TaskPtr p_task, bool task_shows_taskname,
                   bool task_shows_patient) :
    m_title("?")
{
    setDefaults();
    m_p_task = p_task;
    m_task_shows_taskname = task_shows_taskname;
    m_task_shows_patient = task_shows_patient;
}


MenuItem::MenuItem(PatientPtr p_patient)
{
    setDefaults();
    m_p_patient = p_patient;
#ifdef DEBUG_VERBOSE
    qDebug() << Q_FUNC_INFO << this;
#endif
}


void MenuItem::setDefaults()
{
    // Not the most efficient, but saves lots of duplication

    // not m_title
    m_subtitle = "";
    m_icon = "";

    m_arrow_on_right = false;
    m_chain = false;
    m_copyright_details_pending = false;
    m_crippled = false;
    m_implemented = true;
    m_label_only = false;
    m_needs_privilege = false;
    m_not_if_locked = false;
    m_task_shows_taskname = false;
    m_task_shows_patient = false;
    m_unsupported = false;

    m_func = nullptr;
    m_openable_widget_maker = nullptr;
    m_p_menuproxy.clear();
    m_task_tablename = "";
    m_p_task.clear();
    m_p_patient.clear();
}


QString MenuItem::title() const
{
    if (m_p_task) {
        return m_p_task->instanceTitle();
    }
    return m_title;
}


TaskPtr MenuItem::task() const
{
    return m_p_task;
}


PatientPtr MenuItem::patient() const
{
#ifdef DEBUG_VERBOSE
    qDebug() << Q_FUNC_INFO << this;
#endif
    return m_p_patient;
}


QWidget* MenuItem::rowWidget(CamcopsApp& app) const
{
    Qt::Alignment text_align = Qt::AlignLeft | Qt::AlignVCenter;
    QSizePolicy sp_icon(QSizePolicy::Fixed, QSizePolicy::Fixed);

    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();
    row->setLayout(rowlayout);

    if (m_p_task) {
        // --------------------------------------------------------------------
        // Task instance
        // --------------------------------------------------------------------
        // Stretch: http://stackoverflow.com/questions/14561516/qt-qhboxlayout-percentage-size
        //
        // ICON | ICON | +----------------------------------------------------+
        // ICON | ICON | | A                   B                 C            |
        // ICON | ICON | |                                                    |
        // ICON | ICON | +----------------------------------------------------+
        //
        // ... where BOXES is either a two- or a three-column layout
        // Layout within that is a bit tricky. We want to specify the stretches
        // so columns are in a fixed proportion. However, labels don't
        // themselves expand beyond what's necessary, and the fixed-stretch
        // method multiplies everything by a fixed amount, so we encapsulate
        // all the text elements in their own QHBoxLayout with its own
        // addStretch(), then stretch-multiply up those (which requires
        // encapsulating *those* in another QWidget...).

        bool complete = m_p_task->isComplete();
        int timestamp_stretch = STRETCH_2COL_TIMESTAMP;
        int summary_stretch = STRETCH_2COL_SUMMARY;

        // Notification of "incomplete" status
        QLabel* incomplete_icon = m_p_task->isComplete()
                ? UiFunc::blankIcon()
                : UiFunc::iconWidget(UiFunc::iconFilename(UiConst::ICON_WARNING));
        incomplete_icon->setSizePolicy(sp_icon);
        rowlayout->addWidget(incomplete_icon);

        // Move-off item, if selected (only applicable to anonymous tasks)
        if (m_p_task->isAnonymous()) {
            QLabel* icon = m_p_task->shouldMoveOffTablet()
                    ? UiFunc::iconWidget(UiFunc::iconFilename(UiConst::CBS_FINISHFLAG))
                    : UiFunc::blankIcon();
            QSizePolicy sp_icon(QSizePolicy::Fixed, QSizePolicy::Fixed);
            icon->setSizePolicy(sp_icon);
            rowlayout->addWidget(icon);
        }

        // Taskname OR patient
        if (m_task_shows_taskname || m_task_shows_patient) {
            QWidget* col1_widget = new QWidget();
            QHBoxLayout* col1_hbox = new QHBoxLayout();
            col1_widget->setLayout(col1_hbox);

            int firstcol_stretch = STRETCH_3COL_WTASKNAME_TASKNAME;
            QString contents;
            if (m_task_shows_taskname) {
                contents = m_p_task->shortname();
                timestamp_stretch = STRETCH_3COL_WTASKNAME_TIMESTAMP;
                summary_stretch = STRETCH_3COL_WTASKNAME_SUMMARY;
            } else {
                if (m_p_task->isAnonymous()) {
                    contents = tr("<Anonymous task>");
                } else {
                    Patient* pt = m_p_task->patient();
                    if (pt) {
                        contents = pt->surnameUpperForename();
                    }
                }
                firstcol_stretch = STRETCH_3COL_WPATIENT_PATIENT;
                timestamp_stretch = STRETCH_3COL_WPATIENT_TIMESTAMP;
                summary_stretch = STRETCH_3COL_WPATIENT_SUMMARY;
            }
            QLabel* taskname = new LabelWordWrapWide(contents);
            taskname->setAlignment(text_align);
            taskname->setObjectName(complete
                                    ? CssConst::TASK_ITEM_TASKNAME_COMPLETE
                                    : CssConst::TASK_ITEM_TASKNAME_INCOMPLETE);

            col1_hbox->addWidget(taskname);
            col1_hbox->addStretch();
            QSizePolicy sp_taskname(QSizePolicy::Preferred,
                                    QSizePolicy::Preferred);
            sp_taskname.setHorizontalStretch(firstcol_stretch);
            col1_widget->setSizePolicy(sp_taskname);
            rowlayout->addWidget(col1_widget);
        }

        // Timestamp
        QWidget* col2_widget = new QWidget();
        QHBoxLayout* col2_hbox = new QHBoxLayout();
        col2_widget->setLayout(col2_hbox);

        QLabel* timestamp = new LabelWordWrapWide(
            m_p_task->whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
        timestamp->setAlignment(text_align);
        timestamp->setObjectName(complete
                                 ? CssConst::TASK_ITEM_TIMESTAMP_COMPLETE
                                 : CssConst::TASK_ITEM_TIMESTAMP_INCOMPLETE);

        col2_hbox->addWidget(timestamp);
        col2_hbox->addStretch();
        QSizePolicy sp_timestamp(QSizePolicy::Preferred,
                                 QSizePolicy::Preferred);
        sp_timestamp.setHorizontalStretch(timestamp_stretch);
        col2_widget->setSizePolicy(sp_timestamp);
        rowlayout->addWidget(col2_widget);

        // Summary
        QWidget* col3_widget = new QWidget();
        QHBoxLayout* col3_hbox = new QHBoxLayout();
        col3_widget->setLayout(col3_hbox);

        QLabel* summary = new LabelWordWrapWide(
                    m_p_task->summaryWithCompleteSuffix());
        summary->setAlignment(text_align);
        summary->setObjectName(complete
                               ? CssConst::TASK_ITEM_SUMMARY_COMPLETE
                               : CssConst::TASK_ITEM_SUMMARY_INCOMPLETE);

        col3_hbox->addWidget(summary);
        col3_hbox->addStretch();
        QSizePolicy sp_summary(QSizePolicy::Preferred, QSizePolicy::Preferred);
        sp_summary.setHorizontalStretch(summary_stretch);
        col3_widget->setSizePolicy(sp_summary);
        rowlayout->addWidget(col3_widget);

    } else if (m_p_patient) {
        // --------------------------------------------------------------------
        // Patient (for patient-choosing menu)
        // --------------------------------------------------------------------
        //
        // ICON | - SURNAME, Forename
        // ICON | - Sex, age, DOB
        // ICON | - ID numbers

        // Title/subtitle style
        QVBoxLayout* textlayout = new QVBoxLayout();

        QSizePolicy sp(QSizePolicy::Preferred, QSizePolicy::Preferred);

        LabelWordWrapWide* title = new LabelWordWrapWide(
                    QString("%1, %2")
                    .arg(m_p_patient->surname().toUpper())
                    .arg(m_p_patient->forename()));
        LabelWordWrapWide* subtitle1 = new LabelWordWrapWide(
                    QString("%1, %2y, DOB %3")
                    .arg(m_p_patient->sex())
                    .arg(m_p_patient->ageYears())
                    .arg(m_p_patient->dobText()));
        LabelWordWrapWide* subtitle2 = new LabelWordWrapWide(
                    m_p_patient->shortIdnumSummary());

        title->setAlignment(text_align);
        subtitle1->setAlignment(text_align);
        subtitle2->setAlignment(text_align);
        title->setObjectName(CssConst::MENU_ITEM_TITLE);
        subtitle1->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
        subtitle2->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
        title->setSizePolicy(sp);
        subtitle1->setSizePolicy(sp);
        subtitle2->setSizePolicy(sp);
        textlayout->addWidget(title);
        textlayout->addWidget(subtitle1);
        textlayout->addWidget(subtitle2);

        // Patient icon
        if (!m_p_patient->compliesWith(app.uploadPolicy()) ||
                m_p_patient->anyIdClash()) {
            rowlayout->addWidget(UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_STOP)));
        } else if (!m_p_patient->compliesWith(app.finalizePolicy())) {
            rowlayout->addWidget(UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_WARNING)));
        } else if (m_p_patient->shouldMoveOffTablet()) {
            rowlayout->addWidget(UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::CBS_FINISHFLAG)));
        } else {
            rowlayout->addWidget(UiFunc::blankIcon());
        }

        rowlayout->addLayout(textlayout);
        rowlayout->addStretch();

    } else {
        // --------------------------------------------------------------------
        // Conventional menu item
        // --------------------------------------------------------------------
        //
        // ICON | - Title                                           | childicon
        // ICON | - Subtitle                                        | childicon
        // ICON |                                                   | childicon

        // Icon
        if (!m_label_only) {  // Labels go full-left
            if (!m_icon.isEmpty()) {
                QLabel* icon = UiFunc::iconWidget(m_icon);
                rowlayout->addWidget(icon);
            } else if (m_chain) {
                QLabel* icon = UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_CHAIN));
                rowlayout->addWidget(icon);
            } else {
                rowlayout->addWidget(UiFunc::blankIcon());
            }
        }

        // Title/subtitle
        QVBoxLayout* textlayout = new QVBoxLayout();

        QLabel* title = new LabelWordWrapWide(m_title);
        title->setAlignment(text_align);
        title->setObjectName(CssConst::MENU_ITEM_TITLE);
        textlayout->addWidget(title);
        if (!m_subtitle.isEmpty()) {
            QLabel* subtitle = new LabelWordWrapWide(m_subtitle);
            subtitle->setAlignment(text_align);
            subtitle->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
            textlayout->addWidget(subtitle);
        }
        rowlayout->addLayout(textlayout);
        rowlayout->addStretch();

        // Arrow on right
        if (m_arrow_on_right) {
            QLabel* iconLabel = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_HASCHILD),
                nullptr, false);
            rowlayout->addWidget(iconLabel);
        }

        // Background colour, via stylesheets
        if (m_label_only) {
            row->setObjectName(CssConst::LABEL_ONLY);
        } else if (!m_implemented) {
            row->setObjectName(CssConst::NOT_IMPLEMENTED);
        } else if (m_unsupported) {
            row->setObjectName(CssConst::UNSUPPORTED);
        } else if (m_not_if_locked && app.locked()) {
            row->setObjectName(CssConst::LOCKED);
        } else if (m_needs_privilege && !app.privileged()) {
            row->setObjectName(CssConst::NEEDS_PRIVILEGE);
        }
        // ... but not for locked/needs privilege, as otherwise we'd need
        // to refresh the whole menu? Well, we could try it.
        // On Linux desktop, it's extremely fast.
    }

    // Size policy
    QSizePolicy size_policy(QSizePolicy::MinimumExpanding,  // horizontal
                            QSizePolicy::Fixed);  // vertical
    row->setSizePolicy(size_policy);

    return row;
}


void MenuItem::act(CamcopsApp& app) const
{
    // ========================================================================
    // Reasons to refuse
    // ========================================================================
    if (m_label_only) {
        // qDebug() << "Label-only row touched; ignored";
        return;
    }
    if (m_p_task) {
        // Handled via verb buttons instead.
        return;
    }
    if (!m_implemented) {
        UiFunc::alert(tr("Not implemented yet!"));
        return;
    }
    if (m_unsupported) {
        UiFunc::alert(tr("Not supported on this platform!"));
        return;
    }
    if (m_needs_privilege && !app.privileged()) {
        UiFunc::alert(tr("You must set Privileged Mode first"));
        return;
    }
    if (m_not_if_locked && app.locked()) {
        UiFunc::alert(tr("Can’t perform this action when CamCOPS is locked"),
                      tr("Unlock first"));
        return;
    }
    // ========================================================================
    // Ways to act
    // ========================================================================
    if (m_p_menuproxy) {
        MenuWindow* pWindow = m_p_menuproxy->create(app);
        app.open(pWindow);
        return;
    }
    if (m_func) {
        m_func();
        return;
    }
    if (m_openable_widget_maker) {
        OpenableWidget* widget = m_openable_widget_maker(app);
        app.open(widget);
        return;
    }
    if (!m_task_tablename.isEmpty()) {
        SingleTaskMenu* pWindow = new SingleTaskMenu(m_task_tablename, app);
        app.open(pWindow);
        return;
    }
    if (!m_html.filename.isEmpty()) {
        HtmlInfoWindow* pWindow = new HtmlInfoWindow(
            app, m_html.title, m_html.filename, m_html.icon, m_html.fullscreen);
        app.open(pWindow);
        return;
    }
    qWarning() << "Menu item selected but no action specified:"
               << m_title;
}


bool MenuItem::isImplemented() const
{
    return m_implemented;
}


MenuItem& MenuItem::setImplemented(bool implemented)
{
    m_implemented = implemented;
    return *this;
}


MenuItem& MenuItem::setLabelOnly(bool label_only)
{
    m_label_only = label_only;
    return *this;
}


MenuItem& MenuItem::setNeedsPrivilege(bool needs_privilege)
{
    m_needs_privilege = needs_privilege;
    if (needs_privilege) {
        m_not_if_locked = true;  // just for safety!
    }
    return *this;
}


MenuItem& MenuItem::setNotIfLocked(bool not_if_locked)
{
    m_not_if_locked = not_if_locked;
    return *this;
}


MenuItem& MenuItem::setUnsupported(bool unsupported)
{
    m_unsupported = unsupported;
    return *this;
}


QDebug operator<<(QDebug debug, const MenuItem& m)
{
    debug.nospace() << "MenuItem @ " << Convert::prettyPointer(&m)
                    << " (m_title=" << m.m_title
                    << ", m_p_task=" << m.m_p_task
                    << ", m_p_patient=" << m.m_p_patient
                    << ")";
    return debug;
}


QDebug operator<<(QDebug debug, const MenuItem* m)
{
    debug << *m;
    return debug;
}
