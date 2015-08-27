// SetMenu_FROM_LP.js

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

/*jslint node: true, newcap: true */
"use strict";
/*global L */

module.exports = function SetMenu_FROM_LP() {

    var MenuWindow = require('menulib/MenuWindow'),
        UICONSTANTS = require('common/UICONSTANTS'),
        ALLTASKS = require('common/ALLTASKS'),
        data = [
            UICONSTANTS.CHANGE_PATIENT_MENU_LINE,
            // ================================================================
            // GENERIC
            // ================================================================
            {
                maintitle: L('t_from_lp_generic'),
                labelOnly: true
            },
            ALLTASKS.TASKLIST.CGI_I,
            // CORE-10 -- copyright conditions prohibit
            ALLTASKS.TASKLIST.IRAC,
            ALLTASKS.TASKLIST.PATIENT_SATISFACTION,
            ALLTASKS.TASKLIST.FFT,
            ALLTASKS.TASKLIST.REFERRER_SATISFACTION_GEN,
            ALLTASKS.TASKLIST.REFERRER_SATISFACTION_SPEC,
            // ================================================================
            // SPECIFIC
            // ================================================================
            {
                maintitle: L('t_from_lp_specific'),
                labelOnly: true
            },
            ALLTASKS.TASKLIST.ACE3,
            ALLTASKS.TASKLIST.PHQ9,
            // EPDS -- Royal College not currently permitting use
            ALLTASKS.TASKLIST.GAD7,
            ALLTASKS.TASKLIST.HONOS,
            ALLTASKS.TASKLIST.AUDIT_C,
            ALLTASKS.TASKLIST.BMI
            // *** EQ-5D-5L, if permitted?
        ],
        self = new MenuWindow({
            title: L('t_set_from_lp'),
            subtitle: L('s_set_from_lp'),
            data: data
        });

    return self;
};
