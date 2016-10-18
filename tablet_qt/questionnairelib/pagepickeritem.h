#pragma once
#include <QString>


class PagePickerItem
{
    // An option presented by a PagePickerDialog.
public:
    enum PagePickerItemType {
        CompleteSelectable,
        IncompleteSelectable,
        BlockedByPrevious,
    };

    PagePickerItem(const QString& text, int page_number,
                   PagePickerItemType type);
    QString text() const;
    int pageNumber() const;
    PagePickerItemType type() const;
    bool selectable() const;
    QString iconFilename() const;
protected:
    QString m_text;
    int m_page_number;
    PagePickerItemType m_type;
};
