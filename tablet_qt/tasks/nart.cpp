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

#include "nart.h"
#include "lib/convert.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"

const QString NART_TABLENAME("nart");

// Most of the NART is hard-coded as it is language-specific by its nature
const QStringList WORDLIST{
    "chord",
    "ache",
    "depot",
    "aisle",
    "bouquet",
    "psalm",
    "capon",
    "deny",
    "nausea",
    "debt",
    "courteous",
    "rarefy",
    "equivocal",
    "naive",  // accent required
    "catacomb",
    "gaoled",
    "thyme",
    "heir",
    "radix",
    "assignate",
    "hiatus",
    "subtle",
    "procreate",
    "gist",
    "gouge",
    "superfluous",
    "simile",
    "banal",
    "quadruped",
    "cellist",
    "facade",  // accent required
    "zealot",
    "drachm",
    "aeon",
    "placebo",
    "abstemious",
    "detente",  // accent required
    "idyll",
    "puerperal",
    "aver",
    "gauche",
    "topiary",
    "leviathan",
    "beatify",
    "prelate",
    "sidereal",
    "demesne",
    "syncope",
    "labile",
    "campanile",
};
QStringList ACCENTED_WORDLIST;
const int DP = 1;


void initializeNart(TaskFactory& factory)
{
    static TaskRegistrar<Nart> registered(factory);

    ACCENTED_WORDLIST = WORDLIST;
    ACCENTED_WORDLIST.replace(WORDLIST.indexOf("naive"), "naïve");
    ACCENTED_WORDLIST.replace(WORDLIST.indexOf("facade"), "façade");
    ACCENTED_WORDLIST.replace(WORDLIST.indexOf("detente"), "détente");
}


Nart::Nart(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, NART_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addFields(WORDLIST, QVariant::Bool);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Nart::shortname() const
{
    return "NART";
}


QString Nart::longname() const
{
    return tr("National Adult Reading Test");
}


QString Nart::menusubtitle() const
{
    return tr("Estimation of premorbid IQ by reading irregular words.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Nart::isComplete() const
{
    return mathfunc::noneNull(values(WORDLIST));
}


QStringList Nart::summary() const
{
    bool complete = isComplete();
    int errors = numErrors();
    return QStringList{
        result(nelsonFullScaleIQ(complete, errors)),
        result(nelsonWillisonFullScaleIQ(complete, errors)),
        result(brightFullScaleIQ(complete, errors)),
    };
}


QStringList Nart::detail() const
{
    bool complete = isComplete();
    int errors = numErrors();
    QStringList wordresults{"Words correct?"};
    for (int i = 0; i < ACCENTED_WORDLIST.length(); ++i) {
        QString fieldname = WORDLIST.at(i);
        QString word = ACCENTED_WORDLIST.at(i);
        wordresults.append(stringfunc::standardResult(word,
                                                      prettyValue(fieldname)));
    }
    return completenessInfo() + wordresults + QStringList{
        stringfunc::standardResult("Number of errors",
                                   QString::number(errors)),
        "",
        result(nelsonFullScaleIQ(complete, errors)),
        result(nelsonVerbalIQ(complete, errors)),
        result(nelsonPerformanceIQ(complete, errors)),
        "",
        result(nelsonWillisonFullScaleIQ(complete, errors)),
        "",
        result(brightFullScaleIQ(complete, errors)),
        result(brightGeneralAbility(complete, errors)),
        result(brightVerbalComprehension(complete, errors)),
        result(brightPerceptualReasoning(complete, errors)),
        result(brightWorkingMemory(complete, errors)),
        result(brightPerceptualSpeed(complete, errors)),
    };
}


OpenableWidget* Nart::editor(bool read_only)
{
    NameValueOptions options = CommonOptions::incorrectCorrectBoolean();

    QVector<QuElement*> cells;
    for (int i = 0; i < ACCENTED_WORDLIST.length(); ++i) {
        QString fieldname = WORDLIST.at(i);
        QString word = ACCENTED_WORDLIST.at(i).toUpper();
        cells.append((new QuText(word))->setBold());
        cells.append((new QuMcq(fieldRef(fieldname), options))
                     ->setHorizontal(true));
    }

    QuPagePtr page(new QuPage{
        getClinicianQuestionnaireBlockRawPointer(),
        new QuText("Give the subject a piece of paper with the NART word list "
                   "on. Follow the instructions in the Task Information. Use "
                   "the list below to score. You may find it quickest to mark "
                   "errors as the subject reads, then fill in correct answers "
                   "at the end."),
        (new QuGridContainer(2, cells))->setFixedGrid(false),
    });
    page->setTitle(longname());

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Clinician);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Nart::numErrors() const
{
    return mathfunc::countFalse(values(WORDLIST));
}


const QString NELSON_1982("Nelson 1982");
const QString NELSON_WILLISON_1991("Nelson & Willison 1991");
const QString BRIGHT_2016("Bright 2016, PMID 27624393");
#define IF_COMPLETE(complete, x) (complete ? (x) : QVariant())


Nart::NartIQ Nart::nelsonFullScaleIQ(bool complete, int errors) const
{
    // Figures from partial PDF of Nelson 1982
    return NartIQ("Predicted WAIS full-scale IQ",
                  NELSON_1982,
                  "127.7 – 0.826 × errors",
                  IF_COMPLETE(complete, 127.7 - 0.826 * errors));
}


Nart::NartIQ Nart::nelsonVerbalIQ(bool complete, int errors) const
{
    // Figures from partial PDF of Nelson 1982
    return NartIQ("Predicted WAIS verbal IQ",
                  NELSON_1982,
                  "129.0 – 0.919 × errors",
                  IF_COMPLETE(complete, 129.0 - 0.919 * errors));
}


Nart::NartIQ Nart::nelsonPerformanceIQ(bool complete, int errors) const
{
    // Figures from partial PDF of Nelson 1982
    return NartIQ("Predicted WAIS performance IQ",
                  NELSON_1982,
                  "123.5 – 0.645 × errors",
                  IF_COMPLETE(complete, 123.5 - 0.645 * errors));
}


Nart::NartIQ Nart::nelsonWillisonFullScaleIQ(bool complete, int errors) const
{
    // Figures from Bright 2016
    return NartIQ("Predicted WAIS-R full-scale IQ",
                  NELSON_WILLISON_1991,
                  "130.6 – 1.24 × errors",
                  IF_COMPLETE(complete, 130.6 - 1.24 * errors));
}


Nart::NartIQ Nart::brightFullScaleIQ(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV full-scale IQ",
                  BRIGHT_2016,
                  "126.41 – 0.9775 × errors",
                  IF_COMPLETE(complete, 126.41 - 0.9775 * errors));
}


Nart::NartIQ Nart::brightGeneralAbility(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV General Ability Index",
                  BRIGHT_2016,
                  "126.5 – 0.9656 × errors",
                  IF_COMPLETE(complete, 126.5 - 0.9656 * errors));
}


Nart::NartIQ Nart::brightVerbalComprehension(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV Verbal Comprehension Index",
                  BRIGHT_2016,
                  "126.81 – 1.0745 × errors",
                  IF_COMPLETE(complete, 126.81 - 1.0745 * errors));
}


Nart::NartIQ Nart::brightPerceptualReasoning(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV Perceptual Reasoning Index",
                  BRIGHT_2016,
                  "120.18 – 0.6242 × errors",
                  IF_COMPLETE(complete, 120.18 - 0.6242 * errors));
}


Nart::NartIQ Nart::brightWorkingMemory(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV Working Memory Index",
                  BRIGHT_2016,
                  "120.53 – 0.7901 × errors",
                  IF_COMPLETE(complete, 120.53 - 0.7901 * errors));
}


Nart::NartIQ Nart::brightPerceptualSpeed(bool complete, int errors) const
{
    return NartIQ("Predicted WAIS-IV Perceptual Speed Index",
                  BRIGHT_2016,
                  "114.53 – 0.5285 × errors",
                  IF_COMPLETE(complete, 114.53 - 0.5285 * errors));
}


QString Nart::result(const NartIQ& iq) const
{
    QString name = QString("%1 (%2; %3)")
            .arg(iq.quantity, iq.reference, iq.formula);
    QString value = convert::prettyValue(iq.iq, DP);
    return stringfunc::standardResult(name, value);
}
