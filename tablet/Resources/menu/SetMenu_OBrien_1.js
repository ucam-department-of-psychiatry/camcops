// SetMenu_OBrien_1.js

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

/*jslint node: true, newcap: true */
"use strict";
/*global L */

module.exports = function SetMenu_OBrien_1() {

    var MenuWindow = require('menulib/MenuWindow'),
        UICONSTANTS = require('common/UICONSTANTS'),
        ALLTASKS = require('common/ALLTASKS'),
        data = [
            UICONSTANTS.CHANGE_PATIENT_MENU_LINE,
            ALLTASKS.TASKLIST.ACE3,
            ALLTASKS.TASKLIST.CBI_R,
            ALLTASKS.TASKLIST.COPE_BRIEF,
            ALLTASKS.TASKLIST.HADS,
            ALLTASKS.TASKLIST.MDS_UPDRS,
            ALLTASKS.TASKLIST.ZBI12
        ],
        self = new MenuWindow({
            title: L('t_set_obrien_1'),
            subtitle: L('s_set_obrien_1'),
            data: data
        });

    return self;
};
