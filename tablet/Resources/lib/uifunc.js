// uifunc.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var UICONSTANTS = require('common/UICONSTANTS'),
    alertInProgress = false,
    alertDlg = null,
    // ... because Titanium claims its alert box is modal, but it isn't:
    // certainly, multiple copies get popped up when multiple triggering events
    // occur fast.
    defaultWaitMessage = L('default_wait_message');
    // ... stored so as to save string lookup time

function removeAllWindowChildren(window) {
    // Remove all views:
    // http://developer.appcelerator.com/question/78311/removing-all-child-objects-from-a-view
    var removeData = [],
        i;
    if (window && window.children !== undefined) {
        // Save children
        for (i = 0; i < window.children.length; ++i) {
            removeData.push(window.children[i]);
        }
        // Remove children
        for (i = 0; i < removeData.length; ++i) {
            window.remove(removeData[i]);
        }
    }
}
exports.removeAllWindowChildren = removeAllWindowChildren;

function removeAllViewChildren(view) {
    var platform = require('lib/platform');
    if (platform.android || platform.ios) {
        view.removeAllChildren();
    }
}
exports.removeAllViewChildren = removeAllViewChildren;

function alert(message, title) {
    // Titanium.API.debug("uifunc.alert: " + title + ": " + message);
    var platform;
    if (title === undefined) {
        title = "Alert";
    }
    if (alertInProgress && alertDlg) {
        Titanium.API.debug("!!! uifunc.alert called while alert in progress");
        platform = require('lib/platform');
        if (platform.android) {
            // Android
            /* SOMETIMES FAILS, "Dialog activity is destroyed, unable to show
                                 dialog with message: ..."
            alertDlg.setTitle(title);
            alertDlg.setMessage(message);
            alertDlg.show();
            return;
            */
            alertDlg.hide();
            alertDlg = null;
            // ... so proceed to creating a new alert
        } else {
            // iOS: can't alter title/message?
            alertDlg.hide();
            alertDlg = null;
            // ... so proceed to creating a new alert
        }
    }

    // Fresh alert
    alertInProgress = true;
    alertDlg = Titanium.UI.createAlertDialog({
        message: message,
        title: title,
        buttonNames: [L('ok')]
    });
    alertDlg.addEventListener('click', function () {
        alertInProgress = false;
        alertDlg = null;
    });
    alertDlg.show();
}
exports.alert = alert;

function createWait(props) { // *** This class is imperfect and may leak.
    /*
    for iOS (and Android from SDK 3.0 via this interface), we need to add
    the activity indicator to a window -- but we can't get the current
    window (Titanium.UI.currentWindow / getCurrentWindow()) except within
    .js files that created a window using the url method...
    Other problem: if we have a raw spinner, it spins, but is transparent;
    if we add a view-container, we can do borders/opacity, but it doesn't spin.
    Since we can't set the spinner colour, so in practice it's often
    invisible... slightly nicer without spinning/transparency.
    */

    if (props.window === undefined) {
        throw new Error("createWait() called with no window");
    }
    if (props.message === undefined) {
        props.message = defaultWaitMessage;
    }
    if (props.offerCancel === undefined) {
        props.offerCancel = false;
    }
    if (props.zIndex === undefined) {
        props.zIndex = 1;
    }

    // The outer container is transparent but blocks touches
    var outercontainer = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            visible: false
            // ... so, like an ActivityIndicator, it requires to be show()n first
        }),
        transparentfilm = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            backgroundColor: UICONSTANTS.POPUP_BORDER_COLOUR,
            opacity: 0.5
        }),
        innercontainer = Titanium.UI.createView({
            center: {x: '50%', y: '50%'},
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            backgroundColor: UICONSTANTS.WAIT_BACKGROUND_COLOUR,
            layout: 'vertical'
        }),
        waitMessage = Titanium.UI.createLabel({
            top: UICONSTANTS.WAIT_SPACE,
            left: UICONSTANTS.WAIT_SPACE,
            right: UICONSTANTS.WAIT_SPACE,
            bottom: UICONSTANTS.WAIT_SPACE,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            font: UICONSTANTS.WAIT_FONT,
            color: UICONSTANTS.WAIT_COLOUR,
            text: props.message
        }),
        titleLabel,
        cancelButton;
    if (props.title) {
        titleLabel = Titanium.UI.createLabel({
            top: UICONSTANTS.WAIT_SPACE,
            left: UICONSTANTS.WAIT_SPACE,
            right: UICONSTANTS.WAIT_SPACE,
            bottom: UICONSTANTS.WAIT_SPACE,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            font: UICONSTANTS.WAIT_TITLE_FONT,
            color: UICONSTANTS.WAIT_TITLE_COLOUR,
            text: props.title
        });
        innercontainer.add(titleLabel);
    }
    innercontainer.add(waitMessage);
    if (props.offerCancel) {
        if (props.fnCancel === undefined) {
            throw new Error("createWait: undefined fnCancel, yet " +
                            "offerCancel specified");
        }
        cancelButton = Titanium.UI.createButton({
            title: L('cancel'),
            bottom: UICONSTANTS.WAIT_SPACE
        });
        cancelButton.addEventListener('click', props.fnCancel);
        innercontainer.add(cancelButton);
    }
    outercontainer.add(transparentfilm);
    outercontainer.add(innercontainer);
    props.window.add(outercontainer);
    outercontainer.setMessage = function (msg) {
        waitMessage.setText(msg);
    };
    outercontainer.setZIndex(props.zIndex); // make it stay on top
    // ... otherwise, the calling function would have to add this component
    // last
    return outercontainer;
}
exports.createWait = createWait;

function createEncryptionWait(sourcewindow) {
    return createWait({
        window: sourcewindow,
        message: L('encryption_wait_msg'),
        title: L('encryption_wait_title'),
        offerCancel: false
    });
}
exports.createEncryptionWait = createEncryptionWait;

function setPrivilege() {
    var EVENTS = require('common/EVENTS'),
        GV = require('common/GV');
    GV.privileged = true;
    GV.patient_locked = false;
    Titanium.App.fireEvent(EVENTS.PATIENT_LOCK_CHANGED, {});
}
exports.setPrivilege = setPrivilege;

function unlock() {
    var EVENTS = require('common/EVENTS'),
        GV = require('common/GV');
    GV.patient_locked = false;
    Titanium.App.fireEvent(EVENTS.PATIENT_LOCK_CHANGED, {});
}
exports.unlock = unlock;

function createGenericButton(icon, props, iconWhileTouched) {
    if (props.height === undefined) {
        props.height = UICONSTANTS.ICONSIZE;
    }
    if (props.width === undefined) {
        props.width = UICONSTANTS.ICONSIZE;
    }
    if (props.top === undefined) {
        props.top = 0;
    }
    if (iconWhileTouched) {
        // Proper button
        props.backgroundImage = icon;
        props.backgroundSelectedImage = iconWhileTouched;
        // props.backgroundFocusedImage = ...; // for Android
        // props.backgroundDisabledImage = ...;
        // ... if the button is ever disabled
        return Titanium.UI.createButton(props);
    }
    // Image
    props.image = icon;
    return Titanium.UI.createImageView(props);
}
exports.createGenericButton = createGenericButton;

function createLockButton(props) {
    // specify left or right
    var GV = require('common/GV'),
        lockButton,
        EVENTS;
    props.visible = !GV.privileged && !GV.patient_locked;
    lockButton = createGenericButton(UICONSTANTS.ICON_UNLOCKED, props,
                                     UICONSTANTS.ICON_UNLOCKED_T);
    lockButton.addEventListener('click', function () {
        Titanium.API.info("uifunc: lock button clicked");
        if (!GV.patient_locked) {
            //if (GV.selected_patient_id === null) {
            //    alert(L('no_patient_selected'), L('cannot_lock'));
            //}
            //else {
            EVENTS = require('common/EVENTS');
            GV.patient_locked = true;
            Titanium.App.fireEvent(EVENTS.PATIENT_LOCK_CHANGED, {});
            //}
        }
    });
    return lockButton;
}
exports.createLockButton = createLockButton;

/*jslint unparam: true */
function createUnlockButton(props) {
    var GV = require('common/GV'),
        unlockButton,
        storedvars,
        hashedpw,
        AskUsernamePasswordWindow,
        win;
    props.visible = !GV.privileged && GV.patient_locked;
    unlockButton = createGenericButton(UICONSTANTS.ICON_LOCKED, props,
                                       UICONSTANTS.ICON_LOCKED_T);
    unlockButton.addEventListener('click', function () {
        Titanium.API.info("uifunc: unlock button clicked");
        if (GV.patient_locked) {
            storedvars = require('table/storedvars');
            hashedpw = storedvars.unlockPasswordHash.getValue();
            if (!hashedpw) {
                // no security
                unlock();
            } else {
                AskUsernamePasswordWindow = require(
                    'screen/AskUsernamePasswordWindow'
                );
                win = new AskUsernamePasswordWindow({
                    askUsername: false,
                    captionPassword: L("enter_unlock_password"),
                    hintPassword: L('hint_password'),
                    showCancel: true,
                    verifyAgainstHash: true,
                    hashedPassword: hashedpw,
                    callbackFn: function (username, password, verified,
                                          cancelled) {
                        if (cancelled) {
                            return;
                        }
                        if (verified) {
                            unlock();
                        } else {
                            alert(L('wrong_password'), L('unlock'));
                        }
                    }
                });
                win.open();
            }
        }
    });
    return unlockButton;
}
/*jslint unparam: false */
exports.createUnlockButton = createUnlockButton;

function createDeprivilegeButton(props) {
    var GV = require('common/GV'),
        deprivilegeButton,
        EVENTS;
    props.visible = GV.privileged;
    deprivilegeButton = createGenericButton(UICONSTANTS.ICON_PRIVILEGED, props,
                                            UICONSTANTS.ICON_PRIVILEGED_T);
    deprivilegeButton.addEventListener('click', function () {
        Titanium.API.info("uifunc: deprivilege button clicked");
        if (GV.privileged) {
            EVENTS = require('common/EVENTS');
            GV.privileged = false;
            Titanium.App.fireEvent(EVENTS.PATIENT_LOCK_CHANGED, {});
        }
    });
    return deprivilegeButton;
}
exports.createDeprivilegeButton = createDeprivilegeButton;

function setLockButtons(lockButton, unlockButton, deprivilegeButton) {
    var GV = require('common/GV');
    if (GV.privileged) {
        deprivilegeButton.show();
        lockButton.hide();
        unlockButton.hide();
    } else if (GV.patient_locked) {
        deprivilegeButton.hide();
        lockButton.hide();
        unlockButton.show();
    } else {
        deprivilegeButton.hide();
        unlockButton.hide();
        lockButton.show();
    }
}
exports.setLockButtons = setLockButtons;

function setPatientLine(patientlabel) {
    var GV = require('common/GV'),
        patientcolor,
        patienttext,
        Patient;
    if (GV.selected_patient_id === null) {
        patientcolor = UICONSTANTS.NO_PATIENT_COLOUR;
        patienttext = L('no_patient_selected');
    } else {
        patientcolor = UICONSTANTS.PATIENT_COLOUR;
        Patient = require('table/Patient');
        patienttext = (new Patient(GV.selected_patient_id)).getSummary();
    }
    patientlabel.setText(patienttext);
    patientlabel.setColor(patientcolor);
}
exports.setPatientLine = setPatientLine;

function notWhenLocked() {
    alert(L('not_when_locked_msg'), L('not_when_locked_title'));
}
exports.notWhenLocked = notWhenLocked;

function choosePatient() {
    var GV = require('common/GV'),
        SelectPatientWindow,
        win;
    Titanium.API.info("uifunc.choosePatient");
    if (GV.patient_locked) {
        notWhenLocked();
        return;
    }
    SelectPatientWindow = require('screen/SelectPatientWindow');
    win = new SelectPatientWindow();
    win.open();
}
exports.choosePatient = choosePatient;

/*
function createChoosePatientButton(props) {
    // specify left or right
    var choosepatientbutton = createGenericButton(
        UICONSTANTS.ICON_CHOOSE_PATIENT, props);
    choosepatientbutton.addEventListener('click', choosePatient);
    return choosepatientbutton;
}
exports.createChoosePatientButton = createChoosePatientButton;
*/

function createBackButton(props) {
    return createGenericButton(UICONSTANTS.ICON_BACK, props,
                               UICONSTANTS.ICON_BACK_T);
}
exports.createBackButton = createBackButton;

function createZoomButton(props) {
    return createGenericButton(UICONSTANTS.ICON_ZOOM, props,
                               UICONSTANTS.ICON_ZOOM_T);
}
exports.createZoomButton = createZoomButton;

function createAddButton(props) {
    return createGenericButton(UICONSTANTS.ICON_ADD, props,
                               UICONSTANTS.ICON_ADD_T);
}
exports.createAddButton = createAddButton;

function createDeleteButton(props) {
    return createGenericButton(UICONSTANTS.ICON_DELETE, props,
                               UICONSTANTS.ICON_DELETE_T);
}
exports.createDeleteButton = createDeleteButton;

function createEditButton(props) {
    return createGenericButton(UICONSTANTS.ICON_EDIT, props,
                               UICONSTANTS.ICON_EDIT_T);
}
exports.createEditButton = createEditButton;

function createFinishFlagButton(props) {
    return createGenericButton(UICONSTANTS.ICON_FINISHFLAG, props,
                               UICONSTANTS.ICON_FINISHFLAG_T);
}
exports.createFinishFlagButton = createFinishFlagButton;

function createOkButton(props) {
    return createGenericButton(UICONSTANTS.ICON_OK, props,
                               UICONSTANTS.ICON_OK_T);
}
exports.createOkButton = createOkButton;

function createCancelButton(props) {
    return createGenericButton(UICONSTANTS.ICON_CANCEL, props,
                               UICONSTANTS.ICON_CANCEL_T);
}
exports.createCancelButton = createCancelButton;

function createReloadButton(props) {
    return createGenericButton(UICONSTANTS.ICON_RELOAD, props,
                               UICONSTANTS.ICON_RELOAD_T);
}
exports.createReloadButton = createReloadButton;

function createCameraButton(props) {
    return createGenericButton(UICONSTANTS.ICON_CAMERA, props,
                               UICONSTANTS.ICON_CAMERA_T);
}
exports.createCameraButton = createCameraButton;

function createRotateAnticlockwiseButton(props) {
    return createGenericButton(UICONSTANTS.ICON_ROTATE_ANTICLOCKWISE, props,
                               UICONSTANTS.ICON_ROTATE_ANTICLOCKWISE_T);
}
exports.createRotateAnticlockwiseButton = createRotateAnticlockwiseButton;

function createRotateClockwiseButton(props) {
    return createGenericButton(UICONSTANTS.ICON_ROTATE_CLOCKWISE, props,
                               UICONSTANTS.ICON_ROTATE_CLOCKWISE_T);
}
exports.createRotateClockwiseButton = createRotateClockwiseButton;

function buttonPosition(n, nEdgeSpaces) {
    nEdgeSpaces = (nEdgeSpaces === undefined) ? 1 : nEdgeSpaces;
    return UICONSTANTS.SPACE * (n + nEdgeSpaces) + UICONSTANTS.ICONSIZE * n;
}
exports.buttonPosition = buttonPosition;

function yesNo(x) {
    return x ? L('Yes') : L('No');
}
exports.yesNo = yesNo;

function yesNoNull(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return "null";
    }
    return x ? L('Yes') : L('No');
}
exports.yesNoNull = yesNoNull;

function yesNoUnknown(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return L("Unknown");
    }
    return x ? L('Yes') : L('No');
}
exports.yesNoUnknown = yesNoUnknown;

function trueFalseNull(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return "null";
    }
    return x ? L('True') : L('False');
}
exports.trueFalseNull = trueFalseNull;

function trueFalseUnknown(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return L("Unknown");
    }
    return x ? L('True') : L('False');
}
exports.trueFalseUnknown = trueFalseUnknown;

function presentAbsentNull(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return "null";
    }
    return x ? L('Present') : L('Absent');
}
exports.presentAbsentNull = presentAbsentNull;

function presentAbsentUnknown(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return L("Unknown");
    }
    return x ? L('Present') : L('Absent');
}
exports.presentAbsentUnknown = presentAbsentUnknown;

function niceDateOrNull(x) {
    if (x === undefined) {
        return "undefined";
    }
    if (x === null) {
        return "null";
    }
    return x.format(UICONSTANTS.TASK_DATETIME_FORMAT);
}
exports.niceDateOrNull = niceDateOrNull;

/*
var touchstart = null;
function makeSwipeable(view, allowVertical, tolerance) {
    // https://gist.github.com/841075
    // Modified so start and end can come from different objects
    tolerance = tolerance || 2;
    view.addEventListener('touchstart', function (evt) {
        Titanium.API.trace("SWIPE_HANDLER touchstart");
        touchstart = evt;
    });
    view.addEventListener('touchend', function (end) {
        Titanium.API.trace("SWIPE_HANDLER touchend");
        if (touchstart === null) {
            return;
            // RNC: in case a touch started in a different, non-touchable
            // object
        }
        var dx = end.x - touchstart.x, dy = end.y - touchstart.y;
        touchstart = null; // RNC
        var dist = Math.sqrt(Math.pow(dx, 2) + Math.pow(dy, 2));
        // only trigger if dragged further than 50 pixels
        if (dist < 50) {
            return;
        }
        var isVertical = Math.abs(dx / dy) < 1 / tolerance;
        var isHorizontal = Math.abs(dy / dx) < 1 / tolerance;
        // only trigger if dragged in a particular direction
        if (!isVertical && !isHorizontal) {
            return;
        }
        // disallow vertical swipe, depending on the setting
        if (!allowVertical && isVertical) {
            return;
        }
        // now fire the event off so regular 'swipe' handlers can use this!
        end.direction = (
            isHorizontal
            ? ((dx < 0) ? 'left' : 'right')
            : ((dy < 0) ? 'up' : 'down')
        );
        end.type = 'swipe';
        Titanium.API.trace("SWIPE_HANDLER firing swipe / " + end.direction);
        view.fireEvent('swipe', end);
    });
}
exports.makeSwipeable = makeSwipeable;
*/

function createVerticalSpacer() {
    return Titanium.UI.createView({
        top: 0,
        left: 0,
        height: UICONSTANTS.SPACE,
        width: Titanium.UI.FILL,
        touchEnabled: false
    });
}
exports.createVerticalSpacer = createVerticalSpacer;

function createHorizontalSpacer() {
    return Titanium.UI.createView({
        top: 0,
        left: 0,
        height: UICONSTANTS.SPACE,
        width: UICONSTANTS.SPACE,
        touchEnabled: false
    });
}
exports.createHorizontalSpacer = createHorizontalSpacer;

function createMenuRule() {
    return Titanium.UI.createView({
        backgroundColor: UICONSTANTS.MENU_HEADER_RULE_COLOUR,
        height: UICONSTANTS.MENU_HEADER_RULE_HEIGHT,
        width: Titanium.UI.FILL,
        touchEnabled: false
    });
}
exports.createMenuRule = createMenuRule;

function createQuestionnaireRule() {
    return Titanium.UI.createView({
        backgroundColor: UICONSTANTS.QUESTIONNAIRE_HEADER_RULE_COLOUR,
        height: UICONSTANTS.QUESTIONNAIRE_HEADER_RULE_HEIGHT,
        width: Titanium.UI.FILL,
        touchEnabled: false
    });
}
exports.createQuestionnaireRule = createQuestionnaireRule;

function createMenuTitleText(props, skipVerticalCentre) {
    props.height = Titanium.UI.SIZE;
    props.width = Titanium.UI.FILL;
    props.font = UICONSTANTS.MENU_TITLE_FONT;
    if (!skipVerticalCentre) {
        if (!props.center) {
            props.center = { y: '50%' };
        } else if (!props.center.y) {
            props.center.y = '50%';
        }
    }
    if (props.color === undefined) {
        props.color = UICONSTANTS.MENU_TITLE_COLOUR;
    }
    props.touchEnabled = false;
    return Titanium.UI.createLabel(props);
}
exports.createMenuTitleText = createMenuTitleText;

function createMenuSubtitleText(props, skipVerticalCentre) {
    props.height = Titanium.UI.SIZE;
    props.width = Titanium.UI.FILL;
    props.font = UICONSTANTS.MENU_SUBTITLE_FONT;
    if (!skipVerticalCentre) {
        if (!props.center) {
            props.center = { y: '50%' };
        } else if (!props.center.y) {
            props.center.y = '50%';
        }
    }
    props.color = UICONSTANTS.MENU_TITLE_COLOUR;
    props.touchEnabled = false;
    return Titanium.UI.createLabel(props);
}
exports.createMenuSubtitleText = createMenuSubtitleText;

function addAndroidCloser(win) {
    var platform = require('lib/platform');
    if (!platform.android) {
        return;
    }
    win.addEventListener('android:back', function () {
        win.close();
        win = null; // for garbage collection
    });
}
exports.addAndroidCloser = addAndroidCloser;

function createMenuWindow(p) {
    if (p === undefined) { p = {}; }
    if (p.navBarHidden === undefined) { p.navBarHidden = true; }
    if (p.modal === undefined) { p.modal = false; }
    // In general, do NOT make it a heavyweight window: that would break the
    // EVENTS.PATIENT_EDIT_SAVE message-passing.
    // The error is: java.lang.RuntimeException: Can't marshal non-Parcelable
    // objects across processes.

    // Do not use exitOnClose, since keyboard docking/undocking causes a close
    // event.

    var windowprops = {
            backgroundColor: UICONSTANTS.MENU_BG_COLOUR,
            modal: p.modal,
            // makes it a heavyweight window, so the hardware "back" button works
            navBarHidden: p.navBarHidden // removes the top line
        },
        platform = require('lib/platform'),
        win;
    if (platform.ios7plus) {
        windowprops.fullscreen = true;
        // for iOS 7, or transparent status bar visible
    }

    win = Titanium.UI.createWindow(windowprops);
    return win;
}
exports.createMenuWindow = createMenuWindow;

function showHtml(content, title, nobounce, html_not_filename) {
    // http://developer.appcelerator.com/blog/2011/09/sharing-project-assets-with-android-intents.html
    // http://developer.appcelerator.com/question/42881/loading-local-html-files-with-webview
    // showWait();
    if (nobounce === undefined) { nobounce = false; }
    if (html_not_filename === undefined) { html_not_filename = false; }
    var win = createMenuWindow({modal: true}),
        mainview = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            layout: 'vertical'
        }),
        header = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL
        }),
        backbutton = createBackButton({left: buttonPosition(0) }),
        titletext = createMenuTitleText({
            left: buttonPosition(1),
            right: UICONSTANTS.SPACE,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            text: title
        }),
        platform = require('lib/platform'),
        props = {
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL
        },
        webview;

    backbutton.addEventListener('click', function () {
        win.close();
        win = null; // for garbage collection
    });
    header.add(backbutton);
    header.add(titletext);
    mainview.add(header);
    mainview.add(createVerticalSpacer());
    mainview.add(createMenuRule());
    // Important bit:
    if (html_not_filename) {
        props.html = content;
    } else {
        props.url = platform.translateFilename(content);
    }
    if (nobounce) {
        props.disableBounce = true; // iOS
    }
    webview = Titanium.UI.createWebView(props);
    mainview.add(webview);
    win.add(mainview);
    win.open();
    // hideWait();
}
exports.showHtml = showHtml;

function getImageSize(blob) {
    // https://jira.appcelerator.org/browse/TIMOB-8481
    var platform = require('lib/platform'),
        ImageFactory,
        jpegblob;
    if (platform.android) {
        ImageFactory = require('ti.imagefactory');
        jpegblob = ImageFactory.compress(blob, 0.1);
        // not sure what's faster: low quality (near 0) or high quality
        // (near 1)
        return {
            width: jpegblob.width,
            height: jpegblob.height
        };
    }
    return {
        width: blob.width,
        height: blob.height
    };
}
exports.getImageSize = getImageSize;

function rescaleImage(image, targetWidth, targetHeight, fromScale) {
    var ImageFactory = require('ti.imagefactory');
    return ImageFactory.imageTransform(
        image,
        // In order, the following transformations:
        {
            type: ImageFactory.TRANSFORM_CROP,
            width: targetWidth * fromScale,
            height: targetHeight * fromScale,
            x: 0,
            y: 0,
            format: ImageFactory.PNG,
            quality: 1.0
        },
        {
            type: ImageFactory.TRANSFORM_RESIZE,
            width: targetWidth,
            height: targetHeight,
            format: ImageFactory.PNG,
            quality: 1.0
        }
    );
    // imageTransform has curious syntax for multiple transformations;
    // see example app.js
}
exports.rescaleImage = rescaleImage;

function setFullscreen() {
    var platform = require('lib/platform'),
        Androiduitools;
    if (platform.android) {
        Androiduitools = require('org.camcops.androiduitools');
        Androiduitools.setFullscreen();
    }
}
exports.setFullscreen = setFullscreen;

function createFullscreenView(props) {
    if (props.width === undefined) { props.width = Titanium.UI.FILL; }
    if (props.height === undefined) { props.height = Titanium.UI.FILL; }
    var platform = require('lib/platform'),
        Androiduitools,
        fv;
    if (platform.android) {
        Androiduitools = require('org.camcops.androiduitools');
        fv = Androiduitools.createFullscreenView(props);
        fv.addEventListener("postlayout", function () {
            Titanium.UI.trace("uifunc calling fv.goFullscreen()");
            fv.goFullscreen();
        });
        return fv;
    }
    return Titanium.UI.createView(props);
}
exports.createFullscreenView = createFullscreenView;

function dumpProps(obj) {
    var s = "",
        first = true,
        prop;
    for (prop in obj) {
        if (obj.hasOwnProperty(prop)) {
            if (!first) {
                s += ", ";
            }
            s += prop + "=" + obj[prop];
            first = false;
        }
    }
    return s;
}
exports.dumpProps = dumpProps;

function getRowDataFromTableViewClickEvent(e) {
    var platform = require('lib/platform');
    if (platform.android) {
        // rowData can be null; bug in Titanium, probably (version 2.1.2 GA)
        return e.row;
    }
    return e.rowData; // This is what the docs advertise
}
exports.getRowDataFromTableViewClickEvent = getRowDataFromTableViewClickEvent;

function soundTest(sourcewindow, filename, volume) {
    if (volume === undefined) { volume = 1.0; }
    var wait = createWait({
            window: sourcewindow,
            message: L('sound_test') + " " + filename + "\n" + L('volume') +
                " " + volume
        }),
        soundhandler = require('lib/soundhandler');
    wait.show();

    function onComplete() {
        soundhandler.unloadSound(filename);
        wait.hide();
    }

    soundhandler.loadSound({
        filename: filename,
        fnSoundComplete: onComplete,
        volume: volume
    });
    soundhandler.playSound(filename);
}
exports.soundTest = soundTest;

function getTrimmedTextField(field) {
    // Android is happy with field.value.trim(), but under iOS the value can be
    // a number.
    switch (typeof field.value) {
    case "string":
        return field.value.trim();
    case "number":
        return field.value;
    default:
        return "";
    }
}
exports.getTrimmedTextField = getTrimmedTextField;

function getIntFromTextField(field) {
    var value = parseInt(field.value, 10);
    // see QuestionnaireTypedVariables for a more elaborate form
    if (isNaN(value)) {
        return null;
    }
    return value;
}
exports.getIntFromTextField = getIntFromTextField;

function createSettingsLabel(text) {
    return Titanium.UI.createLabel({
        text: text,
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.EDITING_LABEL_FONT,
        color: UICONSTANTS.EDITING_LABEL_COLOUR
    });
}
exports.createSettingsLabel = createSettingsLabel;

function createWarningLabel(text) {
    return Titanium.UI.createLabel({
        text: text,
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.EDITING_FONT,
        color: UICONSTANTS.EDITING_WARNING_COLOUR
    });
}
exports.createWarningLabel = createWarningLabel;

function createInfoLabel(text) {
    return Titanium.UI.createLabel({
        text: text,
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.EDITING_INFO_FONT,
        color: UICONSTANTS.EDITING_INFO_COLOUR
    });
}
exports.createInfoLabel = createInfoLabel;

function createSettingsEditText(initialvalue, hint, capitalize) {
    if (capitalize === undefined) { capitalize = false; }
    return Titanium.UI.createTextField({
        value: initialvalue,
        left: UICONSTANTS.SPACE,
        width: Titanium.UI.FILL,
        font: UICONSTANTS.EDITING_FONT,
        color: UICONSTANTS.EDITING_TEXT_COLOUR,
        autocapitalization: (capitalize ?
                Titanium.UI.TEXT_AUTOCAPITALIZATION_ALL :
                Titanium.UI.TEXT_AUTOCAPITALIZATION_NONE
        ),
        hintText: hint,
        suppressReturn: true
    });
}
exports.createSettingsEditText = createSettingsEditText;

function createSettingsEditPassword(initialvalue, hint) {
    return Titanium.UI.createTextField({
        value: (initialvalue === null ? "" : initialvalue),
        left: UICONSTANTS.SPACE,
        width: Titanium.UI.FILL,
        font: UICONSTANTS.EDITING_FONT,
        color: UICONSTANTS.EDITING_TEXT_COLOUR,
        backgroundColor: UICONSTANTS.EDITING_PASSWORD_BACKGROUND,
        hintText: hint,
        passwordMask: true,
        suppressReturn: true
    });
}
exports.createSettingsEditPassword = createSettingsEditPassword;

function validateInt(e) {
    var v = parseInt(parseFloat(e.source.value), 10);
    // ... parseFloat copes with e.g. "5e+3", which parseInt rejects
    // ... then some floats can be integers, e.g 5e+3 becomes 5000,
    //     while others can't, e.g. 5e+25 (string) becomes 5e+25 (float) becomes 5 (int)
    // ... but probably the best we can do.
    e.source.value = isNaN(v) ? "" : v.toString();
}

function summarizeTask(task) {
    var Patient = require('table/Patient'),
        title;
    if (task.isAnonymous()) {
        title = (L("anonymous_task") + " " + L('at') + " " +
                     task.getCreationDateTimeNice());
    } else {
        title = (
            (new Patient(task.getPatientID())).getLine1() +
            " " + L('at') + " " + task.getCreationDateTimeNice()
        );
    }
    alert(task.getDetail(), title);
}
exports.summarizeTask = summarizeTask;

function ipFail(task) {
    alert(
        L('task_not_permissible_msg') + "\n\n" + task.whyNotPermissible(),
        L('task_not_permissible_title')
    );
}
exports.ipFail = ipFail;

function editTask(task, wait) {
    if (!task) {
        return;
    }
    var GV = require('common/GV'),
        dlg;
    if (GV.patient_locked) {
        notWhenLocked();
        return;
    }
    if (!task.isEditable()) {
        alert(L('task_not_editable_msg'), L('task_not_editable_title'));
        return;
    }
    if (!task.isTaskPermissible()) {
        ipFail(task);
        return;
    }
    dlg = Titanium.UI.createAlertDialog({
        title: L('edit_record_q'),
        message: (L('edit_this_record_q') + '\n\n' +
                  task.getCreationDateTimeNice()),
        buttonNames: [L('cancel'), L('edit')]
    });
    dlg.addEventListener('click', function (e) {
        if (e.index === 1) { // Edit
            wait.show();
            GV.inChain = false;
            task.edit(false); // may fire EVENTS.TASK_FINISHED
            wait.hide();
        }
        dlg = null;
    });
    dlg.show();
}
exports.editTask = editTask;

function deleteTask(task, callbackWhenDeleted) {
    if (!task) {
        return;
    }
    var GV = require('common/GV'),
        dlg;
    if (GV.patient_locked) {
        notWhenLocked();
        return;
    }
    dlg = Titanium.UI.createAlertDialog({
        title: L('delete_record_q'),
        message: L('delete_this_record_q') + '\n\n' + task.getSummary(),
        buttonNames: [L('cancel'), L('delete')]
    });
    dlg.addEventListener('click', function (e) {
        if (e.index === 1) { // Delete
            task.dbdelete();
            callbackWhenDeleted();
        }
        dlg = null;
    });
    dlg.show();
}
exports.deleteTask = deleteTask;

function zoomTask(task, wait) {
    if (!task) {
        return;
    }
    var GV = require('common/GV'),
        dlg;
    if (GV.patient_locked &&
            GV.selected_patient_id === null &&
            !task.isAnonymous()) {
        notWhenLocked();
        return;
    }
    if (task.isEditable()) {
        dlg = Titanium.UI.createAlertDialog({
            title: L('view_options'),
            message: L('view_options_q'),
            buttonNames: [L('cancel'), L('facsimile'), L('summary')]
        });
        dlg.addEventListener('click', function (e) {
            if (e.index === 1) { // Facsimile
                wait.show();
                GV.inChain = false;
                task.edit(true); // may fire EVENTS.TASK_FINISHED
                wait.hide();
            } else if (e.index === 2) { // Summary
                summarizeTask(task);
            }
            dlg = null;
        });
        dlg.show();
    } else {
        summarizeTask(task);
    }
}
exports.zoomTask = zoomTask;

function addTask(taskclass, wait) {
    Titanium.API.info("uifunc.addTask()");
    var task,
        GV = require('common/GV');
    Titanium.API.info("Making dummy task to inspect properties...");
    task = new taskclass(); // DUMMY
    Titanium.API.info("... done");
    if (!task.isTaskPermissible()) {
        ipFail(task);
        return;
    }
    if (task.isAnonymous()) {
        // the dummy one becomes our real one
        wait.show();
        GV.inChain = false;
        task.edit(); // may fire EVENTS.TASK_FINISHED
        wait.hide();
    } else {
        if (GV.selected_patient_id === null) {
            alert(L('no_patient_selected'), L('cannot_run_task'));
            return;
        }
        wait.show();
        Titanium.API.info("Adding task...");
        task = new taskclass(GV.selected_patient_id); // REAL
        GV.inChain = false;
        Titanium.API.info("Editing new task...");
        task.edit(); // may fire EVENTS.TASK_FINISHED
        wait.hide();
    }
}
exports.addTask = addTask;

function createPasswordPopupWindow() {
    var win = Titanium.UI.createWindow({
        // With NO options, it looks lovely - but we can't catch android:back
        //      (which closes our parent).
        // With modal:true, we can catch android:back, but the parent window
        //      vanishes (and the "CamCOPS" title bar is present).
        // ... we can use navBarHidden to make that go away
        // ALTERNATIVELY: we can make android:back something we override all
        //      the time... mmm... could be tricky. But think.
        // It would mean that all heavyweight windows would catch the event
        //      and translate it into an internal event.
        // Then the heavyweight window would need to know whether it was busy
        //      doing something else (i.e. having a modal
        // popup window on top of it), and so on... Complex.

        // modal: true,
        // ... makes it a heavyweight window, so the hardware "back" button
        // works: http://developer.appcelerator.com/question/2731/adding-a-window-to-the-stack

        fullscreen: true // for iOS 7, or transparent status bar visible
    });
    addAndroidCloser(win);
    return win;
}
exports.createPasswordPopupWindow = createPasswordPopupWindow;

function createQuestionnaireWindow(orientationModes) {
    if (orientationModes === undefined) { orientationModes = []; }
    var win = Titanium.UI.createWindow({
        backgroundColor: UICONSTANTS.QUESTIONNAIRE_BG_COLOUR,
        navBarHidden: true,
        fullscreen: true,
        orientationModes: orientationModes
        // Must be a heavyweight window to support orientationModes
    });
    // NO - DO THIS BY HAND IN QUESTIONNAIRE -- addAndroidCloser(win);
    return win;
    // Avoid using an Android navbar-hiding fullscreen view, since the
    // showWait() function restores it,
    // so it flashes on and off and looks rubbish.
    // *** this might now change in SDK 3.0 (re navbar-hiding Questionnaire
    // window flashing Android navbar on/off)
}
exports.createQuestionnaireWindow = createQuestionnaireWindow;

function createDiagnosticCodeWindow(androidBackCallbackFn) {
    var win = Titanium.UI.createWindow({
            navBarHidden: true,
            backgroundColor: UICONSTANTS.DIAGNOSTICCODE_BACKGROUND,
            layout: 'vertical',
            fullscreen: true // for iOS 7, or transparent status bar visible
        }),
        platform = require('lib/platform');
    if (platform.android && typeof androidBackCallbackFn === "function") {
        win.addEventListener('android:back', androidBackCallbackFn);
    }
    return win;
}
exports.createDiagnosticCodeWindow = createDiagnosticCodeWindow;

function broadcastPatientSelection(id) {
    Titanium.API.trace("broadcastPatientSelection");
    var EVENTS = require('common/EVENTS'),
        GV = require('common/GV');
    GV.selected_patient_id = id;
    Titanium.App.fireEvent(EVENTS.PATIENT_CHOSEN, {});
}
exports.broadcastPatientSelection = broadcastPatientSelection;

function upload(sourcewindow, afterwardsFunc) {
    var dbupload = require('lib/dbupload'),
        netcore = require('lib/netcore'),
        platform = require('lib/platform'),
        dlg;

    function copy() {
        dbupload.upload(sourcewindow, dbupload.UPLOAD_COPY, afterwardsFunc);
    }

    function movekeep() {
        dbupload.upload(
            sourcewindow,
            dbupload.UPLOAD_MOVE_KEEPING_PATIENTS,
            function () {
                var GV = require('common/GV');
                broadcastPatientSelection(GV.selected_patient_id);
                // we won't delete the patient, but we might e.g. delete a task
                // from a summary view
                if (typeof afterwardsFunc === "function") {
                    afterwardsFunc();
                }
            }
        );
    }
    function move() {
        dbupload.upload(
            sourcewindow,
            dbupload.UPLOAD_MOVE,
            function () {
                broadcastPatientSelection(null);
                // ... deselect patient in case it was deleted
                if (typeof afterwardsFunc === "function") {
                    afterwardsFunc();
                }
            }
        );
    }

    function chooseUploadMethod() {
        if (platform.ios) {
            dlg = Titanium.UI.createAlertDialog({
                title: L('upload_choice_title'),
                message: L('upload_choice_msg'),
                buttonNames: [L('cancel'), L('copy'), L('move_keep_patients'),
                              L('move')]
            });
            dlg.addEventListener('click', function (e) {
                if (e.index === 1) {
                    copy();
                } else if (e.index === 2) {
                    movekeep();
                } else if (e.index === 3) {
                    move();
                } else if (typeof afterwardsFunc === "function") {
                    afterwardsFunc();
                }
                dlg = null;
            });
        } else {
            // Android: max 3 buttons, but we get the Android back button to
            // replace "cancel"
            dlg = Titanium.UI.createAlertDialog({
                title: L('upload_choice_title'),
                message: L('upload_choice_msg'),
                buttonNames: [ L('copy'), L('move_keep_patients'), L('move')]
            });
            dlg.addEventListener('click', function (e) {
                if (e.index === 0) {
                    copy();
                } else if (e.index === 1) {
                    movekeep();
                } else if (e.index === 2) {
                    move();
                } else if (typeof afterwardsFunc === "function") {
                    afterwardsFunc();
                }
                dlg = null;
            });
        }
        dlg.show();
    }

    netcore.setTempServerPasswordAndCall(chooseUploadMethod);
}
exports.upload = upload;

function task_finished_offer_upload(sourcewindow, afterwardsFunc) {
    var storedvars = require('table/storedvars'),
        dlg;
    if (!storedvars.offerUploadAfterEdit.getValue()) {
        // user doesn't want to be offered this regularly
        if (typeof afterwardsFunc === "function") {
            afterwardsFunc();
        }
        return;
    }
    dlg = Titanium.UI.createAlertDialog({
        title: L('task_finished_upload_title'),
        message: L('task_finished_upload_msg'),
        buttonNames: [L('cancel'), L('upload')]
    });
    dlg.addEventListener('click', function (e) {
        if (e.index === 1) { // Upload
            upload(sourcewindow, afterwardsFunc);
        } else {
            if (typeof afterwardsFunc === "function") {
                afterwardsFunc();
            }
        }
        dlg = null;
    });
    dlg.show();
}
exports.task_finished_offer_upload = task_finished_offer_upload;
