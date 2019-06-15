// MenuViewWrapper.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

function MenuViewWrapper(p) {

    var MenuHeaderView = require('menulib/MenuHeaderViewWrapper'),
        MenuTableView = require('menulib/MenuTableViewWrapper'),
        UICONSTANTS = require('common/UICONSTANTS'),
        header_table_view_bottom,
        header_table_view,
        footerlabel;

    if (p.addfooter === undefined) { p.addfooter = false; }
    // other properties:
    //      fnBackClicked
    // other properties, passed to MenuHeaderView:
    //      backbutton
    //      icon
    //      title
    //      subtitle
    //      patient_id
    //      patientline
    //      fnBackClicked
    // other properties, passed to MenuTableView:
    //      data

    header_table_view_bottom = (
        p.addfooter ? UICONSTANTS.FOOTER_HEIGHT + UICONSTANTS.SPACE * 2 : 0
    );
    // http://stackoverflow.com/questions/9342303/titanium-mobile-relative-layout

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        backgroundColor: UICONSTANTS.MENU_BG_COLOUR
    });
    // Don't bother with an android:back listener: the Window gets those
    // messages, not the View.

    header_table_view = Titanium.UI.createView({
        top: 0,
        bottom: header_table_view_bottom,
        layout: 'vertical'
    });

    this.header = new MenuHeaderView({
        backbutton: p.backbutton,
        icon: p.icon,
        title: p.title,
        subtitle: p.subtitle,
        patient_id: p.patient_id,
        patientline: p.patientline,
        fnBackClicked: p.fnBackClicked
    });
    header_table_view.add(this.header.tiview);

    this.tableview = new MenuTableView(p.data);
    header_table_view.add(this.tableview.tiview);

    this.tiview.add(header_table_view);

    if (p.addfooter) {
        footerlabel = Titanium.UI.createLabel({
            text: L('app_footer'),
            font: UICONSTANTS.FOOTER_FONT,
            color: UICONSTANTS.FOOTER_COLOUR,
            left: UICONSTANTS.SPACE,
            bottom: UICONSTANTS.SPACE,
            height: UICONSTANTS.FOOTER_HEIGHT,
            // ... Can't safely use Titanium.UI.SIZE, so set this correctly
            width: Titanium.UI.FILL
        });
        // To make a clickable URL, previously: horizontal view with three bits
        // of text; middle text had a 'click' event
        this.tiview.add(footerlabel);
        // ... Must add to the window (not a vertical view) or the bottom
        // property won't work as we wish
    }
}
MenuViewWrapper.prototype = {

    cleanup: function () {
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        this.header.cleanup();
        this.tableview.cleanup();
    }

};
module.exports = MenuViewWrapper;
