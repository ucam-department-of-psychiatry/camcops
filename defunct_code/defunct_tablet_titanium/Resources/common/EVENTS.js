// EVENTS.js
// Application-wide events

/*
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

/*jslint node: true */

module.exports = {
    PATIENT_EDIT_SAVE: 'PATIENT_EDIT_SAVE',
    PATIENT_CHOSEN: 'PATIENT_CHOSEN',
    PATIENT_LOCK_CHANGED: 'PATIENT_LOCK_CHANGED',

    TASK_FINISHED: 'TASK_FINISHED',

    WHISKER_STATUS_CHANGED: 'WHISKER_STATUS_CHANGED',
    WHISKER_EVENT: 'WHISKER_EVENT'
};
