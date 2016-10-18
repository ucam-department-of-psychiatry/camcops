#include "pagepickeritem.h"
#include "common/uiconstants.h"


PagePickerItem::PagePickerItem(const QString& text, int page_number,
                               PagePickerItemType type):
    m_text(text),
    m_page_number(page_number),
    m_type(type)
{
}


QString PagePickerItem::text() const
{
    return m_text;
}


int PagePickerItem::pageNumber() const
{
    return m_page_number;
}


PagePickerItem::PagePickerItemType PagePickerItem::type() const
{
    return m_type;
}


bool PagePickerItem::selectable() const
{
    return m_type == PagePickerItemType::CompleteSelectable ||
           m_type == PagePickerItemType::IncompleteSelectable;
}


QString PagePickerItem::iconFilename() const
{
    switch (m_type) {
    case PagePickerItemType::CompleteSelectable:
        return UiConst::CBS_NEXT;
    case PagePickerItemType::IncompleteSelectable:
        return UiConst::ICON_WARNING;
    case PagePickerItemType::BlockedByPrevious:
    default:  // to prevent compiler warning
        return UiConst::ICON_STOP;
    }
}
