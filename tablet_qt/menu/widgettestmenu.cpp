#include "widgettestmenu.h"
#include <QPushButton>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "diagnosis/icd10.h"
#include "lib/debugfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quaudioplayer.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qucanvas.h"
#include "questionnairelib/qucountdown.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/qudiagnosticcode.h"
#include "questionnairelib/questionnaireheader.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qumcqgriddouble.h"
#include "questionnairelib/qumcqgridsingleboolean.h"
#include "questionnairelib/qumultipleresponse.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/qupickerinline.h"
#include "questionnairelib/qupickerpopup.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/quspinboxdouble.h"
#include "questionnairelib/quspinboxinteger.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quthermometer.h"
#include "widgets/aspectratiopixmaplabel.h"
#include "widgets/canvaswidget.h"
#include "widgets/clickablelabel.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/flowlayout.h"
#include "widgets/flowlayoutcontainer.h"
#include "widgets/horizontalline.h"
#include "widgets/imagebutton.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/verticalline.h"


WidgetTestMenu::WidgetTestMenu(CamcopsApp& app)
    : MenuWindow(app, tr("Widget tests"), "")
{
    FieldRef::GetterFunction getter1 = std::bind(&WidgetTestMenu::dummyGetter1,
                                                 this);
    FieldRef::SetterFunction setter1 = std::bind(&WidgetTestMenu::dummySetter1,
                                                 this, std::placeholders::_1);
    FieldRef::GetterFunction getter2 = std::bind(&WidgetTestMenu::dummyGetter2,
                                                 this);
    FieldRef::SetterFunction setter2 = std::bind(&WidgetTestMenu::dummySetter2,
                                                 this, std::placeholders::_1);
    bool mandatory = true;
    m_fieldref_1 = FieldRefPtr(new FieldRef(getter1, setter1, mandatory));
    m_fieldref_2 = FieldRefPtr(new FieldRef(getter2, setter2, mandatory));

    m_options_1.addItem(NameValuePair("Option A1", 1));
    m_options_1.addItem(NameValuePair("Option A2", 2));
    m_options_1.addItem(NameValuePair("Option A3", 3));

    m_options_2.addItem(NameValuePair("Option B1", 1));
    m_options_2.addItem(NameValuePair("Option B2", 2));

    m_options_3.addItem(NameValuePair("Option C1", 1));
    m_options_3.addItem(NameValuePair("Option C2 " + UiConst::LOREM_IPSUM_1, 2));
    m_options_3.addItem(NameValuePair("Option C3", 3));

    QSizePolicy fixed_fixed(QSizePolicy::Fixed, QSizePolicy::Fixed);
    QSizePolicy expand_expand(QSizePolicy::Expanding, QSizePolicy::Expanding);
    QSizePolicy expand_fixed_hfw = UiFunc::expandingFixedHFWPolicy();
    // UiFunc::horizExpandingPreferredHFWPolicy();

    m_items = {
        MenuItem(tr("Qt widgets")).setLabelOnly(),
        MenuItem(tr("QLabel (size policy = Fixed, Fixed / short / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           fixed_fixed, false, false)),
        MenuItem(tr("QLabel (size policy = Fixed, Fixed / long / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           fixed_fixed, true, false)),
        MenuItem(tr("QLabel (size policy = Fixed, Fixed / long / word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           fixed_fixed, true, true)),
        MenuItem(tr("QLabel (size policy = Expanding, Expanding / short / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_expand, false, false)),
        MenuItem(tr("QLabel (size policy = Expanding, Expanding / long / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_expand, true, false)),
        MenuItem(tr("QLabel (size policy = Expanding, Expanding / long / word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_expand, true, true)),
        MenuItem(tr("QLabel (size policy = Expanding, Fixed, heightForWidth / short / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_fixed_hfw, false, false)),
        MenuItem(tr("QLabel (size policy = Expanding, Fixed, heightForWidth / long / no word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_fixed_hfw, true, false)),
        MenuItem(tr("QLabel (size policy = Expanding, Fixed, heightForWidth / long / word wrap)"),
                 std::bind(&WidgetTestMenu::testQLabel, this,
                           expand_fixed_hfw, true, true)),
        MenuItem(tr("QPushButton (size policy = Fixed, Fixed)"),
                 std::bind(&WidgetTestMenu::testQPushButton, this, fixed_fixed)),
        MenuItem(tr("QPushButton (size policy = Expanding, Expanding)"),
                 std::bind(&WidgetTestMenu::testQPushButton, this, expand_expand)),

        MenuItem(tr("Low-level widgets")).setLabelOnly(),
        MenuItem(tr("AspectRatioPixmapLabel"),
                 std::bind(&WidgetTestMenu::testAspectRatioPixmapLabel, this)),
        MenuItem(tr("BooleanWidget (appearance=CheckBlack)"),
                 std::bind(&WidgetTestMenu::testBooleanWidget, this,
                           BooleanWidget::Appearance::CheckBlack, false)),
        MenuItem(tr("BooleanWidget (appearance=CheckRed)"),
                 std::bind(&WidgetTestMenu::testBooleanWidget, this,
                           BooleanWidget::Appearance::CheckRed, false)),
        MenuItem(tr("BooleanWidget (appearance=Radio)"),
                 std::bind(&WidgetTestMenu::testBooleanWidget, this,
                           BooleanWidget::Appearance::Radio, false)),
        MenuItem(tr("BooleanWidget (appearance=Text, short text)"),
                 std::bind(&WidgetTestMenu::testBooleanWidget, this,
                           BooleanWidget::Appearance::Text, false)),
        MenuItem(tr("BooleanWidget (appearance=Text, long text)"),
                 std::bind(&WidgetTestMenu::testBooleanWidget, this,
                           BooleanWidget::Appearance::Text, true)),
        MenuItem(tr("CanvasWidget"),
                 std::bind(&WidgetTestMenu::testCanvasWidget, this)),
        MenuItem(tr("ClickableLabel (short text)"),
                 std::bind(&WidgetTestMenu::testClickableLabel, this, false)),
        MenuItem(tr("ClickableLabel (long text)"),
                 std::bind(&WidgetTestMenu::testClickableLabel, this, true)),
        MenuItem(tr("ClickableLabelWordWrapWide (short text)"),
                 std::bind(&WidgetTestMenu::testClickableLabelWordWrapWide, this, false)),
        MenuItem(tr("ClickableLabelWordWrapWide (long text)"),
                 std::bind(&WidgetTestMenu::testClickableLabelWordWrapWide, this, true)),
        MenuItem(tr("FlowLayoutContainer (short text)"),
                 std::bind(&WidgetTestMenu::testFlowLayoutContainer, this, false)),
        MenuItem(tr("FlowLayoutContainer (long text)"),
                 std::bind(&WidgetTestMenu::testFlowLayoutContainer, this, true)),
        MenuItem(tr("HorizontalLine"),
                 std::bind(&WidgetTestMenu::testHorizontalLine, this)),
        MenuItem(tr("ImageButton"),
                 std::bind(&WidgetTestMenu::testImageButton, this)),
        MenuItem(tr("LabelWordWrapWide (short text)"),
                 std::bind(&WidgetTestMenu::testLabelWordWrapWide, this, false)),
        MenuItem(tr("LabelWordWrapWide (long text)"),
                 std::bind(&WidgetTestMenu::testLabelWordWrapWide, this, true)),
        MenuItem(tr("VerticalLine"),
                 std::bind(&WidgetTestMenu::testVerticalLine, this)),

        MenuItem(tr("Large-scale widgets")).setLabelOnly(),
        MenuItem(tr("QuestionnaireHeader"),
                 std::bind(&WidgetTestMenu::testQuestionnaireHeader, this)),

        MenuItem(tr("Questionnaire element widgets")).setLabelOnly(),
        MenuItem(tr("QuAudioPlayer"),
                 std::bind(&WidgetTestMenu::testQuAudioPlayer, this)),
        MenuItem(tr("QuBoolean (as_text_button=false, short text)"),
                 std::bind(&WidgetTestMenu::testQuBoolean, this, false, false)),
        MenuItem(tr("QuBoolean (as_text_button=false, long text)"),
                 std::bind(&WidgetTestMenu::testQuBoolean, this, false, true)),
        MenuItem(tr("QuBoolean (as_text_button=true, short text)"),
                 std::bind(&WidgetTestMenu::testQuBoolean, this, true, false)),
        MenuItem(tr("QuBoolean (as_text_button=true, long text)"),
                 std::bind(&WidgetTestMenu::testQuBoolean, this, true, true)),
        MenuItem(tr("QuButton"),
                 std::bind(&WidgetTestMenu::testQuButton, this)),
        MenuItem(tr("QuCanvas"),
                 std::bind(&WidgetTestMenu::testQuCanvas, this)),
        MenuItem(tr("QuCountdown"),
                 std::bind(&WidgetTestMenu::testQuCountdown, this)),
        MenuItem(tr("QuDateTime"),
                 std::bind(&WidgetTestMenu::testQuDateTime, this)),
        MenuItem(tr("QuDiagnosticCode (NB iffy display if you select one!)"),
                 std::bind(&WidgetTestMenu::testQuDiagnosticCode, this)),
        MenuItem(tr("QuHeading"),
                 std::bind(&WidgetTestMenu::testQuHeading, this)),
        MenuItem(tr("QuHorizontalLine"),
                 std::bind(&WidgetTestMenu::testQuHorizontalLine, this)),
        MenuItem(tr("QuImage"),
                 std::bind(&WidgetTestMenu::testQuImage, this)),
        MenuItem(tr("QuLineEdit"),
                 std::bind(&WidgetTestMenu::testQuLineEdit, this)),
        MenuItem(tr("QuLineEditDouble"),
                 std::bind(&WidgetTestMenu::testQuLineEditDouble, this)),
        MenuItem(tr("QuLineEditInteger"),
                 std::bind(&WidgetTestMenu::testQuLineEditInteger, this)),
        MenuItem(tr("QuMCQ (horizontal=false, short text)"),
                 std::bind(&WidgetTestMenu::testQuMCQ, this, false, false)),
        MenuItem(tr("QuMCQ (horizontal=false, long text)"),
                 std::bind(&WidgetTestMenu::testQuMCQ, this, false, true)),
        MenuItem(tr("QuMCQ (horizontal=true, short text)"),
                 std::bind(&WidgetTestMenu::testQuMCQ, this, true, false)),
        MenuItem(tr("QuMCQ (horizontal=true, long text)"),
                 std::bind(&WidgetTestMenu::testQuMCQ, this, true, true)),
        MenuItem(tr("QuMCQGrid (expand=false)"),
                 std::bind(&WidgetTestMenu::testQuMCQGrid, this, false)),
        MenuItem(tr("QuMCQGrid (expand=true)"),
                 std::bind(&WidgetTestMenu::testQuMCQGrid, this, true)),
        MenuItem(tr("QuMCQGridDouble (expand=false)"),
                 std::bind(&WidgetTestMenu::testQuMCQGridDouble, this, false)),
        MenuItem(tr("QuMCQGridDouble (expand=true)"),
                 std::bind(&WidgetTestMenu::testQuMCQGridDouble, this, true)),
        MenuItem(tr("QuMCQGridSingleBoolean (expand=false)"),
                 std::bind(&WidgetTestMenu::testQuMCQGridSingleBoolean, this, false)),
        MenuItem(tr("QuMCQGridSingleBoolean (expand=true)"),
                 std::bind(&WidgetTestMenu::testQuMCQGridSingleBoolean, this, true)),
        MenuItem(tr("QuMultipleResponse (horizontal=false, short text)"),
                 std::bind(&WidgetTestMenu::testQuMultipleResponse, this, false, false)),
        MenuItem(tr("QuMultipleResponse (horizontal=false, long text)"),
                 std::bind(&WidgetTestMenu::testQuMultipleResponse, this, false, true)),
        MenuItem(tr("QuMultipleResponse (horizontal=true, short text)"),
                 std::bind(&WidgetTestMenu::testQuMultipleResponse, this, true, false)),
        MenuItem(tr("QuMultipleResponse (horizontal=true, long text)"),
                 std::bind(&WidgetTestMenu::testQuMultipleResponse, this, true, true)),
        MenuItem(tr("QuPhoto"),
                 std::bind(&WidgetTestMenu::testQuPhoto, this)),
        MenuItem(tr("QuPickerInline"),
                 std::bind(&WidgetTestMenu::testQuPickerInline, this)),
        MenuItem(tr("QuPickerPopup"),
                 std::bind(&WidgetTestMenu::testQuPickerPopup, this)),
        MenuItem(tr("QuSlider (horizontal=false)"),
                 std::bind(&WidgetTestMenu::testQuSlider, this, false)),
        MenuItem(tr("QuSlider (horizontal=true)"),
                 std::bind(&WidgetTestMenu::testQuSlider, this, true)),
        MenuItem(tr("QuSpacer"),
                 std::bind(&WidgetTestMenu::testQuSpacer, this)),
        MenuItem(tr("QuSpinBoxDouble"),
                 std::bind(&WidgetTestMenu::testQuSpinBoxDouble, this)),
        MenuItem(tr("QuSpinBoxInteger"),
                 std::bind(&WidgetTestMenu::testQuSpinBoxInteger, this)),
        MenuItem(tr("QuText"),
                 std::bind(&WidgetTestMenu::testQuText, this)),
        MenuItem(tr("QuTextEdit"),
                 std::bind(&WidgetTestMenu::testQuTextEdit, this)),
        MenuItem(tr("QuThermometer"),
                 std::bind(&WidgetTestMenu::testQuThermometer, this)),
    };
}


QVariant WidgetTestMenu::dummyGetter1() const
{
    return m_dummy_value_1;
}


bool WidgetTestMenu::dummySetter1(const QVariant& value)
{
    bool changed = (value != m_dummy_value_1);
    if (changed) {
        m_dummy_value_1 = value;
    }
    return changed;
}


QVariant WidgetTestMenu::dummyGetter2() const
{
    return m_dummy_value_2;
}


bool WidgetTestMenu::dummySetter2(const QVariant& value)
{
    bool changed = (value != m_dummy_value_2);
    if (changed) {
        m_dummy_value_2 = value;
    }
    return changed;
}


void WidgetTestMenu::dummyAction()
{
    UiFunc::alert("Action!");
}


void WidgetTestMenu::testQuestionnaireElement(QuElement* element)
{
    Questionnaire questionnaire(m_app);
    QWidget* widget = element->widget(&questionnaire);
    widget->setStyleSheet(
                m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_QUESTIONNAIRE));
    DebugFunc::debugWidget(widget, false, false);
}


// ============================================================================
// Qt widgets
// ============================================================================

void WidgetTestMenu::testQLabel(const QSizePolicy& policy,
                                bool long_text, bool word_wrap)
{
    QLabel* widget = new QLabel(long_text ? UiConst::LOREM_IPSUM_1 : "Hello");
    widget->setWordWrap(word_wrap);
    widget->setSizePolicy(policy);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testQPushButton(const QSizePolicy& policy)
{
    QPushButton* widget = new QPushButton("Hello");
    widget->setSizePolicy(policy);
    // http://stackoverflow.com/questions/21367260/qt-making-a-qpushbutton-fill-layout-cell
    connect(widget, &QPushButton::clicked,
            this, &WidgetTestMenu::dummyAction);
    DebugFunc::debugWidget(widget);
}


// ============================================================================
// Low-level widgets
// ============================================================================

void WidgetTestMenu::testAspectRatioPixmapLabel()
{
    AspectRatioPixmapLabel* widget = new AspectRatioPixmapLabel();
    QPixmap pixmap = UiFunc::getPixmap(UiFunc::iconFilename(UiConst::ICON_CAMCOPS));
    widget->setPixmap(pixmap);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testBooleanWidget(BooleanWidget::Appearance appearance,
                                       bool long_text)
{
    BooleanWidget* widget = new BooleanWidget();
    bool big = true;
    bool as_text_button = (appearance == BooleanWidget::Appearance::Text);
    widget->setAppearance(appearance);
    widget->setSize(big);
    widget->setValue(true, true);
    if (as_text_button) {
        widget->setText(long_text ? UiConst::LOREM_IPSUM_2 : "BooleanWidget");
    }
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testCanvasWidget()
{
    QSize size(200, 200);
    CanvasWidget* widget = new CanvasWidget(size);
    QImage img(size, QImage::Format_RGB32);
    widget->setImage(img);
    widget->clear(Qt::white);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testClickableLabel(bool long_text)
{
    QString text = long_text ? UiConst::LOREM_IPSUM_1 : "Text";
    ClickableLabel* widget = new ClickableLabel(text);
    connect(widget, &QAbstractButton::clicked,
            this, &WidgetTestMenu::dummyAction);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testClickableLabelWordWrapWide(bool long_text)
{
    QString text = long_text ? UiConst::LOREM_IPSUM_1 : "Text";
    ClickableLabelWordWrapWide* widget = new ClickableLabelWordWrapWide(text);
    connect(widget, &QAbstractButton::clicked,
            this, &WidgetTestMenu::dummyAction);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testFlowLayoutContainer(bool long_text)
{
    FlowLayout* layout = new FlowLayout();
    layout->addWidget(new LabelWordWrapWide("Option Z1"));
    QString option2 = long_text ? "Option Z2 " + UiConst::LOREM_IPSUM_2
                                : "Option Z2";
    layout->addWidget(new LabelWordWrapWide(option2));
    layout->addWidget(new LabelWordWrapWide("Option Z3"));
    FlowLayoutContainer* widget = new FlowLayoutContainer();
    widget->setLayout(layout);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testHorizontalLine()
{
    const int width = 4;
    HorizontalLine* widget = new HorizontalLine(width);
    widget->setStyleSheet("background-color: black;");
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testImageButton()
{
    ImageButton* widget;
    widget = new ImageButton(UiConst::CBS_ADD);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testLabelWordWrapWide(bool long_text)
{
    QString text = long_text ? UiConst::LOREM_IPSUM_1 : "Text";
    LabelWordWrapWide* widget = new LabelWordWrapWide(text);
    DebugFunc::debugWidget(widget);
}


void WidgetTestMenu::testVerticalLine()
{
    const int width = 4;
    VerticalLine* widget = new VerticalLine(width);
    widget->setStyleSheet("background-color: black;");
    DebugFunc::debugWidget(widget);
}


// ============================================================================
// Large-scale widgets
// ============================================================================

void WidgetTestMenu::testQuestionnaireHeader()
{
    QuestionnaireHeader* widget = new QuestionnaireHeader(
                nullptr, "Title text, quite long",
                false, true, false, CssConst::QUESTIONNAIRE_BACKGROUND_CONFIG);
    widget->setStyleSheet(m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_QUESTIONNAIRE));
    DebugFunc::debugWidget(widget);
}


// ============================================================================
// Questionnaire element widgets
// ============================================================================

void WidgetTestMenu::testQuAudioPlayer()
{
    QuAudioPlayer element(UiConst::DEMO_SOUND_URL);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuBoolean(bool as_text_button, bool long_text)
{
    QString text = long_text ? UiConst::LOREM_IPSUM_1 : "QuBoolean";
    QuBoolean element(text, m_fieldref_1);
    element.setAsTextButton(as_text_button);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuButton()
{
    QuButton element("QuButton", std::bind(&WidgetTestMenu::dummyAction, this));
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuCanvas()
{
    QuCanvas element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuCountdown()
{
    const int time_s = 10;
    QuCountdown element(time_s);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuDateTime()
{
    QuDateTime element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuDiagnosticCode()
{
    QSharedPointer<Icd10> icd10 = QSharedPointer<Icd10>(new Icd10(m_app));
    QuDiagnosticCode element(icd10, m_fieldref_1, m_fieldref_2);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuHeading()
{
    QuHeading element("Heading");
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuHorizontalLine()
{
    QuHorizontalLine element;
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuImage()
{
    QuImage element(UiFunc::iconFilename(UiConst::ICON_CAMCOPS));
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuLineEdit()
{
    QuLineEdit element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuLineEditDouble()
{
    QuLineEditDouble element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuLineEditInteger()
{
    QuLineEditInteger element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuMCQ(bool horizontal, bool long_text)
{
    QuMCQ element(m_fieldref_1, long_text ? m_options_3 : m_options_1);
    element.setHorizontal(horizontal);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuMCQGrid(bool expand)
{
    QList<QuestionWithOneField> question_field_pairs{
        QuestionWithOneField(m_fieldref_1, "Question 1"),
        QuestionWithOneField(m_fieldref_2, "Question 2 " + UiConst::LOREM_IPSUM_1),
    };
    QuMCQGrid element(question_field_pairs, m_options_1);
    element.setExpand(expand);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuMCQGridDouble(bool expand)
{
    QList<QuestionWithTwoFields> question_field_pairs{
        QuestionWithTwoFields("Question 1", m_fieldref_1, m_fieldref_2),
        QuestionWithTwoFields("Question 2 " + UiConst::LOREM_IPSUM_1,
                              m_fieldref_1, m_fieldref_2),
    };
    QuMCQGridDouble element(question_field_pairs, m_options_1, m_options_2);
    element.setExpand(expand);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuMCQGridSingleBoolean(bool expand)
{
    QList<QuestionWithTwoFields> question_field_pairs{
        QuestionWithTwoFields("Question 1", m_fieldref_1, m_fieldref_2),
        QuestionWithTwoFields("Question 2 " + UiConst::LOREM_IPSUM_1,
                              m_fieldref_1, m_fieldref_2),
    };
    QuMCQGridSingleBoolean element(question_field_pairs,
                                   m_options_1, "boolean");
    element.setExpand(expand);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuMultipleResponse(bool horizontal, bool long_text)
{
    QList<QuestionWithOneField> question_field_pairs{
        QuestionWithOneField(m_fieldref_1, "Question 1"),
        QuestionWithOneField(m_fieldref_2, long_text ? UiConst::LOREM_IPSUM_1
                                                     : "Question 2"),
    };
    QuMultipleResponse element(question_field_pairs);
    element.setHorizontal(horizontal);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuPhoto()
{
    QuPhoto element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuPickerInline()
{
    QuPickerInline element(m_fieldref_1, m_options_3);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuPickerPopup()
{
    QuPickerPopup element(m_fieldref_1, m_options_3);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuSlider(bool horizontal)
{
    QuSlider element(m_fieldref_1, 0, 10, 1);
    element.setHorizontal(horizontal);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuSpacer()
{
    QuSpacer element;
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuSpinBoxDouble()
{
    QuSpinBoxDouble element(m_fieldref_1, 0.0, 10.0, 2);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuSpinBoxInteger()
{
    QuSpinBoxInteger element(m_fieldref_1, 0, 10);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuText()
{
    QuText element("text");
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuTextEdit()
{
    QuTextEdit element(m_fieldref_1);
    testQuestionnaireElement(&element);
}


void WidgetTestMenu::testQuThermometer()
{
    QList<QuThermometerItem> thermometer_items;
    for (int i = 0; i <= 10; ++i) {
        QString text = QString::number(i);
        QuThermometerItem item(
            UiFunc::resourceFilename(
                        QString("distressthermometer/dt_sel_%1.png").arg(i)),
            UiFunc::resourceFilename(
                        QString("distressthermometer/dt_unsel_%1.png").arg(i)),
            text,
            i
        );
        thermometer_items.append(item);
    }
    QuThermometer element(m_fieldref_1, thermometer_items);
    element.setRescale(true, 0.4);
    testQuestionnaireElement(&element);
}
