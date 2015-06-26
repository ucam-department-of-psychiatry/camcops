// PhotoSequence.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    maintablename = "photosequence",
    mainfieldlist = dbcommon.standardTaskFields(),
    phototablename = "photosequence_photos",
    PHOTOTABLE_FK_FIELDNAME = "photosequence_id", // FK to photosequence.id
    PHOTOTABLE_FK_FIELD = {
        name: PHOTOTABLE_FK_FIELDNAME,
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to photosequence.id
    photofieldlist = dbcommon.standardAncillaryFields(PHOTOTABLE_FK_FIELD);

mainfieldlist.push.apply(mainfieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
mainfieldlist.push(
    {name: "sequence_description", type: DBCONSTANTS.TYPE_TEXT}
);

photofieldlist.push(
    {name: "seqnum", type: DBCONSTANTS.TYPE_INTEGER, mandatory: true},
    {name: "description", type: DBCONSTANTS.TYPE_TEXT},
    {name: "photo_blobid", type: DBCONSTANTS.TYPE_BLOBID},
    {name: "rotation", type: DBCONSTANTS.TYPE_INTEGER, defaultValue: 90}
    // default rotation, since the primary use of this task is probably as a photocopier
);

// CREATE THE TABLES

dbcommon.createTable(maintablename, mainfieldlist);
dbcommon.createTable(phototablename, photofieldlist);

//=============================================================================
// Photo class
//=============================================================================

function SinglePhoto(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from
    // the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, PHOTOTABLE_FK_FIELDNAME,
                                   "seqnum");
}
lang.inheritPrototype(SinglePhoto, dbcommon.DatabaseObject);
lang.extendPrototype(SinglePhoto, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: SinglePhoto,
    _tablename: phototablename,
    _fieldlist: photofieldlist,
    _sortorder: "id",

    // OTHER

    getAllPhotos: function (photosequence_id) {
        return dbcommon.getAllRowsByKey(PHOTOTABLE_FK_FIELDNAME,
                                        photosequence_id, phototablename,
                                        photofieldlist, SinglePhoto, "id");
    },

});

//=============================================================================
// TASK
//=============================================================================

function comparePhotosBySeqNum(a, b) { // for sorting
    if (a.seqnum < b.seqnum) {
        return -1;
    }
    if (a.seqnum > b.seqnum) {
        return 1;
    }
    return 0;
}

function PhotoSequence(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(PhotoSequence, taskcommon.BaseTask);
lang.extendPrototype(PhotoSequence, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: PhotoSequence,
    _tablename: maintablename,
    _fieldlist: mainfieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Override dbdelete():
    dbdelete: function () {
        // The subsidiary table. First, because they may have BLOBs:
        var dummy_sp = new SinglePhoto(),
            my_photos = dummy_sp.getAllPhotos(this.id),
            i;
        for (i = 0; i < my_photos.length; ++i) {
            my_photos[i].dbdelete(); // should handle any owned BLOBs
        }
        // Then the usual:
        dbcommon.deleteByPK(maintablename, mainfieldlist[0], this);
        // No BLOBs owned by the main table.
    },

    // Override setMoveOffTablet():
    setMoveOffTablet: function (moveoff) {
        // The subsidiary table. First, because they may have BLOBs:
        var dummy_sp = new SinglePhoto(),
            my_photos = dummy_sp.getAllPhotos(this.id),
            i,
            DBCONSTANTS = require('common/DBCONSTANTS');
        for (i = 0; i < my_photos.length; ++i) {
            my_photos[i].setMoveOffTablet(moveoff);
            // should handle any owned BLOBs
        }
        // Then the usual:
        this[DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME] = moveoff;
        this.dbstore();
    },

    getMyPhotos: function () {
        var dummy_sp = new SinglePhoto();
        return dummy_sp.getAllPhotos(this.id);
    },

    numPhotos: function () {
        return this.getMyPhotos().length;
    },

    // Standard task functions
    isComplete: function () {
        return (this.numPhotos() > 0 && this.sequence_description);
    },

    getSummary: function () {
        var my_photos = this.getMyPhotos(),
            s = (this.sequence_description + " (" + L("photos") + ": " +
                 my_photos.length + ")" + this.isCompleteSuffix()),
            i;
        for (i = 0; i < my_photos.length; ++i) {
            // Human numbering:
            if (my_photos[i].description) {
                s += "\n" + (i + 1) + ": " + my_photos[i].description;
            }
        }
        return s;
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            my_photos,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        self.dbstore(); // generates self.id (needed as FK)
        my_photos = self.getMyPhotos();

        function resequence() {
            var i;
            for (i = 0; i < my_photos.length; ++i) {
                my_photos[i].seqnum = i;
                my_photos[i].dbstore();
            }
        }

        function resort() {
            my_photos.sort(comparePhotosBySeqNum);
        }

        function addPhoto() {
            // adds at the end
            // Titanium.API.trace("addPhoto: self.id == " + self.id);
            var photo = new SinglePhoto({ photosequence_id: self.id });
            // Titanium.API.trace("addPhoto: photo == " + JSON.stringify(photo));
            photo.seqnum = my_photos.length;
            photo.dbstore();
            my_photos.push(photo);
            questionnaire.setFocus(my_photos.length);
        }

        function quietlyDeletePhoto(photoIndex) {
            if (photoIndex < 0 || photoIndex >= my_photos.length) {
                return;
            }
            my_photos[photoIndex].dbdelete(); // will delete the BLOB
            my_photos.splice(photoIndex, 1); // remove that one element
            resequence();
            questionnaire.setFocus(photoIndex); // being the page *before* this index
        }

        function deletePhoto(photoIndex) {
            // Titanium.API.trace("deletePhoto: " + photoIndex);
            if (photoIndex < 0 || photoIndex >= my_photos.length) {
                return;
            }
            var dlg = Titanium.UI.createAlertDialog({
                title: L('photosequence_delete_q'),
                message: (
                    L('photosequence_delete_q') + " " + (photoIndex + 1) +
                    " " + L("of") + " " + my_photos.length + "?"
                ),
                buttonNames: [L('cancel'), L('delete')],
            });
            dlg.addEventListener('click', function (e) {
                if (e.index === 1) { // Delete
                    quietlyDeletePhoto(photoIndex);
                }
                dlg = null;
            });
            dlg.show();
        }

        function moveBackwards(photoIndex) {
            // Titanium.API.trace("moveBackwards: " + photoIndex);
            if (photoIndex <= 0 || photoIndex >= my_photos.length) {
                return;
            }
            var precedingIndex = photoIndex - 1;
            my_photos[precedingIndex].seqnum = photoIndex;
            my_photos[precedingIndex].dbstore();
            my_photos[photoIndex].seqnum = precedingIndex;
            my_photos[photoIndex].dbstore();
            resort();
            questionnaire.setFocus(1 + precedingIndex);
        }

        function moveForwards(photoIndex) {
            // Titanium.API.trace("moveForwards: " + photoIndex);
            if (photoIndex < 0 || photoIndex >= my_photos.length - 1) {
                return;
            }
            var followingIndex = photoIndex + 1;
            my_photos[photoIndex].seqnum = followingIndex;
            my_photos[photoIndex].dbstore();
            my_photos[followingIndex].seqnum = photoIndex;
            my_photos[followingIndex].dbstore();
            resort();
            questionnaire.setFocus(1 + followingIndex);
        }

        function getNumPages() {
            return my_photos.length + 1;
        }

        function makePage(pageId) {
            // ignore pageTag since allPagesOnTheFly == true
            var elements = [],
                index = pageId - 1,
                isFirst = (index === 0),
                isLast = (index === my_photos.length - 1);
            if (pageId === 0) {
                // First page
                elements = [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionTypedVariables",
                        mandatory: true,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "sequence_description",
                                prompt: L("photosequence_description_sequence")
                            },
                        ],
                    },
                ];
                if (my_photos.length === 0) {
                    elements.push(
                        {
                            type: "QuestionButton",
                            text: L("photosequence_add"),
                            fnClicked: addPhoto
                        }
                    );
                }
                return {
                    title: (L('photosequence_title') + " (" + L("photos") +
                            ": " + my_photos.length + ")"),
                    clinician: true,
                    elements: elements,
                };
            }

            if (pageId < 0 || pageId > my_photos.length) {
                Titanium.API.trace("Error: PhotoSequence.edit.makePage " +
                                   "called with invalid pageId");
                return {};
            }

            return {
                title: (L("Photo") + " " + pageId + " " + L("of") + " " +
                        my_photos.length),
                clinician: true,
                elements: [
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionButton",
                                text: L("photosequence_add"),
                                inactive: !isLast,
                                fnClicked: addPhoto
                            },
                            {
                                type: "QuestionButton",
                                text: L("photosequence_delete"),
                                fnClicked: function () {
                                    deletePhoto(index);
                                }
                            },
                            {
                                type: "QuestionButton",
                                text: L("photosequence_move_back"),
                                inactive: isFirst,
                                fnClicked: function () {
                                    moveBackwards(index);
                                }
                            },
                            {
                                type: "QuestionButton",
                                text: L("photosequence_move_forwards"),
                                inactive: isLast,
                                fnClicked: function () {
                                    moveForwards(index);
                                }
                            },
                        ],
                    },
                    { type: "QuestionText", text: L('photo_q') },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "description" + index,
                                prompt: L("photosequence_description_photo")
                            },
                        ],
                    },
                    {
                        type: "QuestionPhoto",
                        field: "photo_blobid" + index,
                        mandatory: false,
                        offerDeleteButton: false,
                        rotationField: "rotation" + index
                    },
                ],
            };
        }

        function parseFieldText(field) {
            var split = 0,
                photoIndex;
            if (field.substring(0, "photo_blobid".length) === "photo_blobid") {
                split = "photo_blobid".length;
            } else if (field.substring(0, "description".length) === "description") {
                split = "description".length;
            } else if (field.substring(0, "rotation".length) === "rotation") {
                split = "rotation".length;
            }
            if (split === 0) {
                return {
                    field: field,
                    photoIndex: null
                };
            }
            photoIndex = parseInt(field.substring(split), 10);
            if (isNaN(photoIndex) || photoIndex < 0 ||
                    photoIndex >= my_photos.length) {
                photoIndex = null;
            }
            return {
                field: field.substring(0, split),
                photoIndex: photoIndex
            };
        }

        function setField(field, value) {
            var fieldinfo = parseFieldText(field);
            if (fieldinfo.photoIndex !== null) {
                my_photos[fieldinfo.photoIndex].defaultSetFieldFn(
                    fieldinfo.field,
                    value
                );
                self.touch(); // IMPORTANT. Otherwise a photo might change
                // without creating a new server-side version of the task.
            } else {
                self.defaultSetFieldFn(fieldinfo.field, value);
            }
        }

        function getField(fieldname, getBlobsAsFilenames) {
            var fieldinfo = parseFieldText(fieldname);
            if (fieldinfo.photoIndex !== null) {
                return my_photos[fieldinfo.photoIndex].defaultGetFieldValueFn(
                    fieldinfo.field,
                    getBlobsAsFilenames
                );
            }
            return self.defaultGetFieldValueFn(fieldinfo.field,
                                               getBlobsAsFilenames);
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            allPagesOnTheFly: true,
            pages: [], // all on the fly
            callbackThis: self,
            fnGetFieldValue: getField,
            fnSetField: setField,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have
                // closures referring to questionnaire
            },
            fnGetNumPages: getNumPages,
            fnMakePageOnTheFly: makePage
        });
        questionnaire.open();
    },

});

module.exports = PhotoSequence;
