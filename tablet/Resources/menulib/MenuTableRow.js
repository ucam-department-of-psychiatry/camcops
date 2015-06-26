// MenuTableRow.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

module.exports = function MenuTableRow(rowdata) {
    // properties used exclusively here:
    //      icon
    //      subtitle
    //      arrowOnRight
    //      copyrightDetailsPending
    // properties passed to Titanium.UI.createTableViewRow and read by
    // MenuTableView:
    //      maintitle
    //      notImplemented
    //      unsupported
    //      crippled
    //      needsPrivilege
    //      notIfLocked
    //      window
    //      event
    //      func
    //      task
    //      html
    //      rowType
    //      info
    //      chain
    //      chainList
    //      labelOnly
    // Things are not auto-passed or we get a mess (e.g. "title").
    // VARIABLES ARE PASSED IN BY: TaskSelectorWindow, MenuTableView
    // and read out by the same.

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        i,
        rowprops,
        self,
        iconleft = UICONSTANTS.SPACE,
        textleft,
        iconVerticalLayout,
        icon,
        absentIconSpacer,
        textVerticalLayout,
        primaryLabel,
        secondaryLabel,
        backgroundColor;

    //Titanium.API.trace("MenuTableRow() - parameters: " +
    //                   JSON.stringify(rowdata));

    if (rowdata.chain) {
        if (!rowdata.icon) {
            rowdata.icon = UICONSTANTS.ICON_CHAIN;
        }
        if (rowdata.chainList === undefined ||
                rowdata.chainList.length === 0) {
            throw new Error("MenuTableRow: chain item attempted with " +
                            "invalid chainList");
        }
        if (!rowdata.maintitle) {
            rowdata.maintitle = "";
            for (i = 0; i < rowdata.chainList.length; ++i) {
                if (i > 0) {
                    rowdata.maintitle += " → ";
                }
                rowdata.maintitle += rowdata.chainList[i].title;
            }
        }
        if (!rowdata.subtitle) {
            rowdata.subtitle = L('s_generic_chain');
        }
    }

    if (rowdata.notImplemented || rowdata.unsupported || rowdata.labelOnly) {
        backgroundColor = UICONSTANTS.ROW_NOT_IMPLEMENTED_BACKGROUND_COLOUR;
    } else if (rowdata.copyrightDetailsPending) {
        backgroundColor = UICONSTANTS.COPYRIGHT_DETAILS_PENDING_BACKGROUND_COLOUR;
    } else {
        backgroundColor = UICONSTANTS.MENU_BG_COLOUR;  // the default
    }

    rowprops = {
        height: 'auto',
        // ... TITANIUM BUG (July 2012): Titanium.UI.SIZE doesn't work.
        width: Titanium.UI.FILL,
        className: (rowdata.icon ?
                    (rowdata.subtitle ? "rc1_cmlr" : "rc2_cmlr") :
                    (rowdata.subtitle ? "rc3_cmlr" : "rc4_cmlr")),
        // ... different view structure => need different className
        touchEnabled: true,
        backgroundColor: backgroundColor,
        // Now pass things on:
        maintitle: rowdata.maintitle,
        notImplemented: rowdata.notImplemented,
        unsupported: rowdata.unsupported,
        crippled: rowdata.crippled,
        needsPrivilege: rowdata.needsPrivilege,
        notIfLocked: rowdata.notIfLocked,
        window: rowdata.window,
        event: rowdata.event,
        func: rowdata.func,
        task: rowdata.task,
        html: rowdata.html,
        rowType: rowdata.rowType,
        info: rowdata.info,
        chain: rowdata.chain,
        chainList: rowdata.chainList,
        labelOnly: rowdata.labelOnly,
    };
    if (rowdata.arrowOnRight) {
        rowprops.rightImage = UICONSTANTS.ICON_TABLE_CHILDARROW;
    }
    self = Titanium.UI.createTableViewRow(rowprops);

    textleft = (
        rowdata.icon ?
                (2 * UICONSTANTS.SPACE + UICONSTANTS.ICONSIZE) :
                UICONSTANTS.SPACE
    );

    // IT IS CRITICAL THAT CHILDREN OF THE ROW ARE *NOT* TOUCH-ENABLED (i.e.
    // have "touchEnabled: false"). OTHERWISE:
    // (a) the Android selection colour won't appear properly;
    // (b) all the children have to have row index information, to pass it on
    //     in the event that they're clicked.

    if (rowdata.icon) {
        iconVerticalLayout = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: UICONSTANTS.ICONSIZE,
            left: iconleft,
            center: {y: '50%'},
            layout: 'vertical',
            touchEnabled: false,
        });
        icon = Titanium.UI.createImageView({
            image: rowdata.icon,
            height: UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.ICONSIZE,
            top: UICONSTANTS.SPACE,
            left: 0,
            touchEnabled: false,
        });
        iconVerticalLayout.add(icon);
        iconVerticalLayout.add(uifunc.createVerticalSpacer());
        self.add(iconVerticalLayout);
    } else {
        // Ensure all rows are always as tall as they would be with an icon
        // present
        absentIconSpacer = Titanium.UI.createView({
            height: UICONSTANTS.SPACE * 2 + UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.SPACE,
            left: 0,
            center: {y: '50%'},
            touchEnabled: false,
        });
        self.add(absentIconSpacer);
    }

    textVerticalLayout = Titanium.UI.createView({
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
        left: textleft,
        center: {y: '50%'},
        layout: 'vertical',
        touchEnabled: false,
    });
    primaryLabel = Titanium.UI.createLabel({
        text: rowdata.maintitle,
        font: UICONSTANTS.ROW_TITLE_FONT,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        color: UICONSTANTS.ROW_TITLE_COLOUR,
        top: UICONSTANTS.SPACE,
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
        touchEnabled: false,
    });
    textVerticalLayout.add(primaryLabel);

    if (rowdata.subtitle) {
        secondaryLabel = Titanium.UI.createLabel({
            text: rowdata.subtitle,
            font: UICONSTANTS.ROW_SUBTITLE_FONT,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            color: UICONSTANTS.ROW_SUBTITLE_COLOUR,
            top: 0,
            left: 0,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
            touchEnabled: false,
        });
        textVerticalLayout.add(secondaryLabel);
    }
    textVerticalLayout.add(uifunc.createVerticalSpacer());

    self.add(textVerticalLayout);

    return self;
};
