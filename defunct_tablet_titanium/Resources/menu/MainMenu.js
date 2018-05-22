// MainMenu.js

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

module.exports = function MainMenu() {

    var MenuWindow = require('menulib/MenuWindow'),
        platform = require('lib/platform'),
        UICONSTANTS = require('common/UICONSTANTS'),
        data,
        self;

    function upload() {
        var uifunc = require('lib/uifunc');
        uifunc.upload(self.tiview);
    }

    data = [
        UICONSTANTS.CHANGE_PATIENT_MENU_LINE,
        {
            maintitle: L('menutitle_patient_summary'),
            icon: UICONSTANTS.ICON_PATIENT_SUMMARY,
            window: 'screen/PatientSummaryWindow'
        },
        {
            maintitle: L('menutitle_upload'),
            icon: UICONSTANTS.ICON_UPLOAD,
            func: upload,
            unsupported: (!platform.isDatabaseSupported)
        },
        {
            maintitle: L('menutitle_help'),
            icon: UICONSTANTS.ICON_MENU_HELP,
            window: 'menu/HelpMenu'
        },
        {
            maintitle: L('menutitle_settings'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_SETTINGS,
            window: 'menu/SettingsMenu',
            notIfLocked: true
        },
        {
            maintitle: L('menutitle_clinical'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_CLINICAL,
            window: 'menu/ClinicalMenu'
        },
        {
            maintitle: L('menutitle_global'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_GLOBAL,
            window: 'menu/GlobalMenu'
        },
        {
            maintitle: L('menutitle_cognitive'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_COGNITIVE,
            window: 'menu/CognitiveMenu'
        },
        {
            maintitle: L('menutitle_affective'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_AFFECTIVE,
            window: 'menu/AffectiveMenu'
        },
        {
            maintitle: L('menutitle_addiction'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_ADDICTION,
            window: 'menu/AddictionMenu'
        },
        {
            maintitle: L('menutitle_psychosis'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_PSYCHOSIS,
            window: 'menu/PsychosisMenu'
        },
        {
            maintitle: L('menutitle_catatonia_epse'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_CATATONIA,
            window: 'menu/CatatoniaEpseMenu'
        },
        {
            maintitle: L('menutitle_personality'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_PERSONALITY,
            window: 'menu/PersonalityMenu'
        },
        {
            maintitle: L('menutitle_executive'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_EXECUTIVE,
            window: 'menu/ExecutiveMenu'
        },
        {
            maintitle: L('menutitle_research'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_RESEARCH,
            window: 'menu/ResearchMenu'
        },
        {
            maintitle: L('menutitle_anonymous'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_ANONYMOUS,
            window: 'menu/AnonymousMenu'
        },
        {
            maintitle: L('menutitle_sets_clinical'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_SETS_CLINICAL,
            window: 'menu/ClinicalSetsMenu'
        },
        {
            maintitle: L('menutitle_sets_research'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_SETS_RESEARCH,
            window: 'menu/ResearchSetsMenu'
        },
        {
            maintitle: L('menutitle_alltasks'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_MENU_ALLTASKS,
            window: 'menu/AllTasksMenu'
        }
    ];

    self = new MenuWindow({
        title: L('app_long_title'),
        backbutton: false,
        icon: UICONSTANTS.ICON_CAMCOPS,
        data: data,
        addfooter: false,
        exitOnClose: true // special for the top menu
    });

    return self;
};
