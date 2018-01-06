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

#include "photosequence.h"
#include "common/textconst.h"
#include "db/ancillaryfunc.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"
#include "taskxtra/photosequencephoto.h"

const QString PhotoSequence::PHOTOSEQUENCE_TABLENAME("photosequence");

const QString SEQUENCE_DESCRIPTION("sequence_description");


void initializePhotoSequence(TaskFactory& factory)
{
    static TaskRegistrar<PhotoSequence> registered(factory);
}


PhotoSequence::PhotoSequence(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, PHOTOSEQUENCE_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addField(SEQUENCE_DESCRIPTION, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString PhotoSequence::shortname() const
{
    return "PhotoSequence";
}


QString PhotoSequence::longname() const
{
    return tr("Photograph sequence");
}


QString PhotoSequence::menusubtitle() const
{
    return tr("Sequence of photographs with accompanying detail. "
              "Suitable for use as a photocopier.");
}


QString PhotoSequence::infoFilenameStem() const
{
    return "clinical";
}


// ============================================================================
// Ancillary management
// ============================================================================

QStringList PhotoSequence::ancillaryTables() const
{
    return QStringList{PhotoSequencePhoto::PHOTOSEQUENCEPHOTO_TABLENAME};
}


QString PhotoSequence::ancillaryTableFKToTaskFieldname() const
{
    return PhotoSequencePhoto::FK_NAME;
}


void PhotoSequence::loadAllAncillary(const int pk)
{
    const OrderBy order_by{{PhotoSequencePhoto::SEQNUM, true}};
    ancillaryfunc::loadAncillary<PhotoSequencePhoto, PhotoSequencePhotoPtr>(
                m_photos, m_app, m_db,
                PhotoSequencePhoto::FK_NAME, order_by, pk);
}


QVector<DatabaseObjectPtr> PhotoSequence::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        DatabaseObjectPtr(new PhotoSequencePhoto(m_app, m_db)),
    };
}


QVector<DatabaseObjectPtr> PhotoSequence::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (auto photo : m_photos) {
        ancillaries.append(photo);
    }
    return ancillaries;
}


// ============================================================================
// Instance info
// ============================================================================

bool PhotoSequence::isComplete() const
{
    return numPhotos() > 0 && !valueIsNullOrEmpty(SEQUENCE_DESCRIPTION);
}


QStringList PhotoSequence::summary() const
{
    const int n = numPhotos();
    QStringList lines{stringfunc::abbreviate(valueString(SEQUENCE_DESCRIPTION))};
    lines.append(QString("[%1: <b>%2</b>]")
                 .arg(textconst::PHOTOS)
                 .arg(n));
    for (int i = 0; i < n; ++i) {
        const int human_num = i + 1;
        const QString description = m_photos.at(i)->description();
        if (!description.isEmpty()) {
            lines.append(QString("%1 %2: %3")
                         .arg(textconst::PHOTO)
                         .arg(human_num)
                         .arg(stringfunc::abbreviate(description)));
        }
    }
    return lines;
}


QStringList PhotoSequence::detail() const
{
    return completenessInfo() + summary();
}


OpenableWidget* PhotoSequence::editor(const bool read_only)
{
    // One page per photo.
    // The first page also has the sequence description and clinician details.

    m_questionnaire = new Questionnaire(m_app);

    if (m_photos.length() == 0) {
        addPage(0);
    } else {
        for (int i = 0; i < m_photos.length(); ++i) {
            addPage(i);
        }
    }

    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int PhotoSequence::numPhotos() const
{
    return m_photos.length();
}


// ============================================================================
// Signal handlers
// ============================================================================

void PhotoSequence::refreshQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QuPage* page = m_questionnaire->currentPagePtr();
    const int page_index = m_questionnaire->currentPageIndex();
    rebuildPage(page, page_index);
    m_questionnaire->refreshCurrentPage();
}


void PhotoSequence::addPage(const int page_index)
{
    QuPage* page = new QuPage();
    rebuildPage(page, page_index);
    m_questionnaire->addPage(QuPagePtr(page));
}


void PhotoSequence::rebuildPage(QuPage* page, const int page_index)
{
    QVector<QuElement*> elements;
    QuButton::CallbackFunction callback_add =
            std::bind(&PhotoSequence::addPhoto, this);
    if (page_index == 0) {
        // First page
        elements.append(getClinicianQuestionnaireBlockRawPointer());
        elements.append(new QuText(textconst::PHOTOSEQUENCE_SEQUENCE_DESCRIPTION));
        elements.append(new QuTextEdit(fieldRef(SEQUENCE_DESCRIPTION)));
        if (m_photos.length() == 0) {
            elements.append(new QuButton(textconst::PHOTOSEQUENCE_ADD,
                                         callback_add));
        }
    }
    if (page_index < m_photos.length()) {
        PhotoSequencePhotoPtr photo = m_photos[page_index];
        QuButton::CallbackFunction callback_del =
                std::bind(&PhotoSequence::deletePhoto, this, page_index);
        QuButton::CallbackFunction callback_back =
                std::bind(&PhotoSequence::movePhotoBackwards, this, page_index);
        QuButton::CallbackFunction callback_fwd =
                std::bind(&PhotoSequence::movePhotoForwards, this, page_index);
        const bool is_first = page_index == 0;
        const bool is_last = page_index == m_photos.length() - 1;
        QuButton* add = new QuButton(textconst::PHOTOSEQUENCE_ADD,
                                     callback_add);
        add->setActive(is_last);
        QuButton* del = new QuButton(textconst::PHOTOSEQUENCE_DELETE,
                                     callback_del);
        QuButton* back = new QuButton(textconst::PHOTOSEQUENCE_MOVE_BACK,
                                      callback_back);
        back->setActive(!is_first);
        QuButton* fwd = new QuButton(textconst::PHOTOSEQUENCE_MOVE_FORWARDS,
                                     callback_fwd);
        fwd->setActive(!is_last);
        elements.append(new QuFlowContainer({add, del, back, fwd}));
        elements.append(new QuText(textconst::PHOTOSEQUENCE_PHOTO_DESCRIPTION));
        elements.append(new QuTextEdit(
                            photo->fieldRef(PhotoSequencePhoto::DESCRIPTION)));
        elements.append(new QuPhoto(photo->blobFieldRef(
                                PhotoSequencePhoto::PHOTO_BLOBID, false)));
    }
    page->clearElements();
    page->addElements(elements);
    page->setTitle(QString("%1 %2 %3 %4")
                   .arg(textconst::PHOTO)
                   .arg(page_index + 1)
                   .arg(textconst::OF)
                   .arg(m_photos.length()));
}


void PhotoSequence::renumberPhotos()
{
    // Fine to reset the number to something that doesn't change; the save()
    // call will do nothing.
    const int n = m_photos.size();
    for (int i = 0; i < n; ++i) {
        PhotoSequencePhotoPtr photo = m_photos.at(i);
        photo->setSeqnum(i + 1);
        photo->save();
    }
}


void PhotoSequence::addPhoto()
{
    bool one_is_empty = false;
    for (auto photo : m_photos) {
        if (photo->valueIsNull(PhotoSequencePhoto::PHOTO_BLOBID)) {
            one_is_empty = true;
            break;
        }
    }
    if (one_is_empty) {
        uifunc::alert(tr("A photo is blank; won’t add another"));
        return;
    }
    PhotoSequencePhotoPtr photo(new PhotoSequencePhoto(
                                    pkvalueInt(), m_app, m_db));
    photo->setSeqnum(m_photos.size());
    photo->save();
    m_photos.append(photo);
    if (m_photos.size() > 1) {
        addPage(m_photos.size() - 1);
    }
    // Makes UI sense to go the one we've just added.
    m_questionnaire->goToPage(m_photos.size() - 1);
    refreshQuestionnaire();
}


void PhotoSequence::deletePhoto(const int index)
{
    if (index < 0 || index >= m_photos.size()) {
        return;
    }
    PhotoSequencePhotoPtr photo = m_photos.at(index);
    photo->deleteFromDatabase();
    m_photos.removeAt(index);
    renumberPhotos();
    m_questionnaire->deletePage(index);
    refreshQuestionnaire();
}


void PhotoSequence::movePhotoForwards(const int index)
{
    qDebug() << Q_FUNC_INFO << index;
    if (index < 0 || index >= m_photos.size() - 1) {
        return;
    }
    std::swap(m_photos[index], m_photos[index + 1]);
    renumberPhotos();
    // We need the pages to be re-titled as well as shuffled.
    // So the simplest way is to leave the pages in place and rework them.
    rebuildPage(m_questionnaire->pagePtr(index), index);
    rebuildPage(m_questionnaire->pagePtr(index + 1), index + 1);
    m_questionnaire->goToPage(index + 1);
    refreshQuestionnaire();
}


void PhotoSequence::movePhotoBackwards(const int index)
{
    qDebug() << Q_FUNC_INFO << index;
    if (index < 1 || index >= m_photos.size()) {
        return;
    }
    std::swap(m_photos[index - 1], m_photos[index]);
    renumberPhotos();
    rebuildPage(m_questionnaire->pagePtr(index - 1), index - 1);
    rebuildPage(m_questionnaire->pagePtr(index), index);
    m_questionnaire->goToPage(index - 1);
    refreshQuestionnaire();
}
