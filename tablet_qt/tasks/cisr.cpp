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

/*

===============================================================================
PRIMARY REFERENCE
===============================================================================

CIS-R: Lewis et al. 1992
- https://www.ncbi.nlm.nih.gov/pubmed/1615114

Helpful chronology:
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3347904/#b2-mjms-13-1-058

===============================================================================
INTERNALS
===============================================================================

The internal methodology of the CIS-R is that the textfile
"BASIC CIS-R 02-03-2010.pqs" contains a sequence, of the type:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LABEL_A1

"Some question?"

[
1 "Option 1"
2 "Option 2"
3 "Option 3"
]

SOMEVAR := answer * 10
if answer == 1 then goto LABEL_B1;
if answer == 2 then goto LABEL_B2;
if answer == 3 then goto LABEL_B3;

&

LABEL_B1

...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===============================================================================
IMPLEMENTATION: EARLY THOUGHTS -- NOT USED
===============================================================================

We could in principle do this with a Questionnaire interface, but to be honest
it's going to be easiest to translate with a "direct" interface. Maybe
something like:


void start()
{
    goto(1);
}

void goto_question(int question)
{
    m_current_question = question;
    offer_question();
}

bool offer_question()
{
    // do interesting things
    connect(answer_1, answered, 1);
    return true;
}

bool answered(int answer)
{
    // returns: something we don't care about
    switch (m_current_question) {
    case 1:
        if (answer == 1) {
            m_diagnosis_blah = true;
            return goto(2);
            // C++11: can't do "return goto_question(2);" if goto_question() is
            // of void type, as you're not allowed to return anything from a
            // void function, even of void type:
            // http://stackoverflow.com/questions/35987493/return-void-type-in-c-and-c
            // ... so just make them bool or something.
            // It would be OK in C++14.
        }
        break;
    // ...
    }
}


===============================================================================
IMPLEMENTATION: FURTHER THOUGHTS
===============================================================================

FURTHER THOUGHTS: we'll implement a DynamicQuestionnaire class; q.v.

*/

#include "cisr.h"
#include "questionnairelib/dynamicquestionnaire.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qupage.h"
#include "tasklib/taskfactory.h"

const QString Cisr::CISR_TABLENAME("cisr");

// FP field prefix; NUM field numbers; FN field name
// These match the electronic version of the CIS-R, as per "BASIC CIS-R 02-03-2010.pqs".
const QString FN_ETHNIC("ethnic");
const QString FN_MARRIED("married");
const QString FN_EMPSTAT("empstat");
const QString FN_EMPTYPE("emptype");
const QString FN_HOME("home");

const QString FN_APPETITE1("appetite1");
const QString FN_WEIGHT1("weight1");
const QString FN_WEIGHT2("weight2");
const QString FN_WEIGHT3("weight3");
const QString FN_APPETITE2("appetite2");
const QString FN_WEIGHT4("weight4");  // male/female responses unified (no "weight4a")
const QString FN_WEIGHT5("weight5");

const QString FN_GP_YEAR("gp_year");
const QString FN_DISABLE("disable");
const QString FN_ILLNESS("illness");

const QString FN_SOMATIC_MAND1("somatic_mand1");
const QString FN_SOMATIC_PAIN1("somatic_pain1");
const QString FN_SOMATIC_PAIN2("somatic_pain2");
const QString FN_SOMATIC_PAIN3("somatic_pain3");
const QString FN_SOMATIC_PAIN4("somatic_pain4");
const QString FN_SOMATIC_PAIN5("somatic_pain5");
const QString FN_SOMATIC_MAND2("somatic_mand2");
const QString FN_SOMATIC_DIS1("somatic_dis1");
const QString FN_SOMATIC_DIS2("somatic_dis2");
const QString FN_SOMATIC_DIS3("somatic_dis3");
const QString FN_SOMATIC_DIS4("somatic_dis4");
const QString FN_SOMATIC_DIS5("somatic_dis5");
const QString FN_SOMATIC_DUR("somatic_dur");

const QString FN_FATIGUE_MAND1("fatigue_mand1");
const QString FN_FATIGUE_CAUSE1("fatigue_cause1");
const QString FN_FATIGUE_TIRED1("fatigue_tired1");
const QString FN_FATIGUE_TIRED2("fatigue_tired2");
const QString FN_FATIGUE_TIRED3("fatigue_tired3");
const QString FN_FATIGUE_TIRED4("fatigue_tired4");
const QString FN_FATIGUE_MAND2("fatigue_mand2");
const QString FN_FATIGUE_CAUSE2("fatigue_cause2");
const QString FN_FATIGUE_ENERGY1("fatigue_energy1");
const QString FN_FATIGUE_ENERGY2("fatigue_energy2");
const QString FN_FATIGUE_ENERGY3("fatigue_energy3");
const QString FN_FATIGUE_ENERGY4("fatigue_energy4");
const QString FN_FATIGUE_DUR("fatigue_dur");

const QString FN_CONC_MAND1("conc_mand1");
const QString FN_CONC_MAND2("conc_mand2");
const QString FN_CONC1("conc1");
const QString FN_CONC2("conc2");
const QString FN_CONC3("conc3");
const QString FN_CONC_DUR("conc_dur");
const QString FN_CONC4("conc4");
const QString FN_FORGET_DUR("forget_dur");

const QString FN_SLEEP_MAND1("sleep_mand1");
const QString FN_SLEEP_LOSE1("sleep_lose1");
const QString FN_SLEEP_LOSE2("sleep_lose2");
const QString FN_SLEEP_LOSE3("sleep_lose3");
const QString FN_SLEEP_EMW("sleep_emw");
const QString FN_SLEEP_CAUSE("sleep_cause");
const QString FN_SLEEP_MAND2("sleep_mand2");
const QString FN_SLEEP_GAIN1("sleep_gain1");
const QString FN_SLEEP_GAIN2("sleep_gain2");
const QString FN_SLEEP_DUR("sleep_dur");

const QString FN_IRRIT_MAND1("irrit_mand1");
const QString FN_IRRIT_MAND2("irrit_mand2");
const QString FN_IRRIT1("irrit1");
const QString FN_IRRIT2("irrit2");
const QString FN_IRRIT3("irrit3");
const QString FN_IRRIT4("irrit4");
const QString FN_IRRIT_DUR("irrit_dur");

const QString FN_HYPO_MAND1("hypo_mand1");
const QString FN_HYPO_MAND2("hypo_mand2");
const QString FN_HYPO1("hypo1");
const QString FN_HYPO2("hypo2");
const QString FN_HYPO3("hypo3");
const QString FN_HYPO4("hypo4");
const QString FN_HYPO_DUR("hypo_dur");

const QString FN_DEPR_MAND1("depr_mand1");
const QString FN_DEPR1("depr1");
const QString FN_DEPR_MAND2("depr_mand2");
const QString FN_DEPR2("depr2");
const QString FN_DEPR3("depr3");
const QString FN_DEPR4("depr4");
const QString FN_DEPR_CONTENT("depr_content");
const QString FN_DEPR5("depr5");
const QString FN_DEPR_DUR("depr_dur");
const QString FN_DEPTH1("depth1");
const QString FN_DEPTH2("depth2");
const QString FN_DEPTH3("depth3");
const QString FN_DEPTH4("depth4");
const QString FN_DEPTH5("depth5");
const QString FN_DEPTH6("depth6");
const QString FN_DEPTH7("depth7");
const QString FN_DEPTH8("depth8");
const QString FN_DEPTH9("depth9");
const QString FN_DEPTH10("depth10");
const QString FN_DOCTOR("doctor");

const QString FN_WORRY_MAND1("worry_mand1");
const QString FN_WORRY_MAND2("worry_mand2");
const QString FN_WORRY_CONT1("worry_cont1");
const QString FN_WORRY2("worry2");
const QString FN_WORRY3("worry3");
const QString FN_WORRY4("worry4");
const QString FN_WORRY5("worry5");
const QString FN_WORRY_DUR("worry_dur");

const QString FN_ANX_MAND1("anx_mand1");
const QString FN_ANX_MAND2("anx_mand2");
const QString FN_ANX_PHOBIA1("anx_phobia1");
const QString FN_ANX_PHOBIA2("anx_phobia2");
const QString FN_ANX2("anx2");
const QString FN_ANX3("anx3");
const QString FN_ANX4("anx4");
const QString FN_ANX5("anx5");
const QString FN_ANX_DUR("anx_dur");

const QString FN_PHOBIAS_MAND("phobias_mand");
const QString FN_PHOBIAS_TYPE1("phobias_type1");
const QString FN_PHOBIAS1("phobias1");
const QString FN_PHOBIAS2("phobias2");
const QString FN_PHOBIAS3("phobias3");
const QString FN_PHOBIAS4("phobias4");
const QString FN_PHOBIAS_DUR("phobias_dur");

const QString FN_PANIC_MAND("panic_mand");
const QString FN_PANIC1("panic1");
const QString FN_PANIC2("panic2");
const QString FN_PANIC3("panic3");
const QString FN_PANIC4("panic4");
const QString FN_PANSYM_A("pansym_a");
const QString FN_PANSYM_B("pansym_b");
const QString FN_PANSYM_C("pansym_c");
const QString FN_PANSYM_D("pansym_d");
const QString FN_PANSYM_E("pansym_e");
const QString FN_PANSYM_F("pansym_f");
const QString FN_PANSYM_G("pansym_g");
const QString FN_PANSYM_H("pansym_h");
const QString FN_PANSYM_I("pansym_i");
const QString FN_PANSYM_J("pansym_j");
const QString FN_PANSYM_K("pansym_k");
const QString FN_PANSYM_L("pansym_l");
const QString FN_PANSYM_M("pansym_m");
const QString FN_PANIC5("panic5");
const QString FN_PANIC_DUR("panic_dur");

const QString FN_COMP_MAND1("comp_mand1");
const QString FN_COMP1("comp1");
const QString FN_COMP2("comp2");
const QString FN_COMP3("comp3");
const QString FN_COMP4("comp4");
const QString FN_COMP_DUR("comp_dur");

const QString FN_OBSESS_MAND1("obsess_mand1");
const QString FN_OBSESS_MAND2("obsess_mand2");
const QString FN_OBSESS1("obsess1");
const QString FN_OBSESS2("obsess2");
const QString FN_OBSESS3("obsess3");
const QString FN_OBSESS4("obsess4");
const QString FN_OBSESS_DUR("obsess_dur");

const QString FN_OVERALL2("overall2");

// Number of response values (numbered from 1 to N)
const int N_ETHNIC = 6;
const int N_MARRIED = 5;
const int N_ILLNESS = 8;
const int N_DURATIONS = 5;

// Actual response values
const int V_EMPSTAT_FT = 1;
const int V_EMPSTAT_PT = 2;
const int V_EMPSTAT_STUDENT = 3;
const int V_EMPSTAT_RETIRED = 4;
const int V_EMPSTAT_HOUSEPERSON = 5;
const int V_EMPSTAT_UNEMPJOBSEEKER = 6;
const int V_EMPSTAT_UNEMPILLHEALTH = 7;

const int V_EMPTYPE_SELFEMPWITHEMPLOYEES = 1;
const int V_EMPTYPE_SELFEMPNOEMPLOYEES = 2;
const int V_EMPTYPE_EMPLOYEE = 3;
const int V_EMPTYPE_SUPERVISOR = 4;
const int V_EMPTYPE_MANAGER = 5;
// *** check: what if never employed?

const int V_HOME_OWNER = 1;
const int V_HOME_TENANT = 2;
const int V_HOME_RELATIVEFRIEND = 3;
const int V_HOME_HOSTELCAREHOME = 4;
const int V_HOME_HOMELESS = 5;
const int V_HOME_OTHER = 6;

const int V_DURATION_LT_2W = 1;
const int V_DURATION_2W_6M = 2;
const int V_DURATION_6M_1Y = 3;
const int V_DURATION_1Y_2Y = 4;
const int V_DURATION_GE_2Y = 5;

const int V_APPETITE1_LOSS_NO = 1;
const int V_APPETITE1_LOSS_YES = 2;

const int V_WEIGHT1_WTLOSS_NO = 1;
const int V_WEIGHT1_WTLOSS_YES = 2;

const int V_WEIGHT2_WTLOSS_NOTTRYING = 1;
const int V_WEIGHT2_WTLOSS_TRYING = 2;

const int V_WEIGHT3_WTLOSS_GE_HALF_STONE = 1;
const int V_WEIGHT3_WTLOSS_LT_HALF_STONE = 2;

const int V_APPETITE2_GAIN_NO = 1;
const int V_APPETITE2_GAIN_YES = 2;

const int V_WEIGHT4_WTGAIN_NO = 1;
const int V_WEIGHT4_WTGAIN_YES = 2;
const int V_WEIGHT4_WTGAIN_YES_PREGNANT = 3;

const int V_WEIGHT5_WTGAIN_GE_HALF_STONE = 1;
const int V_WEIGHT5_WTGAIN_LT_HALF_STONE = 2;

const int V_GPYEAR_NONE = 0;
const int V_GPYEAR_1_2 = 1;
const int V_GPYEAR_3_5 = 2;
const int V_GPYEAR_6_10 = 3;
const int V_GPYEAR_GT_10 = 4;

const int V_DISABLE_YES = 1;
const int V_DISABLE_NO = 2;

const int V_SOMATIC_MAND1_NO = 1;
const int V_SOMATIC_MAND1_YES = 2;

const int V_SOMATIC_PAIN1_NEVER = 1;

const int V_SOMATIC_PAIN2_NONE = 1;


// ============================================================================
// Task registration
// ============================================================================

void initializeCisr(TaskFactory& factory)
{
    static TaskRegistrar<Cisr> registered(factory);
}


// ============================================================================
// Constructor
// ============================================================================

Cisr::Cisr(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CISR_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    const QStringList fieldnames{
        FN_ETHNIC,
        FN_MARRIED,
        FN_EMPSTAT,
        FN_EMPTYPE,
        FN_HOME,

        FN_APPETITE1,
        FN_WEIGHT1,
        FN_WEIGHT2,
        FN_WEIGHT3,
        FN_APPETITE2,
        FN_WEIGHT4,
        FN_WEIGHT5,

        FN_GP_YEAR,
        FN_DISABLE,
        FN_ILLNESS,

        FN_SOMATIC_MAND1,
        FN_SOMATIC_PAIN1,
        FN_SOMATIC_PAIN2,
        FN_SOMATIC_PAIN3,
        FN_SOMATIC_PAIN4,
        FN_SOMATIC_PAIN5,
        FN_SOMATIC_MAND2,
        FN_SOMATIC_DIS1,
        FN_SOMATIC_DIS2,
        FN_SOMATIC_DIS3,
        FN_SOMATIC_DIS4,
        FN_SOMATIC_DIS5,
        FN_SOMATIC_DUR,

        FN_FATIGUE_MAND1,
        FN_FATIGUE_CAUSE1,
        FN_FATIGUE_TIRED1,
        FN_FATIGUE_TIRED2,
        FN_FATIGUE_TIRED3,
        FN_FATIGUE_TIRED4,
        FN_FATIGUE_MAND2,
        FN_FATIGUE_CAUSE2,
        FN_FATIGUE_ENERGY1,
        FN_FATIGUE_ENERGY2,
        FN_FATIGUE_ENERGY3,
        FN_FATIGUE_ENERGY4,
        FN_FATIGUE_DUR,

        FN_CONC_MAND1,
        FN_CONC_MAND2,
        FN_CONC1,
        FN_CONC2,
        FN_CONC3,
        FN_CONC_DUR,
        FN_CONC4,
        FN_FORGET_DUR,

        FN_SLEEP_MAND1,
        FN_SLEEP_LOSE1,
        FN_SLEEP_LOSE2,
        FN_SLEEP_LOSE3,
        FN_SLEEP_EMW,
        FN_SLEEP_CAUSE,
        FN_SLEEP_MAND2,
        FN_SLEEP_GAIN1,
        FN_SLEEP_GAIN2,
        FN_SLEEP_DUR,

        FN_IRRIT_MAND1,
        FN_IRRIT_MAND2,
        FN_IRRIT1,
        FN_IRRIT2,
        FN_IRRIT3,
        FN_IRRIT4,
        FN_IRRIT_DUR,

        FN_HYPO_MAND1,
        FN_HYPO_MAND2,
        FN_HYPO1,
        FN_HYPO2,
        FN_HYPO3,
        FN_HYPO4,
        FN_HYPO_DUR,

        FN_DEPR_MAND1,
        FN_DEPR1,
        FN_DEPR_MAND2,
        FN_DEPR2,
        FN_DEPR3,
        FN_DEPR4,
        FN_DEPR_CONTENT,
        FN_DEPR5,
        FN_DEPR_DUR,
        FN_DEPTH1,
        FN_DEPTH2,
        FN_DEPTH3,
        FN_DEPTH4,
        FN_DEPTH5,
        FN_DEPTH6,
        FN_DEPTH7,
        FN_DEPTH8,
        FN_DEPTH9,
        FN_DEPTH10,
        FN_DOCTOR,

        FN_WORRY_MAND1,
        FN_WORRY_MAND2,
        FN_WORRY_CONT1,
        FN_WORRY2,
        FN_WORRY3,
        FN_WORRY4,
        FN_WORRY5,
        FN_WORRY_DUR,

        FN_ANX_MAND1,
        FN_ANX_MAND2,
        FN_ANX_PHOBIA1,
        FN_ANX_PHOBIA2,
        FN_ANX2,
        FN_ANX3,
        FN_ANX4,
        FN_ANX5,
        FN_ANX_DUR,

        FN_PHOBIAS_MAND,
        FN_PHOBIAS_TYPE1,
        FN_PHOBIAS1,
        FN_PHOBIAS2,
        FN_PHOBIAS3,
        FN_PHOBIAS4,
        FN_PHOBIAS_DUR,

        FN_PANIC_MAND,
        FN_PANIC1,
        FN_PANIC2,
        FN_PANIC3,
        FN_PANIC4,
        FN_PANSYM_A,
        FN_PANSYM_B,
        FN_PANSYM_C,
        FN_PANSYM_D,
        FN_PANSYM_E,
        FN_PANSYM_F,
        FN_PANSYM_G,
        FN_PANSYM_H,
        FN_PANSYM_I,
        FN_PANSYM_J,
        FN_PANSYM_K,
        FN_PANSYM_L,
        FN_PANSYM_M,
        FN_PANIC5,
        FN_PANIC_DUR,

        FN_COMP_MAND1,
        FN_COMP1,
        FN_COMP2,
        FN_COMP3,
        FN_COMP4,
        FN_COMP_DUR,

        FN_OBSESS_MAND1,
        FN_OBSESS_MAND2,
        FN_OBSESS1,
        FN_OBSESS2,
        FN_OBSESS3,
        FN_OBSESS4,
        FN_OBSESS_DUR,

        FN_OVERALL2,
    };
    for (const QString& fn : fieldnames) {
        addField(fn, QVariant::Int);
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Cisr::shortname() const
{
    return "CIS-R";
}


QString Cisr::longname() const
{
    return tr("Clinical Interview Schedule – Revised");
}


QString Cisr::menusubtitle() const
{
    return tr("Structured diagnostic interview, yielding ICD-10 diagnoses for "
              "depressive and anxiety disorders.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Cisr::isComplete() const
{
    // ***
    return false;
}


QStringList Cisr::summary() const
{
    // ***
    return QStringList{"Not implemented yet!"};
}


QStringList Cisr::detail() const
{
    // ***
    return completenessInfo() + summary();
}


OpenableWidget* Cisr::editor(const bool read_only)
{
    m_questionnaire = new DynamicQuestionnaire(
                m_app,
                std::bind(&Cisr::makePage, this, std::placeholders::_1),
                std::bind(&Cisr::morePagesToGo, this, std::placeholders::_1));
    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================


// ============================================================================
// DynamicQuestionnaire callbacks
// ============================================================================

QuPagePtr Cisr::makePage(const int current_qnum)
{
    // Return nullptr to finish.
    CisrQuestion q = nextPageEnum(current_qnum);
    return makePageFromEnum(q);

}


bool Cisr::morePagesToGo(const int current_qnum)
{
    // The lazy option, for now:
    return makePage(current_qnum + 1) != nullptr;
}


// ============================================================================
// Internals to build questionnaires
// ============================================================================
// For methods of enum iteration, see also
// - https://stackoverflow.com/questions/1390703/enumerate-over-an-enum-in-c
// - https://stackoverflow.com/questions/8357240/how-to-automatically-convert-strongly-typed-enum-into-int

Cisr::CisrQuestion Cisr::intToEnum(int qi)
{
    const int start = static_cast<int>(CisrQuestion::START);
    const int end = static_cast<int>(CisrQuestion::END);
    Q_ASSERT(qi >= start && qi <= end);
    return static_cast<CisrQuestion>(qi);
}


int Cisr::enumToInt(CisrQuestion qe)
{
    return static_cast<int>(qe);
}


Cisr::CisrQuestion Cisr::nextPageEnum(const int current_qnum)
{
    // This function embodies the logic about the question sequence.
    //
    // This is slightly tricky algorithmically, since the user can go backwards
    // and forwards. The answers so far define a sequence of questions, and
    // we offer the nth from that sequence.
    //
    // Since the CISR sequence is linear with answer-dependent skipping,
    // it's a little bit easier than it might be.
    // All we need to do is define the moments when we SKIP something.

    int internal_qnum = 0;
    for (int external_qnum = 0; external_qnum < current_qnum; ++external_qnum) {
        CisrQuestion q = intToEnum(internal_qnum);
        int next_q = -1;

        switch (q) {
        case CisrQuestion::APPETITE1:
            if (valueInt(FN_APPETITE1) == V_APPETITE1_LOSS_NO) {
                next_q = enumToInt(CisrQuestion::APPETITE2);
            }
            break;

        case CisrQuestion::SOMATIC_MAND1:
            if (valueInt(FN_SOMATIC_MAND1) == V_SOMATIC_MAND1_NO) {
                next_q = enumToInt(CisrQuestion::SOMATIC_MAND2);
            }
            break;

        case CisrQuestion::WEIGHT1:
            if (valueInt(FN_WEIGHT1) == V_WEIGHT1_WTLOSS_NO) {
                next_q = enumToInt(CisrQuestion::GP_YEAR);
            }
            break;

        case CisrQuestion::WEIGHT2:
            if (valueInt(FN_WEIGHT2) == V_WEIGHT2_TRYING) {
                next_q = enumToInt(CisrQuestion::GP_YEAR);
            }
            break;

        case CisrQuestion::WEIGHT3:
            if (valueInt(FN_WEIGHT1) == V_WEIGHT1_WTLOSS_YES) {
                // Loss of weight, so skip weight gain questions
                next_q = enumToInt(CisrQuestion::GP_YEAR);
            }
            break;

        case CisrQuestion::APPETITE2:
            if (valueInt(FN_APPETITE2) == V_APPETITE2_GAIN_NO) {
                next_q = enumToInt(CisrQuestion::GP_YEAR);
            }
            break;

        case CisrQuestion::WEIGHT4:
            if (valueInt(FN_WEIGHT4) != V_WEIGHT4_WTGAIN_YES) {
                next_q = enumToInt(CisrQuestion::GP_YEAR);
            }
            break;

        case CisrQuestion::DISABLE:
            if (valueInt(FN_DISABLE) == V_DISABLE_NO) {
                next_q = enumToInt(CisrQuestion::SOMATIC_MAND1);
            }
            break;

        case CisrQuestion::SOMATIC_MAND1:
            if (valueInt(FN_SOMATIC_MAND1) == V_SOMATIC_MAND1_NO) {
                next_q = enumToInt(CisrQuestion::SOMATIC_MAND2);
            }
            break;

        case CisrQuestion::SOMATIC_PAIN1:
            if (valueInt(FN_SOMATIC_PAIN1) == V_SOMATIC_PAIN1_NEVER) {
                next_q = enumToInt(CisrQuestion::SOMATIC_MAND2);
            }
            break;

        case CisrQuestion::SOMATIC_PAIN2:
            if (valueInt(FN_SOMATIC_PAIN2) == V_SOMATIC_PAIN2_NONE) {
                next_q = enumToInt(CisrQuestion::SOMATIC_MAND2);
            }
            break;

        case CisrQuestion::SOMATIC_PAIN5:
            if (valueInt(FN_SOMATIC_MAND1) != V_SOMATIC_MAND1_NO) {
                // There was pain, so skip "discomfort"
                next_q = enumToInt(CisrQuestion::FATIGUE_MAND1);
            }
            break;

        // *** am here

        case CisrQuestion::END:
            // we've reached the end; no point thinking further
            return CisrQuestion::END;

        default:
            break;
        }
        if (next_q == -1) {
            // Nothing has expressed an overriding preference, so increment...
            next_q = internal_qnum + 1;
        }
        internal_qnum = next_q;
    }
    return intToEnum(internal_qnum);
}


QuPagePtr Cisr::makePageFromEnum(CisrQuestion q)
{
    // Generic functions
    auto title = [this, &q]() -> QString {
        return QString("CISR question %1").arg(intToEnum(q));
    };
    auto prompttext = [this](const QString& xstringname) -> QuElement* {
        return new QuText(xstring(xstringname));
    };
    auto question = [this](const QString& xstringname) -> QuElement* {
        return new QuText(xstring(xstringname));
    };
    auto qpage = [this, &q, &title, &question]
            (const QString& question_xstringname, QuElement* element)
            -> QuPagePtr {
        QuPage* p = new QuPage();
        p->addElement(question(question_xstringname));
        p->addElement(element);
        p->setTitle(title(pretty_qnum));
        return QuPagePtr(p);
    };

    // Page makers
    auto prompt = [this, &title, &prompttext]
            (const QString& prompt_xstringname) -> QuPagePtr {
        QuPage* p = new QuPage();
        p->addElement(prompttext(prompt_xstringname));
        p->setTitle(title(pretty_qnum));
        return QuPagePtr(p);
    };
    auto duration = [this, &qpage]
            (const QString& fieldname, const QString& question_xstringname)
            -> QuPagePtr {
        NameValueOptions options;
        for (int i = 1; i <= N_DURATIONS; ++i) {
            options.append(NameValuePair(
                    xstring(QString("duration_a%1").arg(i)), i));
        }
        QuElement* element = new QuMcq(fieldRef(fieldname), options);
        return qpage(question_xstringname, element);
    };

    switch (q) {
    case CisrQuestion::ETHNIC:
        TO_DO;

    case CisrQuestion::MARRIED:
        TO_DO;

    case CisrQuestion::EMPSTAT:
        TO_DO;

    case CisrQuestion::HOME:
        TO_DO;

    case CisrQuestion::HEALTH_WELLBEING:
        return prompt("health_wellbeing_statement");

    case CisrQuestion::APPETITE1:
        TO_DO;

    case CisrQuestion::WEIGHT1:
        TO_DO;

    case CisrQuestion::WEIGHT2:
        TO_DO;

    case CisrQuestion::WEIGHT3:
        TO_DO;

    case CisrQuestion::APPETITE2:
        TO_DO;

    case CisrQuestion::WEIGHT4:
        TO_DO;

    case CisrQuestion::WEIGHT4A:
        TO_DO;

    case CisrQuestion::WEIGHT5:
        TO_DO;

    case CisrQuestion::GP_YEAR:
        TO_DO;

    case CisrQuestion::DISABLE:
        TO_DO;

    case CisrQuestion::ILLNESS:
        TO_DO;

    case CisrQuestion::SOMATIC_MAND1:
        TO_DO;

    case CisrQuestion::SOMATIC_PAIN1:
        TO_DO;

    case CisrQuestion::SOMATIC_PAIN2:
        TO_DO;

    case CisrQuestion::SOMATIC_PAIN3:
        TO_DO;

    case CisrQuestion::SOMATIC_PAIN4:
        TO_DO;

    case CisrQuestion::SOMATIC_PAIN5:
        TO_DO;

    case CisrQuestion::SOMATIC_MAND2:
        TO_DO;

    case CisrQuestion::SOMATIC_DIS1:
        TO_DO;

    case CisrQuestion::SOMATIC_DIS2:
        TO_DO;

    case CisrQuestion::SOMATIC_DIS3:
        TO_DO;

    case CisrQuestion::SOMATIC_DIS4:
        TO_DO;

    case CisrQuestion::SOMATIC_DIS5:
        TO_DO;

    case CisrQuestion::SOMATIC_DUR:
        return duration(FN_SOMATIC_DUR, "somatic_dur_q");

    case CisrQuestion::FATIGUE_MAND1:
        TO_DO;

    case CisrQuestion::FATIGUE_CAUSE1:
        TO_DO;

    case CisrQuestion::FATIGUE_TIRED1:
        TO_DO;

    case CisrQuestion::FATIGUE_TIRED2:
        TO_DO;

    case CisrQuestion::FATIGUE_TIRED3:
        TO_DO;

    case CisrQuestion::FATIGUE_TIRED4:
        TO_DO;

    case CisrQuestion::FATIGUE_MAND2:
        TO_DO;

    case CisrQuestion::FATIGUE_CAUSE2:
        TO_DO;

    case CisrQuestion::FATIGUE_ENERGY1:
        TO_DO;

    case CisrQuestion::FATIGUE_ENERGY2:
        TO_DO;

    case CisrQuestion::FATIGUE_ENERGY3:
        TO_DO;

    case CisrQuestion::FATIGUE_ENERGY4:
        TO_DO;

    case CisrQuestion::FATIGUE_DUR:
        return duration(FN_FATIGUE_DUR, "fatigue_dur_q");

    case CisrQuestion::CONC_MAND1:
        TO_DO;

    case CisrQuestion::CONC_MAND2:
        TO_DO;

    case CisrQuestion::CONC1:
        TO_DO;

    case CisrQuestion::CONC2:
        TO_DO;

    case CisrQuestion::CONC3:
        TO_DO;

    case CisrQuestion::CONC_DUR:
        return duration(FN_CONC_DUR, "conc_dur_q");

    case CisrQuestion::CONC4:
        TO_DO;

    case CisrQuestion::FORGET_DUR:
        return duration(FN_FORGET_DUR, "forget_dur_q");

    case CisrQuestion::SLEEP_MAND1:
        TO_DO;

    case CisrQuestion::SLEEP_LOSE1:
        TO_DO;

    case CisrQuestion::SLEEP_LOSE2:
        TO_DO;

    case CisrQuestion::SLEEP_LOSE3:
        TO_DO;

    case CisrQuestion::SLEEP_EMW:
        TO_DO;

    case CisrQuestion::SLEEP_CAUSE:
        TO_DO;

    case CisrQuestion::SLEEP_MAND2:
        TO_DO;

    case CisrQuestion::SLEEP_GAIN1:
        TO_DO;

    case CisrQuestion::SLEEP_GAIN2:
        TO_DO;

    case CisrQuestion::SLEEP_DUR:
        return duration(FN_SLEEP_DUR, "sleep_dur_q");

    case CisrQuestion::IRRIT_MAND1:
        TO_DO;

    case CisrQuestion::IRRIT_MAND2:
        TO_DO;

    case CisrQuestion::IRRIT1:
        TO_DO;

    case CisrQuestion::IRRIT2:
        TO_DO;

    case CisrQuestion::IRRIT3:
        TO_DO;

    case CisrQuestion::IRRIT4:
        TO_DO;

    case CisrQuestion::IRRIT_DUR:
        return duration(FN_IRRIT_DUR, "irrit_dur_q");

    case CisrQuestion::HYPO_MAND1:
        TO_DO;

    case CisrQuestion::HYPO_MAND2:
        TO_DO;

    case CisrQuestion::HYPO1:
        TO_DO;

    case CisrQuestion::HYPO2:
        TO_DO;

    case CisrQuestion::HYPO3:
        TO_DO;

    case CisrQuestion::HYPO4:
        TO_DO;

    case CisrQuestion::HYPO_DUR:
        return duration(FN_HYPO_DUR, "hypo_dur_q");

    case CisrQuestion::DEPR_MAND1:
        TO_DO;

    case CisrQuestion::DEPR1:
        TO_DO;

    case CisrQuestion::DEPR_MAND2:
        TO_DO;

    case CisrQuestion::DEPR2:
        TO_DO;

    case CisrQuestion::DEPR3:
        TO_DO;

    case CisrQuestion::DEPR4:
        TO_DO;

    case CisrQuestion::DEPR_CONTENT:
        TO_DO;

    case CisrQuestion::DEPR5:
        TO_DO;

    case CisrQuestion::DEPR_DUR:
        return duration(FN_DEPR_DUR, "hypo_dur_q");

    case CisrQuestion::DEPTH1:
        TO_DO;

    case CisrQuestion::DEPTH2:
        TO_DO;

    case CisrQuestion::DEPTH3:
        TO_DO;

    case CisrQuestion::DEPTH4:
        TO_DO;

    case CisrQuestion::DEPTH5:
        TO_DO;

    case CisrQuestion::DEPTH6:
        TO_DO;

    case CisrQuestion::DEPTH7:
        TO_DO;

    case CisrQuestion::DEPTH8:
        TO_DO;

    case CisrQuestion::DEPTH9:
        TO_DO;

    case CisrQuestion::DEPTH10:
        TO_DO;

    case CisrQuestion::DOCTOR:
        TO_DO;

    case CisrQuestion::DOCTOR2:
        TO_DO;

    case CisrQuestion::DEPR_OUTRO:
        return prompt("depr_outro");

    case CisrQuestion::WORRY_MAND1:
        TO_DO;

    case CisrQuestion::WORRY_MAND2:
        TO_DO;

    case CisrQuestion::WORRY_CONT1:
        TO_DO;

    case CisrQuestion::WORRY1:
        return prompt("worry1");

    case CisrQuestion::WORRY2:
        TO_DO;

    case CisrQuestion::WORRY3:
        TO_DO;

    case CisrQuestion::WORRY4:
        TO_DO;

    case CisrQuestion::WORRY5:
        TO_DO;

    case CisrQuestion::WORRY_DUR:
        return duration(FN_WORRY_DUR, "worry_dur_q");

    case CisrQuestion::ANX_MAND1:
        TO_DO;

    case CisrQuestion::ANX_MAND2:
        TO_DO;

    case CisrQuestion::ANX_PHOBIA1:
        TO_DO;

    case CisrQuestion::ANX_PHOBIA2:
        TO_DO;

    case CisrQuestion::ANX1:
        return prompt("anx1");

    case CisrQuestion::ANX2:
        TO_DO;

    case CisrQuestion::ANX3:
        TO_DO;

    case CisrQuestion::ANX4:
        TO_DO;

    case CisrQuestion::ANX5:
        TO_DO;

    case CisrQuestion::ANX_DUR:
        return duration(FN_ANX_DUR, "anx_dur_q");

    case CisrQuestion::PHOBIAS_MAND:
        TO_DO;

    case CisrQuestion::PHOBIAS_TYPE1:
        TO_DO;

    case CisrQuestion::PHOBIAS1:
        TO_DO;

    case CisrQuestion::PHOBIAS2:
        TO_DO;

    case CisrQuestion::PHOBIAS3:
        TO_DO;

    case CisrQuestion::PHOBIAS4:
        TO_DO;

    case CisrQuestion::PHOBIAS_DUR:
        return duration(FN_PHOBIAS_DUR, "phobias_dur_q");

    case CisrQuestion::PANIC_MAND1:
        TO_DO;

    case CisrQuestion::PANIC1:
        TO_DO;

    case CisrQuestion::PANIC2:
        TO_DO;

    case CisrQuestion::PANIC3:
        TO_DO;

    case CisrQuestion::PANIC4:
        TO_DO;

    case CisrQuestion::PANSYM:
        TO_DO;

    case CisrQuestion::PANIC5:
        TO_DO;

    case CisrQuestion::PANIC_DUR:
        return duration(FN_PANIC_DUR, "panic_dur_q");

    case CisrQuestion::ANX_OUTRO:
        return prompt("anx_outro");

    case CisrQuestion::COMP_MAND1:
        TO_DO;

    case CisrQuestion::COMP1:
        TO_DO;

    case CisrQuestion::COMP2:
        TO_DO;

    case CisrQuestion::COMP3:
        TO_DO;

    case CisrQuestion::COMP4:
        TO_DO;

    case CisrQuestion::COMP_DUR:
        return duration(FN_COMP_DUR, "comp_dur_q");

    case CisrQuestion::OBSESS_MAND1:
        TO_DO;

    case CisrQuestion::OBSESS_MAND2:
        TO_DO;

    case CisrQuestion::OBSESS1:
        TO_DO;

    case CisrQuestion::OBSESS2:
        TO_DO;

    case CisrQuestion::OBSESS3:
        TO_DO;

    case CisrQuestion::OBSESS4:
        TO_DO;

    case CisrQuestion::OBSESS_DUR:
        return duration(FN_OBSESS_DUR, "obsess_dur_q");

    case CisrQuestion::OVERALL1:
        return prompt("overall1");

    case CisrQuestion::OVERALL2:
        TO_DO;

    case CisrQuestion::END:
    default:
        return nullptr;
    }
}
