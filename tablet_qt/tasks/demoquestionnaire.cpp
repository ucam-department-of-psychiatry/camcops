#include "demoquestionnaire.h"
#include "tasklib/taskfactory.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/page.h"
#include "questionnairelib/element.h"
#include "questionnairelib/text.h"


DemoQuestionnaire::DemoQuestionnaire(const QSqlDatabase& db, int load_pk) :
    Task(db, "demoquestionnaire", false, false, false)
{
    addField("q1", QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


QString DemoQuestionnaire::shortname() const
{
    return "Demo";
}


QString DemoQuestionnaire::longname() const
{
    return "Demonstration task";
}


QString DemoQuestionnaire::menusubtitle() const
{
    return "Tutorial and illustration of questionnaire task elements";
}


bool DemoQuestionnaire::isComplete() const
{
    return true;
}


QString DemoQuestionnaire::getSummary() const
{
    return "summary! ***";
}


QString DemoQuestionnaire::getDetail() const
{
    return "detail! ***";
}


void DemoQuestionnaire::edit(CamcopsApp& app)
{
    qDebug() << "DemoQuestionnaire::edit()";
    QString longtext = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent "
        "sed cursus mauris. Ut vulputate felis quis dolor molestie convallis. "
        "Donec lectus diam, accumsan quis tortor at, congue laoreet augue. Ut "
        "mollis consectetur elit sit amet tincidunt. Vivamus facilisis, mi et "
        "eleifend ullamcorper, lorem metus faucibus ante, ut commodo urna "
        "neque bibendum magna. Lorem ipsum dolor sit amet, consectetur "
        "adipiscing elit. Praesent nec nisi ante. Sed vitae sem et eros "
        "elementum condimentum. Proin porttitor purus justo, sit amet "
        "vulputate velit imperdiet nec. Nam posuere ipsum id nunc accumsan "
        "tristique. Etiam pellentesque ornare tortor, a scelerisque dui "
        "accumsan ac. Ut tincidunt dolor ultrices, placerat urna nec, "
        "scelerisque mi."
    );
    QString url = "http://doc.qt.io/qt-5.7/richtext-html-subset.html";
    QString html = QString(
        "Text with embedded HTML markup, providing <b>bold</b>, "
        "<i>italic</i>, and others as per Qt rich text syntax at "
        "<a href=\"%1\">%1</a>."
    ).arg(url);
    PagePtr p1 = PagePtr((new Page({
        ElementPtr((new Text("normal text"))),
        ElementPtr((new Text("bold text"))->bold()),
        ElementPtr((new Text("italic text"))->italic()),
        ElementPtr((new Text(html))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text(longtext))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("big text"))->big()),
        ElementPtr((new Text("... was that enough to scroll "
                             "vertically?"))->bold()),
    }))->setTitle("Page 1"));
    Questionnaire* questionnaire = new Questionnaire(app, {p1});
    // ***
    questionnaire->open();
}


void initializeDemoQuestionnaire(TaskFactory& factory)
{
    static TaskRegistrar<DemoQuestionnaire> registered(factory);
}
