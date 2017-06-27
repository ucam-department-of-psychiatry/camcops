/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "dynamicquestionnaire.h"
#include <QDebug>
#include "lib/uifunc.h"


DynamicQuestionnaire::DynamicQuestionnaire(
        CamcopsApp& app,
        const MakePageFn& make_page_fn,
        const MorePagesToGoFn& more_pages_to_go_fn) :
    Questionnaire(app),
    m_make_page_fn(make_page_fn),
    m_more_pages_to_go_fn(more_pages_to_go_fn)
{
    Q_ASSERT(m_current_page_index == 0);
    QuPagePtr first_page = m_make_page_fn(m_current_page_index);
    if (!first_page) {
        uifunc::stopApp("Dynamic questionnaire created but caller refuses to "
                        "supply first page");
    }
    m_pages.append(first_page);
}


bool DynamicQuestionnaire::morePagesToGo() const
{
    int current_qnum = currentPageIndex();
    return m_more_pages_to_go_fn(current_qnum);
}


void DynamicQuestionnaire::addPage(const QuPagePtr& page)
{
    Q_UNUSED(page);
    uifunc::stopApp("Don't call addPage() on a DynamicQuestionnaire!");
}


void DynamicQuestionnaire::deletePage(int index)
{
    Q_UNUSED(index);
    uifunc::stopApp("Don't call deletePage() on a DynamicQuestionnaire!");
}


void DynamicQuestionnaire::goToPage(int index, bool allow_refresh)
{
    if (index < 0 || index >= nPages()) {
        qWarning() << Q_FUNC_INFO << "Invalid index:" << index;
        return;
    }
    if (index == m_current_page_index && !allow_refresh) {
        qDebug() << "Page" << index <<
                    "(zero-based index) already selected";
        return;
    }
    pageClosing();
    m_current_page_index = index;

    // Now the bit that's different for DynamicQuestionnaire:
    while (m_pages.length() > index + 1) {
        m_pages.removeLast();
    }

    // Back to Questionnaire behaviour:
    build();
}


void DynamicQuestionnaire::processNextClicked()
{
    // As per Questionnaire:
    QuPage* page = currentPagePtr();
    if (!page || (!readOnly() && (page->progressBlocked() ||
                                  page->missingInput()))) {
        // Can't progress
        return;
    }

    // Different:
    Q_ASSERT(m_current_page_index == m_pages.length() - 1);
    int next_qnum = m_current_page_index + 1;
    QuPagePtr new_dynamic_page = m_make_page_fn(next_qnum);
    if (!new_dynamic_page) {
        qWarning()
                << Q_FUNC_INFO
                << "Miscalculation: we have offered a Next button but the "
                   "task wants to finish, so we should have offered a Finish "
                   "button; this implies the task has got its "
                   "'more_pages_to_go_fn' function wrong";
        doFinish();
        return;
    }
    m_pages.append(new_dynamic_page);
    goToPage(next_qnum);
}
