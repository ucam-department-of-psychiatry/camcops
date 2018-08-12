/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_OPTIONS

#include "testmenu.h"
#include <QAbstractButton>
#include <QCoreApplication>
#include <QMediaPlayer>
#include <QProgressDialog>
#include <QPushButton>
#include <QThread>
#include "common/platform.h"
#include "core/networkmanager.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "dialogs/scrollmessagebox.h"
#include "lib/convert.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "lib/soundfunc.h"
#include "maths/ccrandom.h"
#include "maths/eigenfunc.h"
#include "maths/logisticdescriptives.h"
#include "maths/logisticregression.h"
#include "maths/mathfunc.h"
#include "menulib/menuitem.h"
#include "menu/widgettestmenu.h"
#include "qobjects/slownonguifunctioncaller.h"
#include "tasklib/taskfactory.h"  // for TaskPtr
#include "tasks/demoquestionnaire.h"
#include "tasks/phq9.h"
#include "whisker/whiskerinboundmessage.h"
#include "whisker/whiskermanager.h"

const int EXPENSIVE_FUNCTION_DURATION_MS = 5000;

// ----------------------------------------------------------------------------
// Constants for Whisker test task
// ----------------------------------------------------------------------------
// Display, document
const QString main_display("main");
const QString second_display("virtualdisplay");
const QString doc("doc");
// Some demo objects
const QString text_obj = "objtext";
const QString bmp_obj_1("objbitmap1");
const QString bmp_obj_2("objbitmap2");
const QString line_obj("objline");
const QString arc_obj("objarc");
const QString bezier_obj("objbez");
const QString chord_obj("objchord");
const QString ellipse_obj("names_are_unimportant");
const QString pie_obj("objpie");
const QString polygon_obj_1("objpoly1");
const QString polygon_obj_2("objpoly2");
const QString rectangle_obj("objrect");
const QString roundrect_obj("objrr");
const QString camcogquadpattern_obj("camcogquadpattern");
const QString video_obj_1("vid1");
const QString video_obj_2("vid2");
const QString video_obj_both("vidboth");
// Test events.
const QString background_event("background");
const QString event_bmp_1("Coffee");
const QString event_bmp_2("Other thing");
const QString event_ellipse("Ellipse");
const QString event_roundrect("RoundRect");
const QString event_rectangle("Rectangle");
// const QString event_text("Text");
const QString event_polygon_1("Polygon_1");
const QString event_polygon_2("Polygon_2");
const QString event_chord("Chord");
const QString event_pie("Pie");
const QString event_camcogquadpattern("camcogquadpattern");
const QString suffix_event_clicked(" clicked");
const QString suffix_event_unclicked(" mouseup");
const QString suffix_event_touched(" touched");
const QString suffix_event_released(" released");
// const QString suffix_event_double_clicked(" double-clicked");
const QString suffix_event_mouse_moved(" mouse-moved");
const QString suffix_event_touch_moved(" touch-moved");
const QString event_video_1_touched("vid1touched");
const QString event_video_2_touched("vid2touched");
const QString suffix_event_video_play("play");
const QString suffix_event_video_pause("pause");
const QString suffix_event_video_stop("stop");
const QString suffix_event_video_back("back");
const QString suffix_event_video_fwd("fwd");
// Timings
const int FIVE_SEC = 5000;


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app, tr("CamCOPS self-tests"),
                 uifunc::iconFilename(uiconst::CBS_SPANNER)),
      m_player(nullptr)
{
    const QString spanner(uifunc::iconFilename(uiconst::CBS_SPANNER));
    m_items = {
        MenuItem(tr("User testing")).setLabelOnly(),
        MenuItem(
            tr("Test sound"),
            std::bind(&TestMenu::testSound, this)
        ).setNotIfLocked(),
        MenuItem(tr("Developer testing")).setLabelOnly(),
        MenuItem(
            tr("Test debug console"),
            std::bind(&TestMenu::testDebugConsole, this),
            spanner
        ),
        MenuItem(
            tr("Test network (HTTP)"),
            std::bind(&TestMenu::testHttp, this),
            spanner
        ).setNotIfLocked(),
        MenuItem(
            tr("Test network (HTTPS/SSL)"),
            std::bind(&TestMenu::testHttps, this),
            spanner
        ).setNotIfLocked(),
#ifdef DEBUG_OPTIONS
        MenuItem(
            tr("Test PHQ9 creation (nothing is saved)"),
            std::bind(&TestMenu::testPhq9Creation, this),
            spanner
        ).setNotIfLocked(),
        MenuItem(
            tr("Test ICD-10 code set creation (nothing is saved)"),
            std::bind(&TestMenu::testIcd10CodeSetCreation, this),
            spanner
        ),
        MenuItem(
            tr("Test ICD-9-CM code set creation (nothing is saved)"),
            std::bind(&TestMenu::testIcd9cmCodeSetCreation, this),
            spanner
        ),
#endif
        MenuItem(
            tr("Test HTML display (not fullscreen)"),
            HtmlMenuItem("Example HTML: this window should NOT be full-screen",
                         uifunc::resourceFilename("camcops/html/test.html"),
                         "", false),
            spanner
        ),
        MenuItem(
            tr("Test HTML display, and fullscreen display"),
            HtmlMenuItem("Example HTML: this window should be full-screen",
                         uifunc::resourceFilename("camcops/html/test.html"),
                         "", true),
            spanner
        ),
        MenuItem(
            tr("Enter fullscreen"),
            std::bind(&TestMenu::enterFullscreen, this),
            spanner
        ),
        MenuItem(
            tr("Leave fullscreen"),
            std::bind(&TestMenu::leaveFullscreen, this),
            spanner
        ),
        MenuItem(
            tr("Test progress dialog"),
            std::bind(&TestMenu::testProgress, this),
            spanner
        ),
        MenuItem(
            tr("Test wait dialog"),
            std::bind(&TestMenu::testWait, this),
            spanner
        ),
        MenuItem(
            tr("Test scrolling message dialog"),
            std::bind(&TestMenu::testScrollMessageBox, this),
            spanner
        ),
        MenuItem(
            tr("Test size formatter"),
            std::bind(&TestMenu::testSizeFormatter, this),
            spanner
        ),
        MenuItem(
            tr("Test conversions"),
            std::bind(&TestMenu::testConversions, this),
            spanner
        ),
        MenuItem(
            tr("Test Eigen functions"),
            std::bind(&TestMenu::testEigenFunctions, this),
            spanner
        ),
        MenuItem(
            tr("Test random number functions (and associated floating point "
               "assistance functions)"),
            std::bind(&TestMenu::testRandom, this),
            spanner
        ),
        MenuItem(
            tr("Test logistic regression, and the underlying generalized linear model (GLM)"),
            std::bind(&TestMenu::testLogisticRegression, this),
            spanner
        ),
        MAKE_MENU_MENU_ITEM(WidgetTestMenu, app),
        MenuItem(
            tr("Configure demo Whisker task"),
            std::bind(&TestMenu::configureDemoWhiskerTask, this),
            spanner
        ),
        MenuItem(
            tr("Run demo Whisker task"),
            std::bind(&TestMenu::runDemoWhiskerTask, this),
            spanner
        ),
        MAKE_TASK_MENU_ITEM(DemoQuestionnaire::DEMOQUESTIONNAIRE_TABLENAME, app),
    };
}


TestMenu::~TestMenu()
{
    // Unsure if necessary - but similar code in QuAudioPlayer was crashing.
    soundfunc::finishMediaPlayer(m_player);
}


void TestMenu::testDebugConsole()
{
    qInfo() << "Testing debug console. This is the entire test. Success.";
    uifunc::alert("Success! See the debug console for output.");
}


void TestMenu::testSound()
{
    soundfunc::makeMediaPlayer(m_player);
    const QUrl url(uiconst::DEMO_SOUND_URL_1);
    qDebug() << "Trying to play:" << url;
    m_player->setMedia(url);
    m_player->setVolume(50);
    m_player->play();
}


void TestMenu::testHttps()
{
    // To find bad certificates, see
    // https://www.ssllabs.com/ssltest/analyze.html
    const QString url = "https://egret.psychol.cam.ac.uk/index.html";  // good cert
    // const QString url = "https://www.veltigroup.com/";  // bad cert (then Forbidden)

    NetworkManager* netmgr = m_app.networkManager();
    netmgr->setTitle("Test HTTPS");
    netmgr->testHttpsGet(url);
}


void TestMenu::testHttp()
{
    const QString url = "http://egret.psychol.cam.ac.uk/index.html";
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->setTitle("Test HTTP");
    netmgr->testHttpGet(url);
}


void TestMenu::testPhq9Creation()
{
#ifdef DEBUG_OPTIONS
    const QString tablename = Phq9::PHQ9_TABLENAME;
    TaskPtr p_task = m_app.taskFactory()->create(tablename);
    if (!p_task) {
        qCritical() << Q_FUNC_INFO << "Failed to create task: "
                    << qUtf8Printable(tablename);
        return;
    }
    qDebug() << *p_task;
    doneSeeConsole();
#endif
}


void TestMenu::testIcd10CodeSetCreation()
{
#ifdef DEBUG_OPTIONS
    const Icd10 icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
#endif
}


void TestMenu::testIcd9cmCodeSetCreation()
{
#ifdef DEBUG_OPTIONS
    const Icd9cm icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
#endif
}


void TestMenu::doneSeeConsole()
{
    if (platform::PLATFORM_TABLET) {
        uifunc::alert("Done; see USB debugging output");
    } else {
        uifunc::alert("Done; see console");
    }
}


void TestMenu::testProgress()
{
    qDebug() << Q_FUNC_INFO << "start";
    // http://doc.qt.io/qt-4.8/qprogressdialog.html#details
    // http://stackoverflow.com/questions/3752742/how-do-i-create-a-pause-wait-function-using-qt
    const int num_things = 100;
    QProgressDialog progress(
        "Testing progress (but not doing anything; safe to abort)...",
        "Abort test", 0, num_things, this);
    progress.setWindowTitle("Progress dialog");
    progress.setWindowModality(Qt::WindowModal);
    progress.setMinimumDuration(0);
    for (int i = 0; i < num_things; i++) {
        progress.setValue(i);
        if (progress.wasCanceled()) {
            break;
        }
        // Do a small thing:
        QThread::msleep(50);
        // Prevent other things (like audio) from freezing:
        QCoreApplication::processEvents();
    }
    progress.setValue(num_things);
    qDebug() << Q_FUNC_INFO << "finish";
}


void TestMenu::testWait()
{
    SlowNonGuiFunctionCaller(
        std::bind(&TestMenu::expensiveFunction, this),
        this,
        QString("Running uninterruptible expensive function in worker thread "
                "(for %1 ms)").arg(EXPENSIVE_FUNCTION_DURATION_MS),
        "Please wait");
}


void TestMenu::expensiveFunction()
{
    qDebug() << Q_FUNC_INFO << "start: sleep time (ms)" << EXPENSIVE_FUNCTION_DURATION_MS;
    QThread::msleep(EXPENSIVE_FUNCTION_DURATION_MS);
    qDebug() << Q_FUNC_INFO << "finish";
}


void TestMenu::testScrollMessageBox()
{
    ScrollMessageBox msgbox(QMessageBox::Question,
                            "ScrollMessageBox, with some lengthy text",
                            textconst::TERMS_CONDITIONS,
                            this);
    QAbstractButton* one = msgbox.addButton("One (Yes)",
                                            QMessageBox::YesRole);
    QAbstractButton* two = msgbox.addButton("Two (No)",
                                            QMessageBox::NoRole);
    QAbstractButton* three = msgbox.addButton("Three (Reject)",
                                              QMessageBox::RejectRole);
    const int ret = msgbox.exec();
    qInfo() << "exec() returned" << ret;
    QAbstractButton* response = msgbox.clickedButton();
    if (response == one) {
        qInfo() << "Response: one";
    } else if (response == two) {
        qInfo() << "Response: two";
    } else if (response == three) {
        qInfo() << "Response: three";
    } else if (response == nullptr) {
        qInfo() << "Response nullptr (cancelled)";
    } else {
        qInfo() << "Response UNKNOWN";
    }
}


void TestMenu::testSizeFormatter()
{
    const bool space = true;
    const bool longform = false;
    const QString suffix = longform ? "bytes" : "B";
    const QVector<double> nums{
        3e0, 3e1, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 3e8, 3e9,
        3e10, 3e11, 3e12, 3e13, 3e14, 3e15, 3e16, 3e17, 3e18, 3e19,
        3e20, 3e21, 3e22, 3e23, 3e24, 3e25, 3e26, 3e27, 3e28, 3e29,
        0, 27, 999, 1000, 1023, 1024, 1728, 110592, 7077888, 452984832,
        28991029248, 1855425871872, 9223372036854775807.0};
    QString text;
    for (bool binary : {false, true}) {
        for (auto num : nums) {
            text += QString("%1 → %2\n")
              .arg(num)
              .arg(convert::prettySize(num, space, binary, longform, suffix));
        }
    }
    uifunc::alertLogMessageBox(text, "Size formatting", false);
}


void TestMenu::testConversions()
{
    convert::testConversions();
    uifunc::alert("Conversion test: OK");
}


void TestMenu::testEigenFunctions()
{
    const QString text = eigenfunc::testEigenFunctions().join("\n");

    uifunc::alertLogMessageBox(text, "Eigen functions successfully tested",
                               false);
}


void TestMenu::testRandom()
{
    const QString text = ccrandom::testRandom().join("\n");
    uifunc::alertLogMessageBox(text,
                               "Random-number functions (and supporting "
                               "floating-point-delta functions): OK",
                               false);
}


void TestMenu::testLogisticRegression()
{
    using namespace eigenfunc;
    using namespace Eigen;
    QStringList results;

    // ========================================================================
    // Data set 1
    // ========================================================================

    qInfo() << Q_FUNC_INFO
            << "1a. Our 'plain' method: LogisticDescriptives(x, y)";
    const QVector<double> x_q{0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 4.00, 4.25, 4.50, 4.75, 5.00, 5.50};
    const QVector<int> y_q{0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1};
    const LogisticDescriptives ld1(x_q, y_q, true);
    const QString result1 = QString(R"(
# Example from: https://en.wikipedia.org/wiki/Logistic_regression
# R code:

d <- data.frame(
    x = c(0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 4.00, 4.25, 4.50, 4.75, 5.00, 5.50),
    y = c(0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1)
)
dm <- matrix(c(rep(1, length(d$x)), d$x), ncol=2)
# irls_svdnewton(dm, d$y)
model <- glm(y ~ x, family=binomial(link='logit'), data=d)
summary(model)

# R gives coefficients: intercept = -4.0777, x = 1.5046
# (as per Wikipedia also)

Our results: intercept = %1, slope = %2)
        )").arg(ld1.intercept()).arg(ld1.slope());

    qInfo() << Q_FUNC_INFO
            << "1b. A more detailed look: LogisticRegression(), IRLS";
    const VectorXd x_e = eigenColumnVectorFromQVector<double>(x_q);
    const VectorXi y_e = eigenColumnVectorFromQVector<int>(y_q);
    LogisticRegression lr1a(Glm::SolveMethod::IRLS_KaneLewis);
    lr1a.setVerbose(true);
    lr1a.fit(x_e, y_e);
    const VectorXd coeffs1a = lr1a.coefficients();
    const VectorXd p = lr1a.predictProb();
    const VectorXi cat = lr1a.predictBinary();

    qInfo() << Q_FUNC_INFO
            << "1c. A more detailed look: LogisticRegression(), IRLS SVD Newton";
    LogisticRegression lr1c(Glm::SolveMethod::IRLS_SVDNewton_KaneLewis);
    lr1c.setVerbose(true);
    lr1c.fit(x_e, y_e);
    const VectorXd coeffs1c = lr1c.coefficients();

    results.append(QString(R"(
With the same data:

IN x: %1
IN y: %2

IRLS method:
OUT coefficients: %3
OUT predicted p: %4
OUT predicted categories: %5
OUT n_iterations: %6
OUT time to fit (ms): %7

IRLS-SVD-Newton method:
OUT coefficients: %8
OUT n_iterations: %9
OUT time to fit (ms): %10
        )")
            .arg(qStringFromEigenMatrixOrArray(x_e))
            .arg(qStringFromEigenMatrixOrArray(y_e))
            .arg(qStringFromEigenMatrixOrArray(coeffs1a))
            .arg(qStringFromEigenMatrixOrArray(p))
            .arg(qStringFromEigenMatrixOrArray(cat))
            .arg(QString::number(lr1a.nIterations()))
            .arg(QString::number(lr1a.timeToFitMs()))
            .arg(qStringFromEigenMatrixOrArray(coeffs1c))
            .arg(QString::number(lr1c.nIterations()))
            .arg(QString::number(lr1c.timeToFitMs())));

    const VectorXd test_x = eigenColumnVectorFromInitList<double>({0.8, 1.6, 2.4, 3.2});
    const VectorXd predicted_p = lr1a.predictProb(test_x);
    const VectorXd retrieved_x = lr1a.retrodictUnivariatePredictor(predicted_p);
    const LogisticDescriptives ld2(coeffs1a);
    VectorXd crosscheck_x(retrieved_x.size());
    for (int i = 0; i < crosscheck_x.size(); ++i) {
        const double p = predicted_p(i);
        crosscheck_x(i) = ld2.x(p);
    }

#ifdef GLM_OFFER_R_GLM_FIT
    qInfo() << Q_FUNC_INFO
            << "1d. LogisticRegression(), IRLS implemented as per R glm.fit";
    LogisticRegression lr1d(Glm::SolveMethod::IRLS_R_glmfit);
    lr1d.setVerbose(true);
    lr1d.fit(x_e, y_e);
    const VectorXd coeffs1d = lr1d.coefficients();
    results.append(QString("With our implementation of R's glm.fit IRLS: "
                           "%1").arg(qStringFromEigenMatrixOrArray(coeffs1d)));
#endif

    results.append(QString(R"(
Now some silly things:

test_x: %1
predicted_p: %2
retrieved_x [SHOULD MATCH test_x]: %3
crosscheck_x (via LogisticDescriptives()) [SHOULD MATCH test_x]: %4
        )")
            .arg(qStringFromEigenMatrixOrArray(test_x))
            .arg(qStringFromEigenMatrixOrArray(predicted_p))
            .arg(qStringFromEigenMatrixOrArray(retrieved_x))
            .arg(qStringFromEigenMatrixOrArray(crosscheck_x)));

    // ========================================================================
    // Data set 2
    // ========================================================================

    qInfo() << Q_FUNC_INFO
            << "2a. A more numerically complex example, via IRLS.";
    VectorXd x2 = eigenColumnVectorFromInitList<double>({
        0.09969334049243989, 0, 0.04984667024621994,
        0.059846670246219945, 0.04984667024621994, 0.059846670246219945,
        0.04984667024621994, 0.059846670246219945, 0.04984667024621994,
        0.059846670246219945, 0.06984667024621995, 0.059846670246219945,
        0.06984667024621995, 0.059846670246219945});
    VectorXi y2 = eigenColumnVectorFromInitList<int>({
        1, 0, 0,
        1, 0, 1,
        0, 1, 0,
        0, 1, 0,
        1, 1});
    LogisticRegression lr2a(Glm::SolveMethod::IRLS_KaneLewis);
    lr2a.setVerbose(true);
    lr2a.fit(x2, y2);
    const VectorXd coeffs2a = lr2a.coefficients();

    qInfo() << Q_FUNC_INFO
            << "2b. A more numerically complex example, via IRLS-SVD-Newton.";
    LogisticRegression lr2b(Glm::SolveMethod::IRLS_SVDNewton_KaneLewis);
    lr2b.setVerbose(true);
    lr2b.fit(x2, y2);
    const VectorXd coeffs2b = lr2b.coefficients();

    results.append(QString(R"(
Another example, giving a warning in R:

d2 <- data.frame(
    intensity = c(
        0.09969334049243989, 0, 0.04984667024621994,
        0.059846670246219945, 0.04984667024621994, 0.059846670246219945,
        0.04984667024621994, 0.059846670246219945, 0.04984667024621994,
        0.059846670246219945, 0.06984667024621995, 0.059846670246219945,
        0.06984667024621995, 0.059846670246219945
    ),
    yes = c(
        1, 0, 0,
        1, 0, 1,
        0, 1, 0,
        0, 1, 0,
        1, 1)
)
m2 <- glm(yes ~ intensity, family=binomial(link='logit'), data=d2)
# R coefficients: intercept -119.8, slope 2014.1

CamCOPS: coefficients: IRLS: %1
CamCOPS: coefficients: IRLS-SVD-Newton: %2
)")
            .arg(qStringFromEigenMatrixOrArray(coeffs2a))
            .arg(qStringFromEigenMatrixOrArray(coeffs2b)));

#ifdef GLM_OFFER_R_GLM_FIT
    qInfo() << Q_FUNC_INFO << "2c. And again with the R glm.fit method.";
    LogisticRegression lr2c(Glm::SolveMethod::IRLS_R_glmfit);
    lr2c.setVerbose(true);
    lr2c.fit(x2, y2);
    const VectorXd coeffs2c = lr2c.coefficients();
    results.append(QString(
           "CamCOPS: coefficients: RNC implementation of R's "
           "glm.fit IRLS: %1").arg(qStringFromEigenMatrixOrArray(coeffs2c)));
#endif

    /*

plot(d2$intensity, d2$yes)
m2 <- glm(yes ~ intensity, family=binomial(link='logit'), data=d2)
# Warning message: glm.fit: fitted probabilities numerically 0 or 1 occurred
# R coefficients: intercept -119.8, slope 2014.1
predict(m2, type='response')

# Then with IRLS-SVD-Newton method from https://bwlewis.github.io/GLM/ :
design2 = matrix(c(rep(1, length(d2$intensity)), d2$intensity), ncol=2)
m3 <- irls_svdnewton(design2, d2$yes)  # maxit=25, tol=1e-08
# ... coefficients -16.69754, 240.95452; iterations 25 (i.e. non-convergence)

We get non-convergence with IRLS, but with the same max_iterations and
tolerance, we get the same results from IRLS-SVD-Newton:

CamCOPS: coefficients: IRLS: %1
CamCOPS: coefficients: IRLS-SVD-Newton: %2

... but note that max_iterations is important during non-convergence; e.g. with
500 instead, we get 0.177316312229748, 2.10120649598573. Stick with 25!

To visualize:

logistic <- function(x, intercept=0, slope=1) {
  t <- intercept + slope * x
  1 / (1 + exp(-t))
}
# curve(logistic(x), -6, 6)  # as per Wikipedia!
r_fn <- function(x) logistic(x, -119.8, 2014.1)
camcops_25_fn <- function(x) logistic(x, -16.6975412143982, 240.954480219989)
camcops_500_fn <- function(x) logistic(x, 0.177316312229748, 2.10120649598573)
rcppnumerical_fastlr_fn <- function(x) logistic(x, -49.08323, 831.76727)
plot(r_fn, 0, max(d2$intensity), col='blue')
plot(camcops_25_fn, col='red', add=TRUE)
plot(camcops_500_fn, col='green', add=TRUE)
plot(rcppnumerical_fastlr_fn, col='orange', add=TRUE)
points(x=d2$intensity, y=d2$yes)

The R function is doing it better, although the IRLS-SVD-Newton one isn't dreadful.
To see R's actual GLM method, type "glm.fit".
See also https://www.r-bloggers.com/even-faster-linear-model-fits-with-r-using-rcppeigen/

Implement the full method used by R, or RcppEigen:

https://github.com/RcppCore/RcppEigen/blob/master/src/fastLm.cpp
https://github.com/yixuan/RcppNumerical/blob/master/src/fastLR.cpp
https://github.com/lme4/lme4/tree/master/src

Rcpp

    */

    uifunc::alertLogMessageBox(results.join("\n"),
                               tr("Test logistic regression"), false);
}


void TestMenu::configureDemoWhiskerTask()
{

}


void TestMenu::runDemoWhiskerTask()
{
    using namespace whiskerapi;
    using namespace whiskerconstants;

    WhiskerManager* w = m_app.whiskerManager();
    if (!w->isConnected()) {
        w->alertNotConnected();
        return;
    }
    connect(w, &WhiskerManager::eventReceived,
            this, &TestMenu::whiskerEventReceived);
    // ... will autodisconnect when "this" is deleted, as the menu closes

    // We follow DemoConsoleClientTask.cpp from the Whisker SDK:

    // ------------------------------------------------------------------------
    // Variables
    // ------------------------------------------------------------------------
    const int display_num = 0;
    const bool use_video = true;
    const bool use_two_videos = true;
    const QString media_directory("");
    const QString bmp_filename_1("C:\\coffee.bmp");
    const QString bmp_filename_2("C:\\santa_fe.bmp");
    const QString video_filename_1("C:\\started.wmv");
    const QString video_filename_2("C:\\security.wmv");

    // ------------------------------------------------------------------------
    // Setup
    // ------------------------------------------------------------------------

    w->displayClaim(display_num, main_display);
    w->displayScaleDocuments(main_display, true);
    if (!use_video) {
        DisplayCreationOptions dco;
        w->displayCreateDevice(second_display, dco);
        w->displayScaleDocuments(second_display, true);
    }
    w->displayCreateDocument(doc);
    w->displaySetDocumentSize(doc, QSize(1600, 1200));
    w->displaySetBackgroundColour(doc, QColor(100, 0, 0));

    // ------------------------------------------------------------------------
    // Simple objects
    // ------------------------------------------------------------------------

    Pen pen(1, QColor(255, 255, 0), PenStyle::Solid);
    Brush brush(QColor(0, 0, 255), QColor(0, 100, 100), true,
                BrushStyle::Solid, BrushHatchStyle::BDiagonal);

    w->displayAddObject(
                doc, line_obj,
                Line(QPoint(50, 50), QPoint(700, 700), pen));
    w->displayAddObject(
                doc, arc_obj,
                Arc(QRect(100, 100, 300, 300),
                    QPoint(150, 100), QPoint(350, 100), pen));
    w->displayAddObject(
                doc, bezier_obj,
                Bezier(QPoint(100, 100), QPoint(100, 400),
                       QPoint(400, 100), QPoint(400, 400), pen));

    pen.width = 2;

    w->displayAddObject(
                doc, chord_obj,
                Chord(QRect(300, 300, 200, 200),
                      QPoint(300, 350), QPoint(500, 350), pen, brush));

    brush.colour = QColor(0, 200, 0);

    w->displayAddObject(
                doc, ellipse_obj,
                Ellipse(QRect(650, 100, 100, 300), pen, brush));
    w->displayAddObject(
                doc, pie_obj,
                Pie(QRect(600, 300, 200, 200),
                    QPoint(800, 300), QPoint(800, 500), pen, brush));

    brush.style = BrushStyle::Hatched;
    brush.opaque = false;

    w->displayAddObject(
                doc, rectangle_obj,
                Rectangle(QRect(150, 450, 100, 100), pen, brush));
    w->displayAddObject(
                doc, roundrect_obj,
                RoundRect(QRect(900, 450, 300, 100),
                          QSize(150, 150), pen, brush));

    brush.hatch_style = BrushHatchStyle::FDiagonal;
    brush.bg_colour = QColor(100, 100, 0);

    w->displayAddObject(
                doc, polygon_obj_1,
                Polygon(
                    // triangle
                    QVector<QPoint>{{400, 500}, {600, 450}, {600, 550}},
                    pen, brush, false
                ));
    w->displayAddObject(
                doc, polygon_obj_2,
                Polygon(
                    // pentagram
                    QVector<QPoint>{{150, 425},
                                    {75, 650},
                                    {250, 500},
                                    {50, 500},
                                    {225, 650}},
                    pen, brush, false
                ));

    Text text(QPoint(50, 50), "CamCOPS Whisker demo", 0, "Times New Roman");
    text.italic = true;
    w->displayAddObject(doc, text_obj, text);

    w->setMediaDirectory(media_directory);
    w->displayAddObject(
                doc, bmp_obj_1,
                Bitmap(QPoint(100, 100), bmp_filename_1));
    w->displayAddObject(
                doc, bmp_obj_2,
                Bitmap(QPoint(200, 200), bmp_filename_2));

    w->displayAddObject(
                doc, camcogquadpattern_obj,
                CamcogQuadPattern(
                    QPoint(350, 100),
                    QSize(10, 8),
                    QVector<uint8_t>{1, 2, 3, 4, 5, 6, 7, 8},
                    QVector<uint8_t>{9, 10, 11, 12, 13, 14, 15, 16},
                    QVector<uint8_t>{255, 254, 253, 252, 251, 250, 249, 248},
                    QVector<uint8_t>{247, 246, 245, 244, 243, 242, 241, 240},
                    QColor(255, 0, 0),
                    QColor(0, 255, 0),
                    QColor(0, 0, 255),
                    QColor(255, 255, 0),
                    QColor(50, 50, 50)
                ));

    auto setDemoEvents = [&](const QString& obj,
                             const QString& eventstem) -> void {
        w->displaySetEvent(doc, obj, DocEventType::MouseDown,
                           eventstem + suffix_event_clicked);
        w->displaySetEvent(doc, obj, DocEventType::MouseUp,
                           eventstem + suffix_event_unclicked);
        w->displaySetEvent(doc, obj, DocEventType::MouseMove,
                           eventstem + suffix_event_mouse_moved);
        w->displaySetEvent(doc, obj, DocEventType::TouchDown,
                           eventstem + suffix_event_touched);
        w->displaySetEvent(doc, obj, DocEventType::TouchUp,
                           eventstem + suffix_event_released);
        w->displaySetEvent(doc, obj, DocEventType::TouchMove,
                           eventstem + suffix_event_touch_moved);
    };

    setDemoEvents(bmp_obj_1, event_bmp_1);
    setDemoEvents(bmp_obj_2, event_bmp_2);
    setDemoEvents(ellipse_obj, event_ellipse);
    setDemoEvents(roundrect_obj, event_roundrect);
    setDemoEvents(rectangle_obj, event_rectangle);
    // setDemoEvents(strTextObj, event_text);
    setDemoEvents(polygon_obj_1, event_polygon_1);
    setDemoEvents(polygon_obj_2, event_polygon_2);
    setDemoEvents(chord_obj, event_chord);
    setDemoEvents(pie_obj, event_pie);
    setDemoEvents(camcogquadpattern_obj, event_camcogquadpattern);

    w->displaySetBackgroundEvent(doc, DocEventType::MouseDown,
                                 background_event + suffix_event_clicked);
    w->displaySetBackgroundEvent(doc, DocEventType::TouchDown,
                                 background_event + suffix_event_touched);

    // ------------------------------------------------------------------------
    // Video
    // ------------------------------------------------------------------------

    auto setVideoDemoEvents = [&](const QString& obj,
                                  const QString& touchevent) -> void {
        w->displaySetEvent(doc, obj, DocEventType::MouseDown,
                           touchevent);
        w->displaySetEvent(doc, obj, DocEventType::TouchDown,
                           touchevent);
    };
    auto createVideoCluster = [&](const QString& prefix, int top) -> void {
        const QString strPlayObj(prefix + "play");
        const QString strPauseObj(prefix + "pause");
        const QString strStopObj(prefix + "stop");
        const QString strBackObj(prefix + "back");
        const QString strFwdObj(prefix + "fwd");

        brush.style = BrushStyle::Solid;
        brush.colour = QColor(0, 0, 255);
        w->displayAddObject(
                    doc, strPlayObj,
                    Polygon(QVector<QPoint>{QPoint(800, top),
                                            QPoint(850, top + 25),
                                            QPoint(800, top + 50)},
                            pen, brush));

        brush.colour = QColor(0, 0, 0);
        w->displayAddObject(
                    doc, strPauseObj,
                    Rectangle(QRect(900, top, 50, 50), pen, brush));
        brush.colour = QColor(0, 255, 0);
        w->displayAddObject(
                    doc, strPauseObj,
                    Rectangle(QRect(900, top, 15, 50), pen, brush));
        w->displayAddObject(
                    doc, strPauseObj,
                    Rectangle(QRect(935, top, 15, 50), pen, brush));

        brush.colour = QColor(255, 0, 0);
        w->displayAddObject(
                    doc, strStopObj,
                    Rectangle(QRect(1000, top, 50, 50), pen, brush));

        brush.colour = QColor(0, 0, 0);
        w->displayAddObject(
                    doc, strBackObj,
                    Rectangle(QRect(1100, top, 50, 50), pen, brush));

        brush.colour = QColor(0, 0, 0);
        w->displayAddObject(
                    doc, strBackObj,
                    Polygon(QVector<QPoint>{QPoint(1125, top),
                                            QPoint(1100, top + 25),
                                            QPoint(1125, top + 50)},
                            pen, brush));
        w->displayAddObject(
                    doc, strBackObj,
                    Polygon(QVector<QPoint>{QPoint(1150, top),
                                            QPoint(1125, top + 25),
                                            QPoint(1150, top + 50)},
                            pen, brush));

        brush.colour = QColor(0, 0, 0);
        w->displayAddObject(
                    doc, strFwdObj,
                    Rectangle(QRect(1200, top, 50, 50), pen, brush));
        brush.colour = QColor(255, 255, 0);
        w->displayAddObject(
                    doc, strFwdObj,
                    Polygon(QVector<QPoint>{QPoint(1200, top),
                                            QPoint(1225, top + 25),
                                            QPoint(1200, top + 50)},
                            pen, brush));
        w->displayAddObject(
                    doc, strFwdObj,
                    Polygon(QVector<QPoint>{QPoint(1225, top),
                                            QPoint(1250, top + 25),
                                            QPoint(1225, top + 50)},
                            pen, brush));

        setVideoDemoEvents(strPlayObj, prefix + suffix_event_video_play);
        setVideoDemoEvents(strPauseObj, prefix + suffix_event_video_pause);
        setVideoDemoEvents(strStopObj, prefix + suffix_event_video_stop);
        setVideoDemoEvents(strFwdObj, prefix + suffix_event_video_fwd);
        setVideoDemoEvents(strBackObj, prefix + suffix_event_video_back);
    };

    if (use_video) {
        const QString strAudioDevice("audiodevice");

        w->audioClaim(1, strAudioDevice);
        // w->displaySetAudioDevice(0, 1);
        w->displaySetAudioDevice(main_display, strAudioDevice);
        const int videotop1 = 50, videotop2 = 600;
        bool bLoop = true;

        w->displayAddObject(
                    doc, video_obj_1,
                    Video(QPoint(50, videotop1), video_filename_1, bLoop));
        if (use_two_videos) {
            w->displayAddObject(
                        doc, video_obj_2,
                        Video(QPoint(50, videotop2), video_filename_2, bLoop));
        }
        qDebug() << "~~~ Starting video 2 at 10s";
        w->videoSeekAbsolute(doc, video_obj_2, 10000);
        w->videoTimestamps(true);

        createVideoCluster(video_obj_1, 50);
        setVideoDemoEvents(video_obj_1, event_video_1_touched);
        if (use_two_videos) {
            createVideoCluster(video_obj_both, 300);
            createVideoCluster(video_obj_2, 600);
            setVideoDemoEvents(video_obj_2, event_video_2_touched);
        }
    }

    // ------------------------------------------------------------------------
    // OK; go.
    // ------------------------------------------------------------------------

    w->displayShowDocument(main_display, doc);
    if (!use_video) {
        w->displayShowDocument(second_display, doc);
    }
}


void TestMenu::whiskerEventReceived(const WhiskerInboundMessage& msg)
{
    WhiskerManager* w = m_app.whiskerManager();
    const QString event = msg.event();

    qInfo().noquote() << "Received event:" << event;

    // Video control:

    auto reportVideoTimings = [&]() -> void {
        unsigned int time = w->videoGetTimeMs(doc, video_obj_1);
        unsigned int duration = w->videoGetDurationMs(doc, video_obj_1);
        qInfo().nospace()
                << "video1 time: " << time
                << "; video1 duration: " << duration;
        time = w->videoGetTimeMs(doc, video_obj_2);
        duration = w->videoGetDurationMs(doc, video_obj_2);
        qInfo().nospace()
                << "video2 time: " << time
                << "; video2 duration: " << duration;
    };

    if (event == event_video_1_touched) {
        qInfo() << "~~~ Seeking video 1 forward 5s, playing video 1, pausing video 2";
        w->videoSeekRelative(doc, video_obj_1, FIVE_SEC);
        w->videoPlay(doc, video_obj_1);
        w->videoPause(doc, video_obj_2);
        reportVideoTimings();
    } else if (event == event_video_2_touched) {
        qInfo() << "~~~ Pausing video 1, seeking video 1 back 5s, playing video 2";
        w->videoSeekRelative(doc, video_obj_1, -FIVE_SEC);
        w->videoPlay(doc, video_obj_2);
        w->videoPause(doc, video_obj_1);
        reportVideoTimings();
    } else if (event == video_obj_1 + suffix_event_video_play) {
        qInfo() << "~~~ Playing video 1";
        w->videoPlay(doc, video_obj_1);
    } else if (event == video_obj_2 + suffix_event_video_play) {
        qInfo() << "~~~ Playing video 2";
        w->videoPlay(doc, video_obj_2);
    } else if (event == video_obj_both + suffix_event_video_play) {
        qInfo() << "~~~ Playing video 1+2";
        w->videoPlay(doc, video_obj_1);
        w->videoPlay(doc, video_obj_2);
    } else if (event == video_obj_1 + suffix_event_video_pause) {
        qInfo() << "~~~ Pausing video 1";
        w->videoPause(doc, video_obj_1);
    } else if (event == video_obj_2 + suffix_event_video_pause) {
        qInfo() << "~~~ Pausing video 2";
        w->videoPause(doc, video_obj_2);
    } else if (event == video_obj_both + suffix_event_video_pause) {
        qInfo() << "~~~ Pausing video 1+2";
        w->videoPause(doc, video_obj_1);
        w->videoPause(doc, video_obj_2);
    } else if (event == video_obj_1 + suffix_event_video_stop) {
        qInfo() << "~~~ Stopping video 1";
        w->videoStop(doc, video_obj_1);
    } else if (event == video_obj_2 + suffix_event_video_stop) {
        qInfo() << "~~~ Stopping video 2";
        w->videoStop(doc, video_obj_2);
    } else if (event == video_obj_both + suffix_event_video_stop) {
        qInfo() << "~~~ Stopping video 1+2";
        w->videoStop(doc, video_obj_1);
        w->videoStop(doc, video_obj_2);
    } else if (event == video_obj_1 + suffix_event_video_fwd) {
        qInfo() << "~~~ Fwding video 1";
        w->videoSeekRelative(doc, video_obj_1, FIVE_SEC);
    } else if (event == video_obj_2 + suffix_event_video_fwd) {
        qInfo() << "~~~ Fwding video 2";
        w->videoSeekRelative(doc, video_obj_2, FIVE_SEC);
    } else if (event == video_obj_both + suffix_event_video_fwd) {
        qInfo() << "~~~ Fwding video 1+2";
        w->videoSeekRelative(doc, video_obj_1, FIVE_SEC);
        w->videoSeekRelative(doc, video_obj_2, FIVE_SEC);
    } else if (event == video_obj_1 + suffix_event_video_back) {
        qInfo() << "~~~ Backing video 1";
        w->videoSeekRelative(doc, video_obj_1, -FIVE_SEC);
    } else if (event == video_obj_2 + suffix_event_video_back) {
        qInfo() << "~~~ Backing video 2";
        w->videoSeekRelative(doc, video_obj_2, -FIVE_SEC);
    } else if (event == video_obj_both + suffix_event_video_back) {
        qInfo() << "~~~ Backing video 1+2";
        w->videoSeekRelative(doc, video_obj_1, -FIVE_SEC);
        w->videoSeekRelative(doc, video_obj_2, -FIVE_SEC);
    }
}

// todo: *** test actual bitmaps
// todo: *** test actual videos
// todo: *** test Whisker timers
// todo: *** test Whisker lines
// todo: *** test Whisker line flashing via callbacks
// todo: *** when task finished, call w->disconnectAllWhiskerSignals(this)
