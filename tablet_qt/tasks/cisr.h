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

#pragma once
#include <QPointer>
#include <QString>
#include "common/aliases_camcops.h"
#include "tasklib/task.h"

class CamcopsApp;
class DynamicQuestionnaire;
class OpenableWidget;
class TaskFactory;

void initializeCisr(TaskFactory& factory);


class Cisr : public Task
{
    Q_OBJECT
public:
    Cisr(CamcopsApp& app, DatabaseManager& db,
         int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    // ------------------------------------------------------------------------
    // DynamicQuestionnaire callbacks
    // ------------------------------------------------------------------------
    QuPagePtr makePage(int current_qnum);
    bool morePagesToGo(int current_qnum);
public:
    static const QString CISR_TABLENAME;
protected:
    enum class CisrQuestion {  // The sequence of all possible questions.
        START,
        ETHNIC = START,
        MARRIED,
        EMPSTAT,
        HOME,

        HEALTH_WELLBEING,

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
    CisrQuestion intToEnum(int qi);
    int enumToInt(CisrQuestion qe);
    CisrQuestion nextPageEnum(int current_qnum);
    QuPagePtr makePageFromEnum(CisrQuestion q);

protected:
    QPointer<DynamicQuestionnaire> m_questionnaire;
};
