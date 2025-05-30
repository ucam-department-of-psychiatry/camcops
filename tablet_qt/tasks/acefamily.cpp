/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/


#include "acefamily.h"

#include "lib/convert.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "maths/mathfunc.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qutext.h"

using mathfunc::scoreStringWithPercent;


// ============================================================================
// Class data
// ============================================================================

const QString AceFamily::ACE3_TABLENAME(QStringLiteral("ace3"));

const QString AceFamily::TASK_DEFAULT_VERSION(QStringLiteral("A"));

// Shared field names and field prefixes
const QString AceFamily::FN_TASK_EDITION(QStringLiteral("task_edition"));
const QString
    AceFamily::FN_TASK_ADDRESS_VERSION(QStringLiteral("task_address_version"));
const QString AceFamily::FN_REMOTE_ADMINISTRATION(
    QStringLiteral("remote_administration")
);
const QString AceFamily::FN_AGE_FT_EDUCATION(
    QStringLiteral("age_at_leaving_full_time_education")
);
const QString AceFamily::FN_OCCUPATION(QStringLiteral("occupation"));
const QString AceFamily::FN_HANDEDNESS(QStringLiteral("handedness"));

const QString AceFamily::FP_ATTN_TIME(QStringLiteral("attn_time"));

const QString AceFamily::FP_MEM_REPEAT_ADDR_GENERIC(
    QStringLiteral("mem_repeat_address_trial%1_%2")
);
const QString AceFamily::FP_MEM_REPEAT_ADDR_TRIAL1(
    QStringLiteral("mem_repeat_address_trial1_")
);
const QString AceFamily::FP_MEM_REPEAT_ADDR_TRIAL2(
    QStringLiteral("mem_repeat_address_trial2_")
);
const QString AceFamily::FP_MEM_REPEAT_ADDR_TRIAL3(
    QStringLiteral("mem_repeat_address_trial3_")
);
const QString
    AceFamily::FP_MEM_RECALL_ADDRESS(QStringLiteral("mem_recall_address"));

const QString AceFamily::FN_FLUENCY_ANIMALS_SCORE(
    QStringLiteral("fluency_animals_score")
);

const QString AceFamily::FN_VSP_DRAW_CLOCK(QStringLiteral("vsp_draw_clock"));

const QString AceFamily::FN_PICTURE1_BLOBID(QStringLiteral("picture1_blobid"));
const QString AceFamily::FN_PICTURE2_BLOBID(QStringLiteral("picture2_blobid"));
const QString AceFamily::FN_COMMENTS(QStringLiteral("comments"));

const QString AceFamily::TAG_PG_PREAMBLE(QStringLiteral("pg_preamble"));
const QString AceFamily::TAG_EL_CHOOSE_TASK_VERSION(
    QStringLiteral("choose_addr_version")
);
const QString
    AceFamily::TAG_EL_SHOW_TASK_VERSION(QStringLiteral("show_addr_version"));
const QString AceFamily::TAG_REMOTE(QStringLiteral("remote_instr"));
const QString AceFamily::TAG_STANDARD(QStringLiteral("std_instr"));
const QString
    AceFamily::TAG_PG_ADDRESS_LEARNING_FAMOUS(QStringLiteral("pg_addr_learn"));
const QString
    AceFamily::TAG_PG_MEM_FREE_RECALL(QStringLiteral("pg_mem_free_recall"));

const QString AceFamily::X_MINI_ACE_SCORE(QStringLiteral("mini_ace_score"));


// ============================================================================
// Local data
// ============================================================================

const Version SERVER_ACE3_ADDRESS_VARIANT_VERSION(2, 4, 15);

// ============================================================================
// AceFamily
// ============================================================================

AceFamily::AceFamily(
    CamcopsApp& app,
    DatabaseManager& db,
    const QString& tablename,
    QObject* parent
) :
    Task(app, db, tablename, false, true, false, parent),
    // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    // No fields. Subclasses should add those, and call load(load_pk).
}

Version AceFamily::minimumServerVersion() const
{
    // From v2.4.15 we support ACE-III versions A/B/C (address variations).
    return SERVER_ACE3_ADDRESS_VARIANT_VERSION;
}

bool AceFamily::isTaskProperlyCreatable(QString& why_not_creatable) const
{
    if (!isServerStringVersionEnough(
            SERVER_ACE3_ADDRESS_VARIANT_VERSION, why_not_creatable
        )) {
        return false;
    }
    if (!isAddressVersionInfoValid()) {
        why_not_creatable = tr(
            "Server strings are not providing valid information about which "
            "address versions are available. Try re-fetching server info."
        );
        return false;
    }
    return true;
}

QString AceFamily::xstringTaskname() const
{
    return ACE3_TABLENAME;
}

// ============================================================================
// Cosmetic support functions
// ============================================================================

QString AceFamily::scorePercent(int score, int out_of) const
{
    return ": " + scoreStringWithPercent(score, out_of) + ".";
}

// ============================================================================
// Task address version support functions
// ============================================================================

QStringList AceFamily::rawAddressVersionsAvailable() const
{
    const QString x = QString(QStringLiteral("task_address_versions"));
    const QString csv_data = xstring(x);
    return convert::csvStringToQStringList(csv_data);
}

bool AceFamily::isAddressVersionInfoValid(const QStringList& versions) const
{
    // Must be a sequence of capital letters like A, B, C, ...
    const int n = versions.size();
    if (n < 1 || n > 26) {
        return false;
    }
    int base = 'A';
    for (int i = 0; i < n; ++i) {
        const QString& v = versions[i];
        const char c = base + i;
        const QString expected(c);
        if (v != expected) {
            return false;
        }
    }
    return true;
}

bool AceFamily::isAddressVersionInfoValid() const
{
    const QStringList versions = rawAddressVersionsAvailable();
    return isAddressVersionInfoValid(versions);
}

QStringList AceFamily::addressVersionsAvailable() const
{
    const QStringList versions = rawAddressVersionsAvailable();
    if (isAddressVersionInfoValid(versions)) {
        return versions;
    }
    // Default for duff data:
    return QStringList{TASK_DEFAULT_VERSION};
}

QString AceFamily::targetAddressComponent(const int component) const
{
    Q_ASSERT(component >= 1 && component <= N_MEM_REPEAT_RECALL_ADDR);
    const QString task_address_version = taskAddressVersion();
    const QString x = QString(QStringLiteral("task_%1_target_address_%2"))
                          .arg(task_address_version)
                          .arg(component);
    return xstring(x);
}

// ============================================================================
// Automatic tag generation
// ============================================================================

QString AceFamily::tagAddressRegistration(int trial, int component) const
{
    return QString(QStringLiteral("addr_reg_%1_%2")).arg(trial).arg(component);
}

QString AceFamily::tagAddressFreeRecall(int component) const
{
    return QString(QStringLiteral("addr_recall_%1")).arg(component);
}

// ============================================================================
// Editor assistance functions
// ============================================================================

QuElement* AceFamily::textRaw(const QString& string) const
{
    return new QuText(string);
};

QuElement* AceFamily::text(const QString& stringname) const
{
    return textRaw(xstring(stringname));
};

QuElement* AceFamily::explanation(const QString& stringname) const
{
    return (new QuText(xstring(stringname)))->setItalic();
};

QuElement* AceFamily::stdExplan(const QString& stringname) const
{
    return explanation(stringname)->addTag(TAG_STANDARD);
};

QuElement* AceFamily::remExplan(const QString& stringname) const
{
    return explanation(stringname)->addTag(TAG_REMOTE);
};

QuElement* AceFamily::heading(const QString& stringname) const
{
    return new QuHeading(xstring(stringname));
};

QuElement* AceFamily::subheading(const QString& stringname) const
{
    return (new QuText(xstring(stringname)))->setBold()->setBig();
};

QuElement* AceFamily::instructionRaw(const QString& string) const
{
    return (new QuText(string))->setBold();
};

QuElement* AceFamily::instruction(const QString& stringname) const
{
    return instructionRaw(xstring(stringname));
};

QuElement* AceFamily::stdInstruct(const QString& stringname) const
{
    return instruction(stringname)->addTag(TAG_STANDARD);
};

QuElement* AceFamily::remInstruct(const QString& stringname) const
{
    return instruction(stringname)->addTag(TAG_REMOTE);
};

QuElement* AceFamily::boolean(
    const QString& stringname,
    const QString& fieldname,
    bool mandatory,
    bool bold
)
{
    return (new QuBoolean(xstring(stringname), fieldRef(fieldname, mandatory)))
        ->setBold(bold);
};

QuElement* AceFamily::boolimg(
    const QString& filenamestem, const QString& fieldname, bool mandatory
)
{
    return new QuBoolean(
        uifunc::resourceFilename(filenamestem),
        QSize(),
        fieldRef(fieldname, mandatory)
    );
};

QuElement* AceFamily::warning(const QString& string) const
{
    return (new QuText(string))->setWarning();
};
