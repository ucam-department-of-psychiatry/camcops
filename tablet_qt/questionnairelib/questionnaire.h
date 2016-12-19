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

#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include "common/aliases_camcops.h"
#include "common/uiconstants.h"  // for FontSize
#include "widgets/openablewidget.h"
#include "qupage.h"

class QVBoxLayout;
class QWidget;

class CamcopsApp;
class QuestionnaireHeader;


class Questionnaire : public OpenableWidget
{
    // Master class controlling a questionnaire.

    Q_OBJECT
public:
    Questionnaire(CamcopsApp& app);
    Questionnaire(CamcopsApp& app, const QList<QuPagePtr>& pages);
    Questionnaire(CamcopsApp& app, std::initializer_list<QuPagePtr> pages);

    virtual void build() override;
    bool event(QEvent* e) override;

    void setType(QuPage::PageType type);
    void addPage(const QuPagePtr& page);
    void setReadOnly(bool read_only = true);
    void setJumpAllowed(bool jump_allowed = true);
    void setWithinChain(bool within_chain = true);

    bool readOnly() const;
    int fontSizePt(UiConst::FontSize fontsize) const;

    void openSubWidget(OpenableWidget* widget);
    CamcopsApp& app() const;
    QString getSubstitutedCss(const QString& filename) const;
    QuPage* currentPagePtr() const;
    void setVisibleByTag(const QString& tag, bool visible,
                         bool current_page = true);
    QList<QuElement*> getElementsByTag(const QString& tag,
                                       bool current_page = true);
    QuElement* getFirstElementByTag(const QString& tag,
                                    bool current_page = true);
    QList<QuPage*> getPages(bool current_page);
protected:
    void commonConstructor();
    int currentPageNumOneBased() const;
    int nPages() const;
    void doFinish();
    void doCancel();
    void pageClosing();
protected slots:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
    void resetButtons();
    void goToPage(int index_zero_based);
    void debugLayout();
signals:
    void editStarted();
    void editFinished(bool aborted);
    void pageAboutToOpen();  // about to display page
    void cancelled();  // failure/cancel
    void completed();  // success/OK
    // and finished() is emitted with either; see OpenableWidget

protected:
    CamcopsApp& m_app;
    QList<QuPagePtr> m_pages;
    QuPage::PageType m_type;
    bool m_read_only;
    bool m_jump_allowed;
    bool m_within_chain;

    bool m_built;
    QPointer<QVBoxLayout> m_outer_layout;
    QPointer<QWidget> m_background_widget;
    QPointer<QVBoxLayout> m_mainlayout;
    QPointer<QuestionnaireHeader> m_p_header;
    QPointer<QVBoxLayout> m_p_content;
    int m_current_pagenum_zero_based;
};
