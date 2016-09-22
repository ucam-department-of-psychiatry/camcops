#pragma once
#include <QString>


struct HtmlMenuItem
{
    // Exists only to improve polymorphic constructor of MenuItem
public:
    HtmlMenuItem(const QString& title = "", const QString& filename = "",
                 const QString& icon = "", bool fullscreen = false) :
        title(title),
        filename(filename),
        icon(icon),
        fullscreen(fullscreen)
    {}
public:
    // These are the title/icon shown on the HTML page, not the menu
    QString title;
    QString filename;
    QString icon;
    bool fullscreen;
};
