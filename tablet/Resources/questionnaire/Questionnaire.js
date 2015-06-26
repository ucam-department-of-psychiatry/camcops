// Questionnaire.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var MODULE_NAME = "Questionnaire";

var qcommon = require('questionnairelib/qcommon');
var UICONSTANTS = require('common/UICONSTANTS');

function createSpacerView() {
    return Titanium.UI.createView({
        height: UICONSTANTS.BIGSPACE,
        width: Titanium.UI.FILL,
        touchEnabled: false,
        // backgroundColor: COLOURS.RED,
    });
}

function createElementContainer(disableScroll) {
    // var COLOURS = require('common/COLOURS');
    // disableScroll = true;
    if (disableScroll) {
        return Titanium.UI.createView({
            left: UICONSTANTS.BIGSPACE,
            right: UICONSTANTS.BIGSPACE,
            top: 0,
            height: Titanium.UI.FILL,
            layout: 'vertical',
            // backgroundColor: COLOURS.GREEN,
        });
    }
    return Titanium.UI.createScrollView({
        left: UICONSTANTS.BIGSPACE,
        right: UICONSTANTS.BIGSPACE,
        top: 0,
        // height: '90%', // I've not been able to get the height right
        // without making the scrollview scroll even when its content is
        // too small to justify scrolling.
        height: Titanium.UI.FILL, // working in Jan 2014 (Titanium 3.2.0)
        layout: 'vertical',

        scrollType: 'vertical',
        contentHeight: 'auto',
        showVerticalScrollIndicator: true,
        showHorizontalScrollIndicator: false,
        horizontalWrap: false,
        disableBounce: true,
        horizontalBounce: false,

        // backgroundColor: COLOURS.GREEN,
    });
    /*
    Problem Feb 2014 (Titanium 3.2.0 and 3.2.1): scrolling horizontally even
    when told not to. Occurs with long (wrapping) text. Completely replicable
    within Questionnaire framework Can't replicate it with a simple piece of
    code, though (bugtest_horizontal_scroll_bigtext.jsx). Behaviour changes
    when you use "disableBounce: true", so it's probably a bug with that.
    *** CURRENT BUG with scrollview, I blame Titanium, but it's hard to
    replicate in simple code.
    */
}

/*jslint unparam: true */
function setDefaultPageProperties(pageprops, pageIndex, npages, readonly) {
    /*
        optional page property: pageTag
        optional page property: nextprogression
        usual property: elements
        ... sub-property for each element: type
        ... optional sub-property for each element: elementTag
        ... (other properties passed to constructor determined by type)
    */
    qcommon.setDefaultProperty(pageprops, "clinician", false);
    qcommon.setDefaultProperty(pageprops, "clinicianAssisted", false);
    qcommon.setDefaultProperty(pageprops, "config", false);
    qcommon.setDefaultProperty(pageprops, "disableScroll", false);
    qcommon.setDefaultProperty(pageprops, "title",
                               L('question') + " " + (pageIndex + 1) + " " +
                               L('of') + " " + npages);
    // if (readonly) { pageprops.title += " " + L('read_only_suffix'); }
}
/*jslint unparam: false */

function addElements(currentview, elements) {
    // Create/add element objects
    Titanium.API.info("Questionnaire: adding " + elements.length +
                      " elements");
    var i,
        newElement;
    for (i = 0; i < elements.length; ++i) {
        qcommon.setDefaultHorizontalPosLeft(elements[i], 0);
        qcommon.setDefaultVerticalPosTop(elements[i], UICONSTANTS.BIGSPACE);
        newElement = qcommon.makeElement(elements[i]);
        currentview.elements.push(newElement);
        currentview.elementcontainer.add(newElement.tiview);
        newElement.applyVisible();
    }
    // currentview.elementcontainer.add( createSpacerView() );
    // ... PUT THIS BACK if we fix the scrollview's height problems.
}

//-------------------------------------------------------------------------
// Code to talk to all elements, even those within sub-containers.
// An elementcontainer is something with an array "elements" in it.
//-------------------------------------------------------------------------
function callFnForAllElements(elements, func, param) {
    // Recursive; can extend to any max number of parameters
    var i;
    for (i = 0; i < elements.length; ++i) {
        func(elements[i], param);
        if (elements[i].elements !== undefined) {
            callFnForAllElements(elements[i].elements, func, param);
        }
    }
}

function callMemberFnForAllElements(elements, funcname, param) {
    // Recursive
    var i;
    for (i = 0; i < elements.length; ++i) {
        if (typeof elements[i][funcname] === "function") {
            elements[i][funcname](param);
            // call function funcname() belonging to the element
        }
        if (elements[i].elements !== undefined) {
            callMemberFnForAllElements(elements[i].elements, funcname, param);
        }
    }
}

function callMemberFnForAllElementsById(elements, elementId, funcname, param) {
    // Recursive
    var i;
    for (i = 0; i < elements.length; ++i) {
        if (typeof elements[i][funcname] === "function" &&
                elements[i].elementId !== undefined) {
            if (elements[i].elementId === elementId) {
                elements[i][funcname](param);
                // call function funcname() belonging to the element
            }
        }
        if (elements[i].elements !== undefined) {
            callMemberFnForAllElementsById(elements[i].elements, elementId,
                                           funcname, param);
        }
    }
}

function callMemberFnForAllElementsByTag(elements, elementTag, funcname,
                                         param1, param2) {
    // Recursive
    var i;
    for (i = 0; i < elements.length; ++i) {
        if (typeof elements[i][funcname] === "function" &&
                elements[i].elementTag !== undefined) {
            if (elements[i].elementTag === elementTag) {
                elements[i][funcname](param1, param2);
                // call function funcname() belonging to the element
            }
        }
        if (elements[i].elements !== undefined) {
            callMemberFnForAllElementsByTag(elements[i].elements, elementTag,
                                            funcname, param1, param2);
        }
    }
}

function elementwiseAnd(elements, funcname) { // Recursive
    var i;
    for (i = 0; i < elements.length; ++i) {
        if (typeof elements[i][funcname] === "function") {
            if (!elements[i][funcname]()) {
                return false;
            }
        }
        if (elements[i].elements !== undefined) {
            if (!elementwiseAnd(elements[i].elements, funcname)) {
                return false;
            }
        }
    }
    return true;
}

function elementwiseOr(elements, funcname) { // Recursive
    var i;
    for (i = 0; i < elements.length; ++i) {
        if (typeof elements[i][funcname] === "function") {
            if (elements[i][funcname]()) {
                return true;
            }
        }
        if (elements[i].elements !== undefined) {
            if (elementwiseOr(elements[i].elements, funcname)) {
                return true;
            }
        }
    }
    return false;
}

function setElementValue(element, afterViewVisible) {
    if (typeof element.setFromField === "function") {
        // Some elements want their values set before the view is visible
        // (which looks smoother). Some crash (e.g. webview setting image, i.e.
        // QuestionCanvas), and need it after.
        // All should set their setValueOnlyAfterVisible property, via
        // qcommon.copyVitalPropsToSelf() if nowhere else.
        //
        // The other option is willSetOwnValueOnCreation (default false).

        if (afterViewVisible === element.setValueOnlyAfterVisible &&
                !element.willSetOwnValueOnCreation) {
            element.setFromField();
        }
    }
}

//-------------------------------------------------------------------------
// Questionnaire itself
//-------------------------------------------------------------------------

function Questionnaire(props) {

    var uifunc = require('lib/uifunc'),
        i,
        self = this;
    qcommon.requireProperty(props, "callbackThis", MODULE_NAME);
    // ... pass the "this" (or equivalent "self")
    // ... http://stackoverflow.com/questions/3127429/javascript-this-keyword
    // ... not inefficient: http://stackoverflow.com/questions/518000
    qcommon.requireFunctionProperty(props, "fnGetFieldValue", MODULE_NAME);
    // ... function (fieldname, getBlobsAsFilenames) { ... }
    qcommon.requireFunctionProperty(props, "fnFinished", MODULE_NAME);
    // ... function (result, editing_time_s) { ... }
    // ... called IMMEDIATELY BEFORE the questionnaire window closes; however,
    //     if you pop up dialogues or the like, the questionnaire may have
    //     closed before they can open.
    qcommon.setDefaultProperty(props, "orientationModes", []);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "allPagesOnTheFly", false);
    qcommon.setDefaultProperty(props, "okIconAtEnd", false);
    qcommon.setDefaultProperty(props, "allowPageJumpDuringEditing", true);
    qcommon.requireProperty(props, "pages", MODULE_NAME);
    if (props.allPagesOnTheFly) {
        if (typeof props.fnGetNumPages !== "function") {
            throw new Error("Questionnaire: allPagesOnTheFly == true, but " +
                            "missing fnGetNumPages");
        }
        if (typeof props.fnMakePageOnTheFly !== "function") {
            throw new Error("Questionnaire: allPagesOnTheFly == true, but " +
                            "missing fnMakePageOnTheFly");
        }
    }
    for (i = 0; i < props.pages.length; ++i) {
        setDefaultPageProperties(props.pages[i], i, props.pages.length,
                                 props.readOnly);
    }
    /*
        other optional questionnaire properties:

        fnMakePageOnTheFly: function (pageId, pageTag) {
            // ... pageTag == null if allPagesOnTheFly == true
            return PAGEPROPS;
        },
        fnGetNumPages: function () {
            // ... called when allPagesOnTheFly == true
            return NUMPAGES;
        },
        fnSetField: function (field, value) { ... },
        fnShowNext: function (currentPage, pageTag) {
            if (wewant) {
                questionnaire.setMandatoryByTag(elementTag, mandatory,
                                                extraParam);
            }
            else (maybe) {
                questionnaire.setFromFieldByTag(elementTag);
            }
            return { care: DO_WE_CARE_BOOL, showNext: SHOW_NEXT_BOOL };
            // RATIONALE: fnShowNext may do more complex processing than simple
            // mandatory-or-not.
            // NB: calling setMandatoryByTag() will often allow you to
            /       return { care: false };
            // as the framework will then re-process based on the new mandatory
            // states.
        },
        fnShowBack: function (currentPage, pageTag) {
            return { care: DO_WE_CARE_BOOL, showBack: SHOW_BACK_BOOL };
        },
        fnNextPage: function (sourcePageId, pageTag) {
            return NEW_PAGE_NUMBER_ZERO_BASED;
        },
        fnPreviousPage: function (sourcePageId, pageTag) {
            return NEW_PAGE_NUMBER_ZERO_BASED;
        },
    */

    this.props = props;
    this.editing_time_start = null;
    this.tiview = uifunc.createQuestionnaireWindow(props.orientationModes);
    this.wait = uifunc.createWait({ window: this.tiview });
    this.currentview = null;
    this.currentPage = 0;
    this.lastPageValidatedForJump = 0;
    /*
        Hard to precalculate the last page to which a jump is allowed,
        because the current isNextAllowed code allows interaction with existing
        UI elements (i.e. they look at the UI contents, not just the field
        contents), and the UI elements have not yet been set up.
        So this would be a significant bit of reworking.
        Look at e.g. the CECAQ3 for a complex example.
        Barring this, what we get easily is the ability to jump to the last
        page that we've seen during this edit that allows us to proceed;
        see lastPageToWhichJumpAllowed().
    */
    this.androidBackListener = function () {
        self.pageAbort();
    };
    this.tiview.addEventListener('android:back', this.androidBackListener);
    this.openListener = function () {
        self.setFocus(self.currentPage);
    };
    // ... don't call before we open the questionnaire, or fnShowNext callbacks
    // to e.g. setMandatoryByTag fail (because the questionnaire object hasn't
    // been fully created yet)
    this.tiview.addEventListener('open', this.openListener);
    this.relayEventListener = function (e) {
        self.relayEventToElement(e);
    };
    Titanium.App.addEventListener(UICONSTANTS.EVENT_TO_ELEMENT,
                                  this.relayEventListener);
    // ... should have a matching removeEventListener call somewhere
    // Avoid memory leaks:
    // http://docs.appcelerator.com/titanium/2.0/index.html#!/guide/Managing_Memory_and_Finding_Leaks
    this.jumpDialog = null;
    this.jumpListener = null;
}
Questionnaire.prototype = {

    cleanup: function () {
        var uifunc = require('lib/uifunc'),
            imagecache = require('lib/imagecache');
        imagecache.clearCache();
        if (this.currentView) {
            uifunc.removeAllViewChildren(this.currentView);
            this.currentView = null;
        }
        this.tiview.removeEventListener('open', this.openListener);
        this.openListener = null;
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        Titanium.App.removeEventListener(UICONSTANTS.EVENT_TO_ELEMENT,
                                         this.relayEventListener);
        this.relayEventListener = null;
        this.cleanupJump();
    },

    cleanupJump: function () {
        if (this.jumpDialog) {
            this.jumpDialog.removeEventListener("click", this.jumpListener);
            this.jumpListener = null;
            this.jumpDialog = null;
        }
    },

    open: function () {
        var moment = require('lib/moment');
        this.editing_time_start = moment();
        this.tiview.open();
    },

    close: function () {
        this.tiview.close();
        this.cleanup();
    },

    showWait: function () {
        this.wait.show();
    },

    hideWait: function () {
        this.wait.hide();
    },

    // Number of pages
    numPages: function () {
        if (!this.props.allPagesOnTheFly) {
            return this.props.pages.length;
        }
        return this.props.fnGetNumPages.call(this.props.callbackThis);
    },

    final_finish: function (result) {
        var moment,
            editing_time_end,
            editing_time_s = 0;
        if (!this.props.readOnly && this.editing_time_start !== null) {
            // Read-only viewing doesn't alter the editing time.
            moment = require('lib/moment');
            editing_time_end = moment();
            editing_time_s = editing_time_end.diff(this.editing_time_start,
                                                   'seconds',
                                                   true);  // floating-point
        }
        this.props.fnFinished.call(this.props.callbackThis,
                                   result,
                                   editing_time_s);
        this.close(); // will call cleanup
    },

    allowJump: function (numPages) {
        return (
            (this.props.readOnly || this.props.allowPageJumpDuringEditing) &&
            numPages > 1
        );
    },

    lastPageToWhichJumpAllowed: function () {
        if (this.props.readOnly) {
            return this.numPages() - 1;
        }
        return this.lastPageValidatedForJump;
    },

    //-------------------------------------------------------------------------
    // Creation
    //-------------------------------------------------------------------------

    setFocus: function (pageId) { // NB Titanium View method: setFocusable
        var QuestionnaireHeader = require(
                'questionnairelib/QuestionnaireHeader'
            ),
            uifunc = require('lib/uifunc'),
            np = this.numPages(),
            i,
            pageprops,
            self = this,
            headerprops;

        if (pageId < 0 || pageId >= np) {
            Titanium.API.info("Questionnaire.setFocus: invalid pageId");
            return;
        }
        if (this.currentview !== null) {
            this.tiview.remove(this.currentview.tiview);
            // try to be explicit for garbage collection:
            uifunc.removeAllViewChildren(this.currentview.tiview);
            this.currentview.tiview = null;
            this.currentview.header.cleanup();
            uifunc.removeAllViewChildren(this.currentview.elementcontainer);
            this.currentview.elementcontainer = null;
            for (i = 0; i < this.currentview.elements.length; ++i) {
                this.currentview.elements[i].cleanup_base();
                // ... will also call cleanup() for each one
            }
            this.currentview = null;
        }
        Titanium.API.info("Questionnaire: moving to page " + pageId);

        // Get properties for the new page
        if (this.props.allPagesOnTheFly ||
                (this.props.pages[pageId].onTheFly &&
                 typeof this.props.fnMakePageOnTheFly === "function")) {
            Titanium.API.info("Questionnaire: making page " + pageId +
                              " on the fly");
            pageprops = this.props.fnMakePageOnTheFly.call(
                this.props.callbackThis,
                pageId,
                (this.props.allPagesOnTheFly ?
                        null :
                        this.props.pages[pageId].pageTag
                )
            );
            setDefaultPageProperties(pageprops, pageId,
                                     this.props.pages.length,
                                     this.props.readOnly);
        } else {
            pageprops = this.props.pages[pageId];
        }

        // View
        headerprops = {
            title: pageprops.title,
            backAllowed: this.isBackAllowed(pageId),
            jumpAllowed: this.allowJump(np),
            readOnly: this.props.readOnly,
            firstQuestion: (pageId === 0),
            lastQuestion: (
                pageId === np - 1 ||
                pageprops.nextprogression === UICONSTANTS.FINISHED
            ),
            fnAbort: function () { self.pageAbort(); },
            fnNext: function () { self.pageNext(pageId); },
            fnBack: function () { self.pageBack(pageId); },
            fnJump: function () { self.pageJump(); },
            okIconAtEnd: this.props.okIconAtEnd,
        };
        if (pageprops.clinicianAssisted) {
            headerprops.backgroundColor = (
                this.props.readOnly ?
                        UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CLINICIAN_READONLY :
                        UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CLINICIAN
            );
        }
        this.currentview = {
            tiview: Titanium.UI.createView({
                top: 0,
                left: 0,
                height: Titanium.UI.FILL,
                width: Titanium.UI.FILL,
                backgroundColor: (
                    pageprops.config ?
                            UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CONFIG :
                            (this.props.readOnly ?
                                    (pageprops.clinician ?
                                            UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CLINICIAN_READONLY :
                                            UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_READONLY
                                    ) :
                                    (pageprops.clinician ?
                                            UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CLINICIAN :
                                            UICONSTANTS.QUESTIONNAIRE_BG_COLOUR
                                    )
                            )
                ),
                layout: 'vertical',
            }),
            header: new QuestionnaireHeader(headerprops),
            elements: [],
            elementcontainer: createElementContainer(pageprops.disableScroll),
        };
        this.currentview.tiview.add(this.currentview.header.tiview);
        this.currentview.tiview.add(uifunc.createQuestionnaireRule());
        this.currentview.tiview.add(this.currentview.elementcontainer);

        // Set element/page ID (etc.) for all element properties (recursively)
        this.setElementDetails(pageprops.elements, pageId, 0);
        // ... 0 being the starting element counter; will be incremented
        // recursively
        addElements(this.currentview, pageprops.elements);

        // It looks smoother if we pre-set elements where possible.
        this.setAllValues(false);
        // DO NOT attach the event listener to the questionview.
        // When the questionview has many members (e.g. LUNSERS), firing the
        // event causes crashes with many, many errors like
        //      !!! Unable to convert unknown Java object class
        //      'org.appcelerator.kroll.KrollRuntime$1' to Js value !!!
        // ... then a crash with
        //      JNI ERROR (app bug): local reference table overflow (max=512)

        // Make it visible
        this.tiview.add(this.currentview.tiview);

        // sendOpeningMessages();
        // Some things will want to set their values only after the view is
        // visible.
        this.setAllValues(true);
        this.callShowNext(); // only works after the view's been added to the
        // window and is visible

        this.hideWait();
        // Androiduitools.setFullscreen();
        Titanium.API.trace("Questionnaire: setFocus: all done");
    },

    setElementDetails: function (elements, pageId, elementIdCounter) {
        var i;
        for (i = 0; i < elements.length; ++i) {
            if (elements[i].type === undefined) {
                throw new Error("No type specified for page " + pageId +
                                ", element " + elementIdCounter);
            }
            elements[i].elementId = elementIdCounter++;
            elements[i].pageId = pageId;
            elements[i].questionnaire = this; // will be passed by reference:
            // http://snook.ca/archives/javascript/javascript_pass
            // The read-only property can also be set per element (but if it's
            // set for the page, all elements must be read-only):
            if (elements[i].readOnly === undefined || this.props.readOnly) {
                elements[i].readOnly = this.props.readOnly;
            }
            if (elements[i].elements !== undefined) {
                elementIdCounter = this.setElementDetails(elements[i].elements,
                                                          elementIdCounter);
            }
        }
        return elementIdCounter;
    },

    //-------------------------------------------------------------------------
    // Value changed: from questionnaire element to field
    //-------------------------------------------------------------------------
    setFieldValue: function (field, value) {
        Titanium.API.trace("Questionnaire.setFieldValue: field=" + field +
                           ", value=" + JSON.stringify(value));
        if (typeof this.props.fnSetField === "function") {
            this.props.fnSetField.call(this.props.callbackThis,
                                       field, value);
        }
        this.callShowNext();
    },

    // Read field value: from field to questionnaire element
    getFieldValue: function (field, getBlobsAsFilenames) {
        var v = this.props.fnGetFieldValue.call(this.props.callbackThis,
                                                field, getBlobsAsFilenames);
        if (v === undefined) {
            return null;
        }
        return v;
    },

    //-------------------------------------------------------------------------
    // Global event being directed to element
    //-------------------------------------------------------------------------
    relayEventToElement: function (e) {
        if (e.broadcastToAllElements) {
            Titanium.API.info("Questionnaire.relayEventToElement: " +
                              "broadcasting to all elements");
            callMemberFnForAllElements(this.currentview.elements,
                                       "eventToElement", e);
        } else {
            if (this.currentPage !== e.pageId || e.elementId < 0) {
                Titanium.API.info("Questionnaire.relayEventToElement: " +
                                  "invalid page/element ID");
                return;
            }
            Titanium.API.info("Questionnaire.relayEventToElement: passing " +
                              "to element " + e.elementId);
            callMemberFnForAllElementsById(this.currentview.elements,
                                           e.elementId, "eventToElement", e);
        }
    },

    //-------------------------------------------------------------------------
    // Communicate with elements
    //-------------------------------------------------------------------------
    setAllValues: function (afterViewVisible) {
        if (this.currentview === null) {
            Titanium.API.trace("... no currentview");
            return;
        }
        callFnForAllElements(this.currentview.elements, setElementValue,
                             afterViewVisible);
    },

    sendClosingMessages: function () {
        // Provide an onClose feature for any views that need to do special
        // cleanup (e.g. countdown timers).
        if (this.currentview === null) {
            return;
        }
        callMemberFnForAllElements(this.currentview.elements, "onClose");
    },

    sendOpeningMessages: function () {
        // Provide an onOpen feature for any views that need to do special
        // calculations (e.g. webviews).
        if (this.currentview === null) {
            return;
        }
        callMemberFnForAllElements(this.currentview.elements, "onOpen");
    },

    getPageTag: function (potentiallyInvalidPagenum) {
        var page = this.props.pages[potentiallyInvalidPagenum];
        // OK to index by something crazy, e.g. x[undefined], x[null],
        // but the result is undefined.
        if (page === undefined) {
            return undefined;
        }
        return page.pageTag;
    },

    isNextAllowed: function () {
        // If we have a user-defined function, and it cares, use that.
        var showNextResponse,
            inputRequired;
        if (typeof this.props.fnShowNext === "function") {
            Titanium.API.trace("isNextAllowed: custom fnShowNext");
            showNextResponse = this.props.fnShowNext.call(
                this.props.callbackThis,
                this.currentPage,
                this.getPageTag(this.currentPage)
            );
            if (showNextResponse.care) {
                return showNextResponse.showNext;
            }
        }
        // Otherwise, say yes unless one of our elements needs input.
        inputRequired = elementwiseOr(this.currentview.elements,
                                      "isInputRequired");
        return !inputRequired;
    },

    isBackAllowed: function (pageId) {
        // If we have a user-defined function, and it cares, use that.
        var showBackResponse;
        if (typeof this.props.fnShowBack === "function") {
            showBackResponse = this.props.fnShowBack.call(
                this.props.callbackThis,
                this.currentPage,
                this.getPageTag(this.currentPage)
            );
            if (showBackResponse.care) {
                return showBackResponse.showBack;
            }
        }
        // Otherwise:
        return (pageId > 0);
    },

    //-------------------------------------------------------------------------
    // Page controls
    //-------------------------------------------------------------------------
    callShowNext: function () {
        var nextAllowed = this.isNextAllowed();
        if (nextAllowed) {
            this.lastPageValidatedForJump = Math.max(
                Math.min(this.currentPage + 1, this.numPages() - 1),
                this.lastPageValidatedForJump
            );
        } else {
            this.lastPageValidatedForJump = this.currentPage;
        }
        this.currentview.header.showNext(nextAllowed);
    },

    pageAboutToClose: function () {
        Titanium.API.trace("Questionnaire.pageAboutToClose");
        this.showWait();
        this.sendClosingMessages();
    },

    pageAbort: function () {
        var self = this,
            dlg;
        if (this.props.readOnly) {
            this.pageAboutToClose();
            this.final_finish(UICONSTANTS.READONLYVIEWFINISHED);
        } else {
            dlg = Titanium.UI.createAlertDialog({
                title: L('abort_title'),
                message: L('abort_sure'),
                buttonNames: [L('cancel'), L('abort')],
                // *** For some reason, this dialog (alone) mis-sorts its
                // buttons... it puts "Abort" on the left.
            });
            dlg.addEventListener('click', function (e) {
                if (e.index === 1) { // Abort
                    self.pageAboutToClose();
                    self.final_finish(UICONSTANTS.ABORTED);
                }
                dlg = null;
                self = null;
            });
            dlg.show();
        }
    },

    pageBack: function (sourcePageId) {
        this.pageAboutToClose();
        if (typeof this.props.fnPreviousPage === "function") {
            this.currentPage = this.props.fnPreviousPage.call(
                this.props.callbackThis,
                sourcePageId,
                this.getPageTag(sourcePageId)
            );
            if (this.currentPage < 0) {
                this.final_finish(this.props.readOnly ?
                                  UICONSTANTS.READONLYVIEWFINISHED :
                                  UICONSTANTS.FINISHED);
                return;
            }
        } else {
            this.currentPage = sourcePageId - 1;
        }
        if (this.currentPage < 0) {
            this.currentPage = 0;
        }
        this.setFocus(this.currentPage);
    },

    pageNext: function (sourcePageId) {
        this.pageAboutToClose();
        if (typeof this.props.fnNextPage === "function") {
            this.currentPage = this.props.fnNextPage.call(
                this.props.callbackThis,
                sourcePageId,
                this.getPageTag(sourcePageId)
            );
            if (this.currentPage < 0) {
                this.final_finish(this.props.readOnly ?
                                  UICONSTANTS.READONLYVIEWFINISHED :
                                  UICONSTANTS.FINISHED);
                return;
            }
        } else {
            this.currentPage = sourcePageId + 1;
        }
        if (this.currentPage >= this.numPages()) { // "stop" button
            this.final_finish(this.props.readOnly ?
                              UICONSTANTS.READONLYVIEWFINISHED :
                              UICONSTANTS.FINISHED);
            return;
        }
        this.setFocus(this.currentPage);
    },

    pageJump: function () {
        var textOptions = [],
            lastJumpPage = this.lastPageToWhichJumpAllowed(),
            text,
            i,
            platform = require('lib/platform'),
            self = this;
        for (i = 0; i <= lastJumpPage; ++i) {
            if (!this.props.allPagesOnTheFly &&
                    !this.props.pages[i].onTheFly) {
                text = this.props.pages[i].title;
            } else {
                text = L("page") + " " + (i + 1);
            }
            textOptions.push(text);
        }
        if (platform.ios) {
            textOptions.push(L("cancel"));
            // Primary reason: to create an additional line -- otherwise, on
            // long lists, the bottom one is nearly invisible. Bug, I think.
        }
        this.cleanupJump(); // destroy any old ones; shouldn't be any open
        // as they're meant to be modal
        this.jumpDialog = Titanium.UI.createOptionDialog({
            options: textOptions,
            selectedIndex: this.currentPage,
            opaquebackground: true, // or it will ghost when scrolling on iPad
        });
        this.jumpListener = function (e) { self.jumpPageSelected(e); };
        this.jumpDialog.addEventListener("click", this.jumpListener);
        this.jumpDialog.show();
    },

    jumpPageSelected: function (e) {
        var index = e.index;
        if (index < 0) {
            return; // dialogue cancelled
        }
        if (index > this.lastPageToWhichJumpAllowed()) {
            return;
            // something has gone wrong internally, OR it's our extra "cancel"
            // line
        }
        if (index === this.currentPage) {
            return; // nothing to do
        }
        this.pageAboutToClose();
        this.currentPage = index;
        this.setFocus(this.currentPage);
    },

    //-------------------------------------------------------------------------
    // Services
    //-------------------------------------------------------------------------
    setMandatoryByTag: function (elementTag, mandatory, extraParam) {
        // Uses currentview.elements, so only applies to current page
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "setMandatory", mandatory, extraParam);
        // May change visibility status, so:
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "applyVisible");
    },

    setVisibleByTag: function (elementTag, visible) {
        // Uses currentview.elements, so only applies to current page
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "setVisible", visible);
        // ... setVisible calls applyVisible automatically; see qcommon.js
    },

    setMandatoryAndVisibleByTag: function (elementTag, visible_mandatory,
                                           extraParam) {
        // Uses currentview.elements, so only applies to current page
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "setMandatory", visible_mandatory,
                                        extraParam);
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "setVisible", visible_mandatory);
        // ... setVisible calls applyVisible automatically; see qcommon.js
    },

    setFromFieldByTag: function (elementTag) {
        // Uses currentview.elements, so only applies to current page
        callMemberFnForAllElementsByTag(this.currentview.elements, elementTag,
                                        "setFromField");
    },

    refreshCurrentPage: function () {
        Titanium.API.trace("Questionnaire.refreshCurrentPage");
        this.setFocus(this.currentPage);
    },

};
module.exports = Questionnaire;
