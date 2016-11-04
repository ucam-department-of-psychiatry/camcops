#pragma once
#include <QDialog>
#include <QList>
#include "questionnairelib/pagepickeritem.h"

using PagePickerItemList = QList<PagePickerItem>;


class PagePickerDialog : public QDialog
{
    // Choose pages for a Questionnaire.
    // Displays pages that you may be unable to choose, as well.
    Q_OBJECT
public:
    PagePickerDialog(QWidget* parent, const PagePickerItemList& pages,
                     const QString& title = "");
    virtual int choose(int* new_page_number);
    virtual bool event(QEvent* e) override;
protected slots:
    void itemClicked(int item_index);
protected:
    PagePickerItemList m_pages;
    QString m_title;
    int* m_new_page_number;
};
