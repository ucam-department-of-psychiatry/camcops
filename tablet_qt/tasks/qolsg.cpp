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

#include "qolsg.h"
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QPushButton>
#include "lib/graphicsfunc.h"
#include "lib/stringfunc.h"
#include "tasklib/taskfactory.h"
#include "widgets/openablewidget.h"
#include "widgets/screenlikegraphicsview.h"

// Table name
const QString QolSG::QOLSG_TABLENAME("qolsg");

// Fieldnames
const QString FN_CATEGORY_START_TIME("category_start_time");
const QString FN_CATEGORY_RESPONDED("category_responded");
const QString FN_CATEGORY_RESPONSE_TIME("category_response_time");
const QString FN_CATEGORY_CHOSEN("category_chosen");
const QString FN_GAMBLE_FIXED_OPTION("gamble_fixed_option");
const QString FN_GAMBLE_LOTTERY_OPTION_P("gamble_lottery_option_p");
const QString FN_GAMBLE_LOTTERY_OPTION_Q("gamble_lottery_option_q");
const QString FN_GAMBLE_LOTTERY_ON_LEFT("gamble_lottery_on_left");
const QString FN_GAMBLE_STARTING_P("gamble_starting_p");
const QString FN_GAMBLE_START_TIME("gamble_start_time");
const QString FN_GAMBLE_RESPONDED("gamble_responded");
const QString FN_GAMBLE_RESPONSE_TIME("gamble_response_time");
const QString FN_GAMBLE_P("gamble_p");
const QString FN_UTILITY("utility");

// Strings
const QString TX_UTILITY("Utility");
const QString TX_INITIAL_INSTRUCTION(
        "Quality of Life Standard Gamble\n\n\n"
        "Please choose the statement that best describes your current health "
        "state:");
const QString TX_CURRENT_STATE("Current state:");
const QString TX_DEAD("Dead");
const QString TX_HEALTHY("Healthy");
const QString TX_INDIFFERENT("Both wheels seem about equal to me now");
const QString TX_H_ABOVE_1("I am better than 100% healthy");
const QString TX_H_0_TO_1("I am somewhere from 0% to 100% healthy");
const QString TX_H_BELOW_0("My current state is worse than being dead");
const QString TX_LEFT("left");
const QString TX_RIGHT("right");
const QString TX_INSTRUCTION_PREFIX_2(
        "Suppose you are offered two alternatives, represented by the two "
        "wheels below.");
const QString TX_INSTRUCTION_MEDIUM(
        "The FIXEDSIDE wheel represents you remaining in your current state "
        "of health for the rest of your life.\n"
        "The LOTTERYSIDE wheel represents an experimental treatment. There is "
        "a chance that it will return you\nto full health for the rest of "
        "your life. However, there is also a chance that it will kill you "
        "instantly.");
const QString TX_INSTRUCTION_LOW(
        "The FIXEDSIDE wheel represents a poison that would kill you "
        "instantly.\nThe LOTTERYSIDE wheel represents an experimental "
        "treatment. There is a chance that it will return you to full\n"
        "health for the rest of your life. However, there is also a chance "
        "that you will remain in your current state\nof health for the rest "
        "of your life.");
const QString TX_INSTRUCTION_HIGH(
        "The FIXEDSIDE wheel represents a medicine that would give you normal "
        "full health for the rest of your life.\nThe LOTTERYSIDE wheel "
        "represents an experimental treatment. There is a chance that it will "
        "keep you in your current\nstate of health for the rest of your life. "
        "However, there is also a chance that it will kill you instantly.");
const QString TX_INSTRUCTION_SUFFIX(
        "Please drag the red pointer to adjust the chances on the LOTTERYSIDE "
        "wheel, until the two wheels seem\nEQUAL IN VALUE to you. Then press "
        "the green button.");

// Bits to replace in the string above:
const QString FIXEDSIDE("FIXEDSIDE");
const QString LOTTERYSIDE("LOTTERYSIDE");

// Graphics
const int SCENE_WIDTH = 1000;
const int SCENE_HEIGHT = 750;  // 4:3 aspect ratio
const QRectF SCENE_RECT(0, 0, SCENE_WIDTH, SCENE_HEIGHT);
const int BORDER_WIDTH_PX = 2;

// For the QColor objects below:
// (1) Do NOT do this:
//          const QColor EDGE_COLOUR = uiconst::RED;
//          const QColor EDGE_COLOUR(uiconst::RED);
//     ... because the object in the other compilation unit may not be initialized
//     when you need it.
//     http://stackoverflow.com/questions/211237/static-variables-initialisation-order
// (2) This is probably OK:
//          const QColor& EDGE_COLOUR = uiconst::RED;
// (3) But you might as well do this:
//          const QColor EDGE_COLOUR("red");
//     based on the standard names:
//          http://doc.qt.io/qt-5/qcolor.html#setNamedColor
//          https://www.w3.org/TR/SVG/types.html#ColorKeywords

const QColor EDGE_COLOUR("red");
const QColor SCENE_BACKGROUND("salmon");
const QColor BUTTON_BACKGROUND("blue");
const QColor TEXT_COLOUR("white");
const QColor BUTTON_PRESSED_BACKGROUND("olive");
const int TEXT_SIZE_PX = 15;
const int BUTTON_RADIUS = 5;
const int PADDING = 5;


void initializeQolSG(TaskFactory& factory)
{
    static TaskRegistrar<QolSG> registered(factory);
}


QolSG::QolSG(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, QOLSG_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addField(FN_CATEGORY_START_TIME, QVariant::DateTime);
    addField(FN_CATEGORY_RESPONDED, QVariant::Bool);
    addField(FN_CATEGORY_RESPONSE_TIME, QVariant::DateTime);
    addField(FN_CATEGORY_CHOSEN, QVariant::String);
    addField(FN_GAMBLE_FIXED_OPTION, QVariant::String);
    addField(FN_GAMBLE_LOTTERY_OPTION_P, QVariant::String);
    addField(FN_GAMBLE_LOTTERY_OPTION_Q, QVariant::String);
    addField(FN_GAMBLE_LOTTERY_ON_LEFT, QVariant::Bool);
    addField(FN_GAMBLE_STARTING_P, QVariant::Double);
    addField(FN_GAMBLE_START_TIME, QVariant::DateTime);
    addField(FN_GAMBLE_RESPONDED, QVariant::Bool);
    addField(FN_GAMBLE_RESPONSE_TIME, QVariant::DateTime);
    addField(FN_GAMBLE_P, QVariant::Double);
    addField(FN_UTILITY, QVariant::Double);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString QolSG::shortname() const
{
    return "QoL-SG";
}


QString QolSG::longname() const
{
    return tr("Quality of Life: Standard Gamble");
}


QString QolSG::menusubtitle() const
{
    return tr("Standard-gamble measure of quality of life.");
}


QString QolSG::infoFilenameStem() const
{
    return "qol";
}


// ============================================================================
// Instance info
// ============================================================================

bool QolSG::isComplete() const
{
    return !valueIsNull(FN_UTILITY);
}


QStringList QolSG::summary() const
{
    return QStringList{stringfunc::standardResult(TX_UTILITY,
                                                  prettyValue(FN_UTILITY, 3))};
}


QStringList QolSG::detail() const
{
    return completenessInfo() + recordSummaryLines();
}


OpenableWidget* QolSG::editor(bool read_only)
{
    m_scene = new QGraphicsScene(SCENE_RECT);
    m_scene->setBackgroundBrush(QBrush(SCENE_BACKGROUND)); // *** not working
    ScreenLikeGraphicsView* view = new ScreenLikeGraphicsView(m_scene);
    OpenableWidget* widget = new OpenableWidget();
    widget->setGraphicsViewAsOnlyContents(view);

    m_read_only = read_only;
    start();

    return widget;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

void QolSG::start()
{
    QPen pen(EDGE_COLOUR);
    pen.setWidth(BORDER_WIDTH_PX);
    QBrush rect_brush(BUTTON_BACKGROUND);
    m_scene->addRect(QRectF(0, 0, 25, 25), pen, rect_brush);
    m_scene->addRect(QRectF(200, 200, 100, 50), pen, rect_brush);
    m_scene->addRect(QRectF(975, 725, 25, 25), pen, rect_brush);

    graphicsfunc::ButtonAndProxy b = graphicsfunc::makeGraphicsTextButton(
                m_scene, QRectF(500, 500, 100, 200), PADDING,
                "Hello! I'm a <b>button</b> <strong>with</strong> long text",
                TEXT_SIZE_PX, TEXT_COLOUR,
                BUTTON_BACKGROUND, BUTTON_PRESSED_BACKGROUND,
                pen, BUTTON_RADIUS);
    connect(b.button, &QPushButton::clicked, this, &QolSG::testButtonClicked);
    Q_UNUSED(b);
}


// ============================================================================
// Signal handlers
// ============================================================================

void QolSG::testButtonClicked()
{
    qDebug() << Q_FUNC_INFO;
}
