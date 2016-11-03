#pragma once
#include "menulib/menuwindow.h"
#include "questionnairelib/namevalueoptions.h"
#include "widgets/booleanwidget.h"

class QuElement;


class WidgetTestMenu : public MenuWindow
{
    Q_OBJECT
public:
    WidgetTestMenu(CamcopsApp& app);
protected:
    QVariant dummyGetter1() const;
    bool dummySetter1(const QVariant& value);
    QVariant dummyGetter2() const;
    bool dummySetter2(const QVariant& value);
    void dummyAction();
    void testQuestionnaireElement(QuElement* element);

    // ========================================================================
    // Endogenous Qt widgets
    // ========================================================================
    void testQLabel(bool expand);
    void testQPushButton(bool expand);

    // ========================================================================
    // Low-level widgets
    // ========================================================================
    void testAspectRatioPixmapLabel();
    void testBooleanWidget(BooleanWidget::Appearance appearance,
                           bool long_text);
    // Camera: use QuPhoto instead
    void testCanvasWidget();
    void testClickableLabel(bool long_text);
    void testClickableLabelWordWrapWide(bool long_text);
    // DiagnosticCodeSelector: use QuDiagnosticCode instead
    // FlowLayout: see testFlowLayoutContainer
    void testFlowLayoutContainer();
    // GrowingTextEdit: see QuTextEdit
    void testHorizontalLine();
    void testImageButton();
    void testLabelWordWrapWide(bool long_text);
    // OpenableWidget: part of main app framework instead
    // Spacer: see QuSpacer instead
    // TickSlider: see QuSlider instead
    void testVerticalLine();
    // VerticalScrollArea: not a widget, a scroll area

    // ========================================================================
    // Large-scale widgets
    // ========================================================================
    void testQuestionnaireHeader();

    // ========================================================================
    // Questionnaire element widgets
    // ========================================================================
    void testQuAudioPlayer();
    void testQuBoolean(bool as_text_button, bool long_text);
    void testQuButton();
    void testQuCanvas();
    void testQuCountdown();
    void testQuDateTime();
    void testQuDiagnosticCode();
    void testQuHeading();
    void testQuHorizontalLine();
    void testQuImage();
    void testQuLineEdit();
    void testQuLineEditDouble();
    void testQuLineEditInteger();
    void testQuMCQ(bool horizontal, bool long_text);
    void testQuMCQGrid(bool expand);
    void testQuMCQGridDouble(bool expand);
    void testQuMCQGridSingleBoolean(bool expand);
    void testQuMultipleResponse(bool horizontal, bool long_text);
    void testQuPhoto();
    void testQuPickerInline();
    void testQuPickerPopup();
    void testQuSlider(bool horizontal);
    void testQuSpacer();
    void testQuSpinBoxDouble();
    void testQuSpinBoxInteger();
    void testQuText();
    void testQuTextEdit();
    void testQuThermometer();

protected:
    FieldRefPtr m_fieldref_1;
    FieldRefPtr m_fieldref_2;
    QVariant m_dummy_value_1;
    QVariant m_dummy_value_2;
    NameValueOptions m_options_1;
    NameValueOptions m_options_2;
    NameValueOptions m_options_3;
};
