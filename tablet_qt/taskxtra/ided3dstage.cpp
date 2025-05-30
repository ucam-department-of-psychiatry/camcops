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

#include "ided3dstage.h"

#include "ided3dexemplars.h"

// Table names
const QString IDED3DStage::STAGE_TABLENAME("ided3d_stages");

// Fieldnames: Stage
const QString IDED3DStage::FN_FK_TO_TASK("ided3d_id");
const QString IDED3DStage::FN_STAGE("stage");
const QString FN_STAGE_NAME("stage_name");
const QString FN_RELEVANT_DIMENSION("relevant_dimension");
const QString FN_CORRECT_EXEMPLAR("correct_exemplar");
const QString FN_INCORRECT_EXEMPLAR("incorrect_exemplar");
const QString FN_CORRECT_STIMULUS_SHAPES("correct_stimulus_shapes");
const QString FN_CORRECT_STIMULUS_COLOURS("correct_stimulus_colours");
const QString FN_CORRECT_STIMULUS_NUMBERS("correct_stimulus_numbers");
const QString FN_INCORRECT_STIMULUS_SHAPES("incorrect_stimulus_shapes");
const QString FN_INCORRECT_STIMULUS_COLOURS("incorrect_stimulus_colours");
const QString FN_INCORRECT_STIMULUS_NUMBERS("incorrect_stimulus_numbers");
const QString FN_FIRST_TRIAL_NUM("first_trial_num");
const QString FN_N_COMPLETED_TRIALS("n_completed_trials");
const QString FN_N_CORRECT("n_correct");
const QString FN_N_INCORRECT("n_incorrect");
const QString FN_STAGE_PASSED("stage_passed");
const QString FN_STAGE_FAILED("stage_failed");

IDED3DStage::IDED3DStage(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    DatabaseObject(app, db, STAGE_TABLENAME),
    m_incorrect_stimulus_can_overlap(false),
    m_n_possible_locations(0)
{
    addField(FN_FK_TO_TASK, QMetaType::fromType<int>());
    // More keys
    addField(FN_STAGE, QMetaType::fromType<int>(), true);
    // ... 1-based stage number within this session
    // Config
    addField(FN_STAGE_NAME, QMetaType::fromType<QString>());
    addField(FN_RELEVANT_DIMENSION, QMetaType::fromType<QString>());
    addField(FN_CORRECT_EXEMPLAR, QMetaType::fromType<int>());
    // ... was string prior to 2.0.0
    addField(FN_INCORRECT_EXEMPLAR, QMetaType::fromType<int>());
    // ... was string prior to 2.0.0
    addField(FN_CORRECT_STIMULUS_SHAPES, QMetaType::fromType<QVector<int>>());
    addField(FN_CORRECT_STIMULUS_COLOURS, QMetaType::fromType<QVector<int>>());
    // ... was string prior to 2.0.0
    addField(FN_CORRECT_STIMULUS_NUMBERS, QMetaType::fromType<QVector<int>>());
    addField(
        FN_INCORRECT_STIMULUS_SHAPES, QMetaType::fromType<QVector<int>>()
    );
    addField(
        FN_INCORRECT_STIMULUS_COLOURS, QMetaType::fromType<QVector<int>>()
    );
    // ... was string prior to 2.0.0
    addField(
        FN_INCORRECT_STIMULUS_NUMBERS, QMetaType::fromType<QVector<int>>()
    );
    // Results
    addField(FN_FIRST_TRIAL_NUM, QMetaType::fromType<int>());  // 1-based
    addField(FN_N_COMPLETED_TRIALS, QMetaType::fromType<int>());
    addField(FN_N_CORRECT, QMetaType::fromType<int>());
    addField(FN_N_INCORRECT, QMetaType::fromType<int>());
    addField(FN_STAGE_PASSED, QMetaType::fromType<bool>());
    addField(FN_STAGE_FAILED, QMetaType::fromType<bool>());

    load(load_pk);
}


IDED3DStage::IDED3DStage(
    const int task_id,
    CamcopsApp& app,
    DatabaseManager& db,
    const int stage_num_zero_based,
    const QString& stage_name,
    const QString& relevant_dimension,
    const IDED3DExemplars& correct_exemplars,
    const IDED3DExemplars& incorrect_exemplars,
    const int n_possible_locations,
    const bool incorrect_stimulus_can_overlap
) :
    IDED3DStage::IDED3DStage(app, db, dbconst::NONEXISTENT_PK)
// ... delegating constructor
{
    QVector<int> correct_stimulus_shapes = correct_exemplars.getShapes();
    QVector<int> correct_stimulus_colours = correct_exemplars.getColours();
    QVector<int> correct_stimulus_numbers = correct_exemplars.getNumbers();
    QVector<int> correct_exemplar_vec
        = correct_exemplars.getExemplars(relevant_dimension);
    Q_ASSERT(correct_exemplar_vec.length() == 1);
    int correct_exemplar = correct_exemplar_vec.at(0);
    QVector<int> incorrect_stimulus_shapes = incorrect_exemplars.getShapes();
    QVector<int> incorrect_stimulus_colours = incorrect_exemplars.getColours();
    QVector<int> incorrect_stimulus_numbers = incorrect_exemplars.getNumbers();
    QVector<int> incorrect_exemplar_vec
        = incorrect_exemplars.getExemplars(relevant_dimension);
    Q_ASSERT(incorrect_exemplar_vec.length() == 1);
    int incorrect_exemplar = incorrect_exemplar_vec.at(0);

    setValue(FN_FK_TO_TASK, task_id);
    // Config
    setValue(FN_STAGE, stage_num_zero_based + 1);
    setValue(FN_STAGE_NAME, stage_name);
    setValue(FN_RELEVANT_DIMENSION, relevant_dimension);
    setValue(FN_CORRECT_EXEMPLAR, correct_exemplar);
    setValue(FN_INCORRECT_EXEMPLAR, incorrect_exemplar);
    setValue(FN_CORRECT_STIMULUS_SHAPES, correct_stimulus_shapes);
    setValue(FN_CORRECT_STIMULUS_COLOURS, correct_stimulus_colours);
    setValue(FN_CORRECT_STIMULUS_NUMBERS, correct_stimulus_numbers);
    setValue(FN_INCORRECT_STIMULUS_SHAPES, incorrect_stimulus_shapes);
    setValue(FN_INCORRECT_STIMULUS_COLOURS, incorrect_stimulus_colours);
    setValue(FN_INCORRECT_STIMULUS_NUMBERS, incorrect_stimulus_numbers);
    // Results
    setValue(FN_FIRST_TRIAL_NUM, QVariant());  // NULL
    setValue(FN_N_COMPLETED_TRIALS, 0);
    setValue(FN_N_CORRECT, 0);
    setValue(FN_N_INCORRECT, 0);
    setValue(FN_STAGE_PASSED, false);
    setValue(FN_STAGE_FAILED, false);

    save();

    // Internal only:
    m_incorrect_stimulus_can_overlap = incorrect_stimulus_can_overlap;
    m_n_possible_locations = n_possible_locations;
}

int IDED3DStage::taskId() const
{
    return valueInt(FN_FK_TO_TASK);
}

int IDED3DStage::stageNumZeroBased() const
{
    return valueInt(FN_STAGE) - 1;
}

int IDED3DStage::nPossibleLocations() const
{
    return m_n_possible_locations;
}

QVector<int> IDED3DStage::correctStimulusShapes() const
{
    return valueVectorInt(FN_CORRECT_STIMULUS_SHAPES);
}

QVector<int> IDED3DStage::correctStimulusColours() const
{
    return valueVectorInt(FN_CORRECT_STIMULUS_COLOURS);
}

QVector<int> IDED3DStage::correctStimulusNumbers() const
{
    return valueVectorInt(FN_CORRECT_STIMULUS_NUMBERS);
}

QVector<int> IDED3DStage::incorrectStimulusShapes() const
{
    return valueVectorInt(FN_INCORRECT_STIMULUS_SHAPES);
}

QVector<int> IDED3DStage::incorrectStimulusColours() const
{
    return valueVectorInt(FN_INCORRECT_STIMULUS_COLOURS);
}

QVector<int> IDED3DStage::incorrectStimulusNumbers() const
{
    return valueVectorInt(FN_INCORRECT_STIMULUS_NUMBERS);
}

bool IDED3DStage::incorrectStimulusCanOverlap() const
{
    return m_incorrect_stimulus_can_overlap;
}

void IDED3DStage::recordResponse(const bool correct)
{
    if (correct) {
        addToValueInt(FN_N_CORRECT, 1);
    } else {
        addToValueInt(FN_N_INCORRECT, 1);
    }
    save();
}

void IDED3DStage::recordTrialCompleted()
{
    addToValueInt(FN_N_COMPLETED_TRIALS, 1);
    save();
}

void IDED3DStage::recordStageEnded(const bool passed)
{
    setValue(FN_STAGE_PASSED, passed);
    setValue(FN_STAGE_FAILED, !passed);
    save();
}

void IDED3DStage::setFirstTrialIfBlank(const int trial_num_zero_based)
{
    if (valueIsNull(FN_FIRST_TRIAL_NUM)) {
        setValue(FN_FIRST_TRIAL_NUM, trial_num_zero_based + 1);  // 1-based
        save();
    }
}

QString IDED3DStage::summary() const
{
    return QString("Stage: %1; relevant dimension: %2")
        .arg(valueString(FN_STAGE_NAME), valueString(FN_RELEVANT_DIMENSION));
}
