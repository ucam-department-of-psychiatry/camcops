#include "demoquestionnaire.h"
#include "tasklib/taskfactory.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qutext.h"


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
    QString longtext = (  // http://www.lipsum.com/
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

    // *** page 1 text, page 2 buttons
    QuPagePtr p1 = QuPagePtr((new QuPage({
        QuElementPtr((new QuText("normal text"))->addTag("tag1")),
        QuElementPtr((new QuText("bold text"))->bold()),
        QuElementPtr((new QuText("italic text"))->italic()),
        QuElementPtr(new QuText(html)),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText(longtext))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("... was that enough to scroll "
                                 "vertically?"))->bold()),
    }))->setTitle("Page 1: text "
                  "[With a long title: Lorem ipsum dolor sit amet, "
                  "consectetur adipiscing elit. Praesent sed cursus mauris. "
                  "Ut vulputate felis quis dolor molestie convallis.]"));

    QuPagePtr p2 = QuPagePtr((new QuPage({
    QuElementPtr(new QuButton(
        "Say hello",
        std::bind(&DemoQuestionnaire::callback_hello, this))),
    QuElementPtr(new QuButton(
        "Button with args ('foo')",
        std::bind(&DemoQuestionnaire::callback_arg, this, "foo"))),
    QuElementPtr(new QuButton(
        "Button with args ('bar')",
        std::bind(&DemoQuestionnaire::callback_arg, this, "bar"))),
    }))->setTitle("Page 2: buttons"));

    // ***

    Questionnaire* questionnaire = new Questionnaire(app, {p1, p2});
    questionnaire->open();
}


void initializeDemoQuestionnaire(TaskFactory& factory)
{
    static TaskRegistrar<DemoQuestionnaire> registered(factory);
}


void DemoQuestionnaire::callback_hello()
{
    alert("Hello!");
}


void DemoQuestionnaire::callback_arg(const QString& arg)
{
    alert("Function argument was: " + arg);
}
