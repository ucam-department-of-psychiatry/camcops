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
const QString FP_MAIN("main_");
const int NUM_MAIN_MIN = 18;  // CIS-R starts from Q18; was part of a larger earlier thing
const int NUM_MAIN_MAX = 21;
const QString FN_MAIN_19A("main_19a");
const QString FN_MAIN_19B("main_19a");

const QString FP_SOMATIC("somatic_a");  // section A
const int NUM_SOMATIC = 9;  // A9 is just to check your sums; we'll auto-generate

const QString FP_FATIGUE("fatigue_b");  // section B
const int NUM_FATIGUE = 10;  // B10 is just to check your sums; we'll auto-generate
const QString FN_FATIGUE_B3A("fatigue_b3a");

const QString FP_CONCENTRATION("concentration_c");  // section C
const int NUM_CONCENTRATION = 9;

const QString FP_SLEEP("sleep_d");  // section D
const int NUM_SLEEP = 11;
const QString FN_SLEEP_D4A("sleep_d4a");

const QString FP_IRRITABILITY("irritability_e");  // section E
const int NUM_IRRITABILITY = 11;
const QString FN_IRRITABILITY_E7A("irritability_e7a");

const QString FP_WORRYPHYSICAL("worryphysical_f");  // section F
const int NUM_WORRYPHYSICAL = 8;

const QString FP_DEPRESSION("depression_g");  // section G
const int NUM_DEPRESSION = 11;
// There is NO plain G8, just G8(a) and G8(b).
const QString FN_DEPRESSION_G8A_FAMILY("depression_g8a_family");
const QString FN_DEPRESSION_G8A_PARTNER("depression_g8a_partner");
const QString FN_DEPRESSION_G8A_FRIENDS("depression_g8a_friends");
const QString FN_DEPRESSION_G8A_HOUSING("depression_g8a_housing");
const QString FN_DEPRESSION_G8A_MONEY("depression_g8a_money");
const QString FN_DEPRESSION_G8A_PHYSICALHEALTH("depression_g8a_physicalhealth");
const QString FN_DEPRESSION_G8A_MENTALHEALTH("depression_g8a_mentalhealth");
const QString FN_DEPRESSION_G8A_WORK("depression_g8a_work");
const QString FN_DEPRESSION_G8A_LEGAL("depression_g8a_legal");
const QString FN_DEPRESSION_G8A_NEWS("depression_g8a_news");
const QString FN_DEPRESSION_G8A_OTHER("depression_g8a_other");
const QString FN_DEPRESSION_G8A_DK_NO_MAIN("depression_g8a_dk_no_main");
const QString FN_DEPRESSION_G8B("depression_g8b");

const QString FP_DEPRESSIVEIDEAS("depressiveideas_h");  // section H
const int NUM_DEPRESSIVEIDEAS = 11;
const QString FN_DEPRESSIVEIDEAS_H9A("depressiveideas_h9a");
// H9b isn't a question; it's just a prompt for advice about suicidality;
// but we'll document the prompt having been read to the subject:
const QString FN_DEPRESSIVEIDEAS_H9B("depressiveideas_h9b");

const QString FP_WORRY("worry_i");  // section I
const int NUM_WORRY = 9;
// There is NO plain G8, just G8(a) and G8(b).
const QString FN_WORRY_I3A("worry_i3a");
const QString FN_WORRY_G8A_FAMILY("worry_i3a_family");
const QString FN_WORRY_G8A_PARTNER("worry_i3a_partner");
const QString FN_WORRY_G8A_FRIENDS("worry_i3a_friends");
const QString FN_WORRY_G8A_HOUSING("worry_i3a_housing");
const QString FN_WORRY_G8A_MONEY("worry_i3a_money");
const QString FN_WORRY_G8A_PHYSICALHEALTH("worry_i3a_physicalhealth");
const QString FN_WORRY_G8A_MENTALHEALTH("worry_i3a_mentalhealth");
const QString FN_WORRY_G8A_WORK("worry_i3a_work");
const QString FN_WORRY_G8A_LEGAL("worry_i3a_legal");
const QString FN_WORRY_G8A_NEWS("worry_i3a_news");
const QString FN_WORRY_G8A_OTHER("worry_i3a_other");
const QString FN_WORRY_G8A_DK_NO_MAIN("worry_i3a_dk_no_main");
const QString FN_WORRY_I3B("worry_i3b");

const QString FP_ANXIETY("anxiety_j");  // section J
const int NUM_ANXIETY = 12;
const QString FN_ANXIETY_J9A_HEART("anxiety_j9a_heart");
const QString FN_ANXIETY_J9A_SWEATY_SHAKY("anxiety_j9a_sweaty_shaky");
const QString FN_ANXIETY_J9A_DIZZY("anxiety_j9a_dizzy");
const QString FN_ANXIETY_J9A_BREATHLESS("anxiety_j9a_breathless");
const QString FN_ANXIETY_J9A_BUTTERFLIES("anxiety_j9a_butterflies");
const QString FN_ANXIETY_J9A_DRY_MOUTH("anxiety_j9a_dry_mouth");
const QString FN_ANXIETY_J9A_NAUSEA("anxiety_j9a_nausea");

const QString FP_PHOBIA("phobia_k");  // section K
const int NUM_PHOBIA = 9;
// There is NO plain K3, just K3(a) and K3(b).
const QString FN_PHOBIA_K3A("phobia_k3a");
const QString FN_PHOBIA_K3B("phobia_k3b");
const QString FN_PHOBIA_K5A_HEART("phobia_k5a_heart");
const QString FN_PHOBIA_K5A_SWEATY_SHAKY("phobia_k5a_sweaty_shaky");
const QString FN_PHOBIA_K5A_DIZZY("phobia_k5a_dizzy");
const QString FN_PHOBIA_K5A_BREATHLESS("phobia_k5a_breathless");
const QString FN_PHOBIA_K5A_BUTTERFLIES("phobia_k5a_butterflies");
const QString FN_PHOBIA_K5A_DRY_MOUTH("phobia_k5a_dry_mouth");
const QString FN_PHOBIA_K5A_NAUSEA("phobia_k5a_nausea");

const QString FP_PANIC("panic_l");  // section L
const int NUM_PANIC = 8;

const QString FP_COMPULSIONS("compulsions_m");  // section M
const int NUM_COMPULSIONS = 9;

const QString FP_OBSESSIONS("obsessions_n");  // section N
const int NUM_OBSESSIONS = 9;

// There's only one question in section O, with two sub-parts:
const QString FN_OVERALL_1("overall_o1");
const QString FN_OVERALL_1A("overall_o1a");
const QString FN_OVERALL_1B("overall_o1b");


void initializeCisr(TaskFactory& factory)
{
    static TaskRegistrar<Cisr> registered(factory);
}


Cisr::Cisr(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CISR_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // ***

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

enum questionenum {
    ETHNIC,
    MARRIED,
    EMPSTAT,
    HOME,

    APPETITE1,
    WEIGHT1,
    WEIGHT2,
    WEIGHT3,
    APPETITE2,
    WEIGHT4,
    WEIGHT4A,
    WEIGHT5,
    GP_YEAR,
    DISABLE,
    ILLNESS,

    SOMATIC_MAND1,
    SOMATIC_PAIN1,
    SOMATIC_PAIN2,
    SOMATIC_PAIN3,
    SOMATIC_PAIN4,
    SOMATIC_PAIN5,
    SOMATIC_MAND2,
    SOMATIC_DIS1,
    SOMATIC_DIS2,
    SOMATIC_DIS3,
    SOMATIC_DIS4,
    SOMATIC_DIS5,
    SOMATIC_DUR,

    FATIGUE_MAND1,
    FATIGUE_CAUSE1,
    FATIGUE_TIRED1,
    FATIGUE_TIRED2,
    FATIGUE_TIRED3,
    FATIGUE_TIRED4,
    FATIGUE_MAND2,
    FATIGUE_CAUSE2,
    FATIGUE_ENERGY1,
    FATIGUE_ENERGY2,
    FATIGUE_ENERGY3,
    FATIGUE_ENERGY4,
    FATIGUE_DUR,

    CONC_MAND1,
    CONC_MAND2,
    CONC1,
    CONC2,
    CONC3,
    CONC_DUR,
    CONC4,
    FORGET_DUR,

    SLEEP_MAND1,
    SLEEP_LOSE1,
    SLEEP_LOSE2,
    SLEEP_LOSE3,
    SLEEP_EMW,
    SLEEP_CAUSE,
    SLEEP_MAND2,
    SLEEP_GAIN1,
    SLEEP_GAIN2,
    SLEEP_DUR,

    IRRIT_MAND1,
    IRRIT_MAND2,
    IRRIT1,
    IRRIT2,
    IRRIT3,
    IRRIT4,
    IRRIT_DUR,

    HYPO_MAND1,
    HYPO_MAND2,
    HYPO1,
    HYPO2,
    HYPO3,
    HYPO4,
    HYPO_DUR,

    DEPR_MAND1,
    DEPR1,
    DEPR_MAND2,
    DEPR2,
    DEPR3,
    DEPR4,
    DEPR_CONTENT,
    DEPR5,
    DEPR_DUR,
    DEPTH1,
    DEPTH2,
    DEPTH3,
    DEPTH4,
    DEPTH5,
    DEPTH6,
    DEPTH7,
    DEPTH8,
    DEPTH9,
    DEPTH10,
    DOCTOR,
    DOCTOR2,
    DEPR_OUTRO,

    WORRY_MAND1,
    WORRY_MAND2,
    WORRY_CONT1,
    WORRY1,
    WORRY2,
    WORRY3,
    WORRY4,
    WORRY5,
    WORRY_DUR,

    ANX_MAND1,
    ANX_MAND2,
    ANX_PHOBIA1,
    ANX_PHOBIA2,
    ANX1,
    ANX2,
    ANX3,
    ANX4,
    ANX5,
    ANX_DUR,

    PHOBIAS_MAND,
    PHOBIAS_TYPE1,
    PHOBIAS1,
    PHOBIAS2,
    PHOBIAS3,
    PHOBIAS4,
    PHOBIAS_DUR,

    PANIC_MAND1,
    PANIC1,
    PANIC2,
    PANIC3,
    PANIC4,
    PANSYM,
    PANIC5,
    PANIC_DUR,

    ANX_OUTRO,

    COMP_MAND1,
    COMP1,
    COMP2,
    COMP3,
    COMP4,
    COMP_DUR,

    OBSESS_MAND1,
    OBSESS_MAND2,
    OBSESS1,
    OBSESS2,
    OBSESS3,
    OBSESS4,
    OBSESS_DUR,

    OVERALL1,
    OVERALL2,
    END
};

QuPagePtr Cisr::makePage(const int current_qnum)
{
    // Return nullptr to finish.

    // This is slightly tricky algorithmically, since the user can go backwards
    // and forwards. The answers so far define a sequence of questions, and
    // we offer the nth from that sequence.
    //
    // Since the CISR sequence is linear with answer-dependent skipping,
    // it's a little bit easier than it might be.

    int external_qnum;
    int internal_qnum;
    for (external_qnum = 0, internal_qnum = 0;
            internal_qnum < current_qnum;
            ++external_qnum, ++internal_qnum) {
        if (int some_skip_condition = 1) {
            some_skip_condition += 1;  // *** dummy
            internal_qnum += 3;
        }
    }

    // *** this is currently junk; fix

    auto title = [this](int pretty_qnum) -> QString {
        return QString("CISR page %1").arg(pretty_qnum);
    };
    auto rawtext = [this](const QString& text) -> QuElement* {
        return new QuText(text);
    };
    auto page = [this, &title, &rawtext](int qnum) -> QuPagePtr {
        const int pretty_qnum = qnum + 1;
        qDebug().nospace() << "Making page " << qnum
                           << " (pretty 1-based: page " << pretty_qnum << ")";
        QuPage* p = new QuPage();
        p->addElement(rawtext(QString("hello! I'm on page %1").arg(pretty_qnum)));
        p->setTitle(title(pretty_qnum));
        return QuPagePtr(p);
    };

    switch (current_qnum) {
    case 0:
        return page(0);
    case 1:
        return page(1);
    case 2:
        return nullptr;
    default:
        return page(-1);
    }
}


bool Cisr::morePagesToGo(const int current_qnum)
{
    // The lazy option, for now:
    return makePage(current_qnum + 1) != nullptr;
}
