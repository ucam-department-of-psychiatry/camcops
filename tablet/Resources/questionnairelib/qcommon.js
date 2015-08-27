// qcommon.js
// things common to questionnaire elements

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var imagecache = require('lib/imagecache'),
    UICONSTANTS = require('common/UICONSTANTS'),
    // platform = require('lib/platform'),
    AS_BUTTONS = false,  // !platform.android,
    VI = {
        // Validity indicators. Arbitrary numbering:
        CLEAR: 1,
        REQUIRED: 2,
        PROBLEM: 3,
        NULL_BUT_OPTIONAL: 4
    },
    FOURSTATE = {
        TRUE: 1,
        FALSE: 2,
        NULL: 3,
        NULLMANDATORY: 4
    };

//=============================================================================
// Properties
//=============================================================================

function setDefaultProperty(props, propName, defaultValue) {
    if (props[propName] === undefined) {
        props[propName] = defaultValue;
    }
}
exports.setDefaultProperty = setDefaultProperty;

function requireProperty(props, propName, objectName) {
    if (props[propName] === undefined) {
        throw new Error(objectName + " created without " +
                        propName + " property");
    }
}
exports.requireProperty = requireProperty;

function requireFunctionProperty(props, propName, objectName) {
    if (typeof props[propName] !== "function") {
        throw new Error(objectName + " created without " +
                        propName + " function property");
    }
}
exports.requireFunctionProperty = requireFunctionProperty;

function requireSameLength(props, propOne, propTwo, objectName) {
    if (props[propOne].length !== props[propTwo].length) {
        throw new Error(objectName + " created with " + propOne +
                        " and " + propTwo + " having different lengths");
    }
}
exports.requireSameLength = requireSameLength;

function debugProps(props, objectName) {
    var debugfunc = require('lib/debugfunc');
    Titanium.API.trace("PROPERTIES PASSED TO " + objectName);
    debugfunc.dumpObject(props);
}
exports.debugProps = debugProps;

//=============================================================================
// Base class for all question elements
//=============================================================================

function QuestionElementBase(props) {

    // elementId
    if (props.elementId === undefined) {
        throw new Error("copyVitalPropsToSelf: detected missing elementId");
    }
    this.elementId = props.elementId;

    // pageId
    if (props.pageId === undefined) {
        throw new Error("copyVitalPropsToSelf: detected missing elementId");
    }
    this.pageId = props.pageId;

    // setValueOnlyAfterVisible
    this.setValueOnlyAfterVisible = (props.setValueOnlyAfterVisible ?
            true :
            false // default false
    );

    // willSetOwnValueOnCreation
    this.willSetOwnValueOnCreation = (props.willSetOwnValueOnCreation ?
            true :
            false // default false
    );

    // elementTag
    this.elementTag = props.elementTag; // OK to be undefined

    // visible
    setDefaultProperty(props, "visible", true);
    this.visible = props.visible;
    this.actuallyVisible = null;
    // ... ensure we apply visibility at the start (after which, we track it)

    // mandatory?
    setDefaultProperty(props, "mandatory", true);
    this.mandatory = props.mandatory;

    // enabled?
    setDefaultProperty(props, "enabled", false);
    this.setEnabled(props.enabled);

    // though not obligatory for all, common (so we can use this.X without
    // copying props):
    this.questionnaire = props.questionnaire;
    this.field = props.field;
    this.readOnly = props.readOnly;

    // Other optional properties: left, right, top, bottom, center
}
QuestionElementBase.prototype = {

    setVisible: function (visible) {
        this.visible = visible;
        this.applyVisible();
    },

    setEnabled: function (enabled) {
        this.enabled = enabled;
        /*
            var actuallyEnabled = this.enabled;
            // *** more needed here!
        */
    },

    applyVisible: function () {
        var actuallyVisible = this.visible;
        if (typeof this.isInputRequired === "function" &&
                this.isInputRequired()) {
            // Element needs to be completed; don't make it invisible
            actuallyVisible = true;
        }
        // Code to prevent fiddling with visibility unnecessarily (slow!):
        if (actuallyVisible !== this.actuallyVisible ||
                this.actuallyVisible === null) {
            this.tiview.setVisible(actuallyVisible);
            this.actuallyVisible = actuallyVisible;
        }
    },

    cleanup_base: function () {
        var i,
            uifunc;
        this.cleanup();
        if (this.tiview) {
            uifunc = require('lib/uifunc');
            uifunc.removeAllViewChildren(this.tiview);
            this.tiview = null;
        }
        if (this.elements !== undefined) {
            for (i = 0; i < this.elements.length; ++i) {
                this.elements[i].cleanup_base();
                // which will call cleanup(), as above, recursively
            }
        }
    },

    cleanup: function () {
        // can be overridden
        return;
    }

};
exports.QuestionElementBase = QuestionElementBase;

//=============================================================================
// Titanium properties
//=============================================================================

function copyStandardTiProps(from, to) {
    var lang = require('lib/lang');
    lang.copyProperty(from, to, "height");
    lang.copyProperty(from, to, "width");
    lang.copyProperty(from, to, "left");
    lang.copyProperty(from, to, "right");
    lang.copyProperty(from, to, "top");
    lang.copyProperty(from, to, "bottom");
    lang.copyProperty(from, to, "center");
}
exports.copyStandardTiProps = copyStandardTiProps;

function arrayOfIdenticalElements(element, n) {
    var x = [],
        i;
    for (i = 0; i < n; ++i) {
        x.push(element);
    }
    return x;
}
exports.arrayOfIdenticalElements = arrayOfIdenticalElements;

function isHorizontalPositionDefined(props) {
    if (props === undefined) {
        throw new Error("Miscall to isHorizontalPositionDefined");
    }
    if (props.left !== undefined) {
        return true;
    }
    if (props.right !== undefined) {
        return true;
    }
    if (props.center !== undefined && props.center.x !== undefined) {
        return true;
    }
    return false;
}
exports.isHorizontalPositionDefined = isHorizontalPositionDefined;

function setDefaultHorizontalPosLeft(props, left) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultHorizontalPosLeft");
    }
    if (isHorizontalPositionDefined(props)) {
        return;
    }
    if (left === undefined) {
        left = 0;
    }
    props.left = left;
}
exports.setDefaultHorizontalPosLeft = setDefaultHorizontalPosLeft;

function setDefaultHorizontalPosRight(props, right) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultHorizontalPosRight");
    }
    if (isHorizontalPositionDefined(props)) {
        return;
    }
    if (right === undefined) {
        right = 0;
    }
    props.right = right;
}
exports.setDefaultHorizontalPosRight = setDefaultHorizontalPosRight;

function setDefaultHorizontalPosCenter(props, proportion) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultHorizontalPosCenter");
    }
    if (isHorizontalPositionDefined(props)) {
        return;
    }
    if (proportion === undefined) {
        proportion = '50%';
    }
    if (props.center === undefined) {
        props.center = {};
    }
    props.center.x = proportion;
}
exports.setDefaultHorizontalPosCenter = setDefaultHorizontalPosCenter;

function isVerticalPositionDefined(props) {
    if (props === undefined) {
        throw new Error("Miscall to isVerticalPositionDefined");
    }
    if (props.top !== undefined) {
        return true;
    }
    if (props.bottom !== undefined) {
        return true;
    }
    if (props.center !== undefined && props.center.x !== undefined) {
        return true;
    }
    return false;
}
exports.isVerticalPositionDefined = isVerticalPositionDefined;

function setDefaultVerticalPosTop(props, top) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultVerticalPosTop");
    }
    if (isVerticalPositionDefined(props)) {
        return;
    }
    if (top === undefined) {
        top = 0;
    }
    props.top = top;
}
exports.setDefaultVerticalPosTop = setDefaultVerticalPosTop;

function setDefaultVerticalPosBottom(props, bottom) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultVerticalPosBottom");
    }
    if (isVerticalPositionDefined(props)) {
        return;
    }
    if (bottom === undefined) {
        bottom = 0;
    }
    props.bottom = bottom;
}
exports.setDefaultVerticalPosBottom = setDefaultVerticalPosBottom;

function setDefaultVerticalPosCenter(props, proportion) {
    if (props === undefined) {
        throw new Error("Miscall to setDefaultVerticalPosCenter");
    }
    if (isVerticalPositionDefined(props)) {
        return;
    }
    if (proportion === undefined) {
        proportion = '50%';
    }
    if (props.center === undefined) {
        props.center = {};
    }
    props.center.y = proportion;
}
exports.setDefaultVerticalPosCenter = setDefaultVerticalPosCenter;


//=============================================================================
// Widgets encapsulating Titanium objects
//=============================================================================

function ValidityIndicator(props) {
    //-------------------------------------------------------------------------
    // Embodies an indicator of validity.
    //-------------------------------------------------------------------------
    setDefaultProperty(props, "size",
                       UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE);
    setDefaultProperty(props, "tiprops", {});
    setDefaultHorizontalPosLeft(props.tiprops, 0);
    setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.width = props.size;
    props.tiprops.height = props.size;
    props.tiprops.touchEnabled = false;
    props.tiprops.image = null;

    this.tiview = Titanium.UI.createImageView(props.tiprops);
    this.appearance = VI.CLEAR;
}
ValidityIndicator.prototype = {

    // Appearance
    clear: function () {
        if (this.appearance === VI.CLEAR) {
            return;
        }
        this.tiview.setImage(null); // Android: with no parameter, crash with
        // "Uncaught Error: Requires property name as first parameters."
        this.appearance = VI.CLEAR;
    },

    setRequired: function () {
        if (this.appearance === VI.REQUIRED) {
            return;
        }
        this.tiview.setImage(imagecache.getImage(
            UICONSTANTS.ICON_FIELD_INCOMPLETE_MANDATORY
        ));
        this.appearance = VI.REQUIRED;
    },

    setNullButOptional: function () {
        if (this.appearance === VI.NULL_BUT_OPTIONAL) {
            return;
        }
        this.tiview.setImage(imagecache.getImage(
            UICONSTANTS.ICON_FIELD_INCOMPLETE_OPTIONAL
        ));
        this.appearance = VI.NULL_BUT_OPTIONAL;
    },

    setProblem: function () {
        if (this.appearance === VI.PROBLEM) {
            return;
        }
        this.tiview.setImage(imagecache.getImage(
            UICONSTANTS.ICON_FIELD_PROBLEM
        ));
        this.appearance = VI.PROBLEM;
    },

    cleanup: function () {
        this.tiview = null;
    }
};
exports.ValidityIndicator = ValidityIndicator;

function fourstate(boolvalue, mandatory) {
    if (boolvalue === null) {
        return mandatory ? FOURSTATE.NULLMANDATORY : FOURSTATE.NULL;
    }
    return boolvalue ? FOURSTATE.TRUE : FOURSTATE.FALSE;
}

function StateButton(props) {
    //-------------------------------------------------------------------------
    // Embodies a button, represented by text, with colours to indicate the
    // true/false/null (+/- required) state of a corresponding Boolean
    // variable.
    //-------------------------------------------------------------------------
    // Encapsulates the Titanium text button in its tiview member.
    // Significant properties:
    //      text
    //      big
    //      bold
    //      italic
    //      extraData
    //      +/- tiprops
    var platform = require('lib/platform');
    setDefaultProperty(props, "big", false);
    setDefaultProperty(props, "bold", true);
    setDefaultProperty(props, "italic", false);
    setDefaultProperty(props, "tiprops", {});
    setDefaultHorizontalPosLeft(props.tiprops, UICONSTANTS.SPACE);
    setDefaultVerticalPosTop(props.tiprops, UICONSTANTS.SPACE);
    // we can't align right; we need some sort of space between buttons
    setDefaultProperty(props.tiprops, "width", Titanium.UI.SIZE);
    setDefaultProperty(props.tiprops, "height", Titanium.UI.SIZE);
    setDefaultProperty(props.tiprops, "textAlign",
                       Titanium.UI.TEXT_ALIGNMENT_LEFT);
    props.tiprops.color = UICONSTANTS.TEXTBUTTON_NULL_FG;
    props.tiprops.backgroundColor = UICONSTANTS.TEXTBUTTON_NULL_BG;
    props.tiprops.font = UICONSTANTS.getQuestionnaireFont(props.big,
                                                          props.bold,
                                                          props.italic);
    props.tiprops.title = props.text;
    if (platform.ios) {
        // Titanium.UI.iPhone doesn't exist under MobileWeb
        props.tiprops.style = Titanium.UI.iPhone.SystemButtonStyle.PLAIN;
    }
    props.tiprops.extraData = props.extraData;
    // other properties in props.tiprops: passed to Titanium.UI.createButton

    this.tiview = Titanium.UI.createButton(props.tiprops);
    this.appearance = FOURSTATE.NULL;
}
StateButton.prototype = {
    // Appearance
    setAppearance: function (boolvalue, mandatory) {
        var newappearance = fourstate(boolvalue, mandatory);
        if (this.appearance === newappearance) {
            return;
        }
        switch (newappearance) {
        case FOURSTATE.NULL:
            this.tiview.setColor(UICONSTANTS.TEXTBUTTON_NULL_FG);
            this.tiview.setBackgroundColor(UICONSTANTS.TEXTBUTTON_NULL_BG);
            break;
        case FOURSTATE.NULLMANDATORY:
            this.tiview.setColor(UICONSTANTS.TEXTBUTTON_NULL_REQUIRED_FG);
            this.tiview.setBackgroundColor(
                UICONSTANTS.TEXTBUTTON_NULL_REQUIRED_BG
            );
            break;
        case FOURSTATE.FALSE:
            this.tiview.setColor(UICONSTANTS.TEXTBUTTON_0_FG);
            this.tiview.setBackgroundColor(UICONSTANTS.TEXTBUTTON_0_BG);
            break;
        case FOURSTATE.TRUE:
            this.tiview.setColor(UICONSTANTS.TEXTBUTTON_1_FG);
            this.tiview.setBackgroundColor(UICONSTANTS.TEXTBUTTON_1_BG);
            break;
        default:
            throw new Error("Bad value in StateButton setAppearance()");
        }
        this.appearance = newappearance;
    },

    cleanup: function () {
        this.tiview = null;
    }
};
exports.StateButton = StateButton;

function StateRadio(props) {
    //-------------------------------------------------------------------------
    // Embodies a radio button, with images to indicate the
    // true/false/null (+/- required) state of a corresponding Boolean
    // variable.
    //-------------------------------------------------------------------------
    // Significant properties:
    //      readOnly
    //      extraData
    //      +/- tiprops
    setDefaultProperty(props, "readOnly", false);
    setDefaultProperty(props, "tiprops", {});
    setDefaultHorizontalPosLeft(props.tiprops, 0);
    setDefaultVerticalPosTop(props.tiprops, 0);
    props.tiprops.width = UICONSTANTS.RADIO_BUTTON_ICON_SIZE;
    props.tiprops.height = UICONSTANTS.RADIO_BUTTON_ICON_SIZE;
    props.tiprops.touchEnabled = true;
    props.tiprops.extraData = props.extraData;

    if (AS_BUTTONS) {
        props.tiprops.backgroundImage = UICONSTANTS.ICON_RADIO_UNSELECTED;
        props.tiprops.backgroundSelectedImage = (props.readOnly ?
                UICONSTANTS.ICON_RADIO_UNSELECTED :
                UICONSTANTS.ICON_RADIO_UNSELECTED_T
        );
        this.tiview = Titanium.UI.createButton(props.tiprops);
    } else {
        props.tiprops.image = imagecache.getImage(
            UICONSTANTS.ICON_RADIO_UNSELECTED
        );
        this.tiview = Titanium.UI.createImageView(props.tiprops);
    }

    this.props = props;
    this.appearance = FOURSTATE.NULL;
}
StateRadio.prototype = {
    // Appearance
    setAppearance: function (boolvalue, mandatory) {
        var newappearance = fourstate(boolvalue, mandatory);
        if (this.appearance === newappearance) {
            return;
        }
        switch (newappearance) {
        case FOURSTATE.FALSE:
            /* falls through */
        case FOURSTATE.NULL:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(
                    UICONSTANTS.ICON_RADIO_UNSELECTED
                );
                this.tiview.setBackgroundSelectedImage(this.props.readOnly ?
                        UICONSTANTS.ICON_RADIO_UNSELECTED :
                        UICONSTANTS.ICON_RADIO_UNSELECTED_T
                    );
            } else {
                this.tiview.setImage(imagecache.getImage(
                    UICONSTANTS.ICON_RADIO_UNSELECTED
                ));
            }
            break;
        case FOURSTATE.NULLMANDATORY:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(
                    UICONSTANTS.ICON_RADIO_UNSELECTED_REQUIRED
                );
                this.tiview.setBackgroundSelectedImage(this.props.readOnly ?
                        UICONSTANTS.ICON_RADIO_UNSELECTED :
                        UICONSTANTS.ICON_RADIO_UNSELECTED_T
                    );
            } else {
                this.tiview.setImage(imagecache.getImage(
                    UICONSTANTS.ICON_RADIO_UNSELECTED_REQUIRED
                ));
            }
            break;
        case FOURSTATE.TRUE:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(
                    UICONSTANTS.ICON_RADIO_SELECTED
                );
                this.tiview.setBackgroundSelectedImage(this.props.readOnly ?
                        UICONSTANTS.ICON_RADIO_SELECTED :
                        UICONSTANTS.ICON_RADIO_SELECTED_T
                    );
            } else {
                this.tiview.setImage(imagecache.getImage(
                    UICONSTANTS.ICON_RADIO_SELECTED
                ));
            }
            break;
        default:
            throw new Error("Bad value in StateRadio setAppearance()");
        }
        this.appearance = newappearance;
    },

    cleanup: function () {
        this.tiview = null;
    }
};
exports.StateRadio = StateRadio;

function StateCheck(props) {
    //-------------------------------------------------------------------------
    // Embodies a check (tick) box, with images to indicate the
    // true/false/null (+/- required) state of a corresponding Boolean
    // variable.
    //-------------------------------------------------------------------------
    // Significant properties:
    //      readOnly
    //      red
    //      size
    //      extraData
    //      +/- tiprops
    setDefaultProperty(props, "readOnly", false);
    setDefaultProperty(props, "red", true);
    setDefaultProperty(props, "size",
                       UICONSTANTS.QUESTIONNAIRE_CHECKMARK_IMAGE_SIZE);
    setDefaultProperty(props, "tiprops", {});
    setDefaultHorizontalPosLeft(props.tiprops, 0);
    setDefaultVerticalPosTop(props.tiprops, 0);
    props.tiprops.width = props.size;
    props.tiprops.height = props.size;
    props.tiprops.touchEnabled = true;
    props.tiprops.extraData = props.extraData;

    if (AS_BUTTONS) {
        props.tiprops.backgroundImage = UICONSTANTS.ICON_CHECK_UNSELECTED;
        props.tiprops.backgroundSelectedImage = (props.readOnly ?
                UICONSTANTS.ICON_CHECK_UNSELECTED :
                UICONSTANTS.ICON_CHECK_UNSELECTED_T
        );
        this.tiview = Titanium.UI.createButton(props.tiprops);
    } else {
        props.tiprops.image = imagecache.getImage(
            UICONSTANTS.ICON_CHECK_UNSELECTED
        );
        this.tiview = Titanium.UI.createImageView(props.tiprops);
    }

    this.props = props;
    this.appearance = FOURSTATE.NULL;
}
StateCheck.prototype = {
    // Appearance
    setAppearance: function (boolvalue, mandatory) {
        var newappearance = fourstate(boolvalue, mandatory);
        if (this.appearance === newappearance) {
            return;
        }
        switch (newappearance) {
        case FOURSTATE.NULL:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(
                    UICONSTANTS.ICON_CHECK_UNSELECTED
                );
                this.tiview.setBackgroundSelectedImage(this.props.readOnly ?
                        UICONSTANTS.ICON_CHECK_UNSELECTED :
                        UICONSTANTS.ICON_CHECK_UNSELECTED_T
                    );
            } else {
                this.tiview.setImage(imagecache.getImage(
                    UICONSTANTS.ICON_CHECK_UNSELECTED
                ));
            }
            break;
        case FOURSTATE.NULLMANDATORY:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(
                    UICONSTANTS.ICON_CHECK_UNSELECTED_REQUIRED
                );
                this.tiview.setBackgroundSelectedImage(this.props.readOnly ?
                        UICONSTANTS.ICON_CHECK_UNSELECTED :
                        UICONSTANTS.ICON_CHECK_UNSELECTED_T
                    );
            } else {
                this.tiview.setImage(imagecache.getImage(
                    UICONSTANTS.ICON_CHECK_UNSELECTED_REQUIRED
                ));
            }
            break;
        case FOURSTATE.FALSE:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(imagecache.getImage(
                    this.props.red ?
                            UICONSTANTS.ICON_CHECK_FALSE_RED :
                            UICONSTANTS.ICON_CHECK_FALSE_BLACK
                ));
                this.tiview.setBackgroundSelectedImage(imagecache.getImage(
                    this.props.red ?
                            (this.props.readOnly ?
                                    UICONSTANTS.ICON_CHECK_FALSE_RED :
                                    UICONSTANTS.ICON_CHECK_FALSE_RED_T
                            ) :
                            (this.props.readOnly ?
                                    UICONSTANTS.ICON_CHECK_FALSE_BLACK :
                                    UICONSTANTS.ICON_CHECK_FALSE_BLACK_T
                            )
                ));
            } else {
                this.tiview.setImage(imagecache.getImage(
                    this.props.red ?
                            UICONSTANTS.ICON_CHECK_FALSE_RED :
                            UICONSTANTS.ICON_CHECK_FALSE_BLACK
                ));
            }
            break;
        case FOURSTATE.TRUE:
            if (AS_BUTTONS) {
                this.tiview.setBackgroundImage(imagecache.getImage(
                    this.props.red ?
                            UICONSTANTS.ICON_CHECK_TRUE_RED :
                            UICONSTANTS.ICON_CHECK_TRUE_BLACK
                ));
                this.tiview.setBackgroundSelectedImage(imagecache.getImage(
                    this.props.red ?
                            (this.props.readOnly ?
                                    UICONSTANTS.ICON_CHECK_TRUE_RED :
                                    UICONSTANTS.ICON_CHECK_TRUE_RED_T
                            ) :
                            (this.props.readOnly ?
                                    UICONSTANTS.ICON_CHECK_TRUE_BLACK :
                                    UICONSTANTS.ICON_CHECK_TRUE_BLACK_T
                            )
                ));
            } else {
                this.tiview.setImage(imagecache.getImage(
                    this.props.red ?
                            UICONSTANTS.ICON_CHECK_TRUE_RED :
                            UICONSTANTS.ICON_CHECK_TRUE_BLACK
                ));
            }
            break;
        default:
            throw new Error("Bad value in StateCheck setAppearance()");
        }
        this.appearance = newappearance;
    },

    cleanup: function () {
        this.tiview = null;
    }
};
exports.StateCheck = StateCheck;

//=============================================================================
// More complex widgets, e.g. building on those above
//=============================================================================

function BooleanWidget(props) {
    //-------------------------------------------------------------------------
    // Embodies a widget offering "toggle", "setValue", "unset" (etc.)
    // functions, representing a Boolean variable, either with a check box
    // or text button visual representation.
    //-------------------------------------------------------------------------
    var MODULE_NAME = "BooleanWidget",
        UnderlyingWidget;
    setDefaultProperty(props, "mandatory", true);
    setDefaultProperty(props, "asTextButton", false);
    setDefaultProperty(props, "readOnly", false);
    setDefaultProperty(props, "bistate", false); // true or null
    setDefaultProperty(props, "allowNullSelection", false);
    // ... applicable if !bistate
    setDefaultProperty(props, "red", false);
    // ... applicable if !asTextButton
    setDefaultProperty(props, "size",
                       UICONSTANTS.QUESTIONNAIRE_CHECKMARK_IMAGE_SIZE);
    // ... applicable if !asTextButton
    /* // optional property: fnToggle */
    // optional property: extraData
    // optional property: tiprops
    requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    setDefaultProperty(props, "tiprops", {});
    UnderlyingWidget = props.asTextButton ? StateButton : StateCheck;

    this.props = props;
    this.widget = new UnderlyingWidget(props);
    this.tiview = this.widget.tiview;
    this.value = null;
}
BooleanWidget.prototype = {

    // Logic
    getValue: function () {
        return this.value;
    },

    getValueAsInteger: function () {
        if (this.value === null) {
            return null;
        }
        return this.value ? 1 : 0;
    },

    setValue: function (newValue) {
        var appearanceValue;
        if (newValue === null) {
            this.value = null;
            appearanceValue = this.value;
        } else if (newValue) {
            this.value = true;
            appearanceValue = this.value;
        } else {
            this.value = false;
            if (this.props.bistate) {
                appearanceValue = null;
            } else {
                appearanceValue = this.value;
            }
        }
        this.widget.setAppearance(appearanceValue, this.props.mandatory);
    },

    toggle: function () {
        if (!this.props.bistate && this.props.allowNullSelection) {
            this.setValue(this.value === false ? null : !this.value);
            // maps null to true, true to false, false to null
        } else {
            this.setValue(!this.value);
            // maps null to true, true to false, false to true
        }
        // Communication out
        this.props.setFieldValue(this.getValueAsInteger());
        // RETURN INTEGERS or something will try to write the value "false" as
        // a string to an SQLite integer field - later to be interpreted as
        // true!
    },

    unset: function () {
        this.setValue(null);
        // Communication out
        this.props.setFieldValue(this.getValueAsInteger());
    },

    setMandatory: function (mandatory) {
        this.props.mandatory = mandatory;
        this.setValue(this.value, this.props.mandatory);
    },

    isInputRequired: function () {
        return this.props.mandatory && this.value === null;
    },

    cleanup: function () {
        this.widget = null;
        this.tiview = null;
    }
};
exports.BooleanWidget = BooleanWidget;

function McqGroup(props) {
    //-------------------------------------------------------------------------
    // Embodies a group of widgets (using either a radio button or a text
    // button representation) corresponding to a 1-from-many choice.
    //-------------------------------------------------------------------------
    var MODULE_NAME = "McqGroup",
        i,
        newbutton,
        UnderlyingWidget,
        widgetprops;
    setDefaultProperty(props, "mandatory", true);
    setDefaultProperty(props, "readOnly", false);
    setDefaultProperty(props, "asTextButton", false);
    requireProperty(props, "options", MODULE_NAME);
    // ... also defines number of buttons
    requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    setDefaultProperty(props, "tipropsArray",
                       arrayOfIdenticalElements({}, props.options.length));
    requireSameLength(props, "tipropsArray", "options", MODULE_NAME);
    // optional property: extraData
    UnderlyingWidget = props.asTextButton ? StateButton : StateRadio;

    this.props = props;
    this.selected_index = null;
    this.buttons = [];
    this.appearance = [];

    for (i = 0; i < props.options.length; ++i) {
        widgetprops = {
            readOnly: props.readOnly,
            text: props.asTextButton ? props.options[i].key : "",
            extraData: props.extraData, // more extra data
            tiprops: props.tipropsArray[i]
        };
        widgetprops.tiprops.index_id = i; // extra data
        widgetprops.tiprops.touchEnabled = true;
        newbutton = new UnderlyingWidget(widgetprops);
        this.buttons.push(newbutton);
        this.appearance.push(null);
    }
}
McqGroup.prototype = {

    select: function (index, quietly) {
        //Titanium.API.trace("McqGroup.select: index=" + index +
        //                   ", quietly=" + quietly);
        if (index === undefined || index < 0 ||
                index >= this.buttons.length) { // sanity check
            index = null;
        }
        if (index !== null) { // end up with one selected
            if (this.selected_index !== null) {
                // visually a bit better to vanish-then-appear than to see two
                // transiently
                this.set_button_appearance(this.selected_index, false);
                this.set_button_appearance(index, true);
            } else {
                this.set_button_appearance(index, true);
                this.set_all_false_except(index);
            }
        } else { // end up with none selected
            this.deselect_all();
        }
        this.selected_index = index;
        if (!quietly) {
            // send the data back
            this.props.setFieldValue(this.getValue());
        }
    },

    set_button_appearance: function (button_index, boolvalue) {
        this.buttons[button_index].setAppearance(boolvalue,
                                                 this.props.mandatory);
    },

    set_all_false_except: function (exceptIndex) {
        var i;
        for (i = 0; i < this.buttons.length; ++i) {
            if (i !== exceptIndex) {
                this.set_button_appearance(i, false);
            }
        }
    },

    deselect_all: function () {
        var i;
        for (i = 0; i < this.buttons.length; ++i) {
            this.set_button_appearance(i, null);
        }
    },

    // OTHER
    getIndex: function () {
        return this.selected_index;
    },

    getValue: function () {
        if (this.selected_index === null) {
            return null;
        }
        return this.props.options[this.selected_index].value;
    },

    setIndex: function (index) {
        this.select(index, true);
    },

    setValue: function (value) {
        var lang = require('lib/lang'),
            index = lang.kvpGetIndexByValue(this.props.options, value);
        //Titanium.API.trace("McqGroup.setValue: value=" + value +
        //                   ", index=" + index);
        this.select(index, true);
    },

    setMandatory: function (mandatory) {
        this.props.mandatory = mandatory;
        if (this.selected_index === null) {
            this.deselect_all();
        }
    },

    isInputRequired: function () {
        return (this.props.mandatory && this.selected_index === null);
    },

    // no further cleanup necessary
    cleanup: function () {
        var i;
        for (i = 0; i < this.buttons.length; ++i) {
            this.buttons[i].cleanup();
            this.buttons[i] = null;
        }
    }

};
exports.McqGroup = McqGroup;

//=============================================================================
// Other
//=============================================================================

function makeElement(elementprops) {
    var TypeMaker = require("questionnaire/" + elementprops.type);
    return new TypeMaker(elementprops);
}
exports.makeElement = makeElement;

function processButtonTextForIos(text, flankerLeft, flankerRight) {
    // iOS 7 buttons have no characteristics distinguishing them from plain
    // text, except colour (potentially). So:
    var platform = require('lib/platform');
    if (!platform.ios7plus) {
        return text;
    }
    if (flankerLeft === undefined) {
        flankerLeft = UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_LEFT;
    }
    if (flankerRight === undefined) {
        flankerRight = UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_RIGHT;
    }
    return flankerLeft + text + flankerRight;
}
exports.processButtonTextForIos = processButtonTextForIos;

function determineImageSizeHierarchically(propsSize, fileSize, fallbackSize) {
    // Pair 1 > pair 2 > pair 3. Each has width and height members, or
    // undefined.
    if (propsSize.width && propsSize.height) {
        return propsSize;
    }
    if (fileSize.width && fileSize.height) {
        return fileSize;
    }
    return fallbackSize;
}
exports.determineImageSizeHierarchically = determineImageSizeHierarchically;

/*
function BrokenWidgetTiView(text) {
    return Titanium.UI.createLabel({
        left: 0,
        right: 0,
        top: 0,
        height: Titanium.UI.SIZE,

        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(false, true, false),
        color: UICONSTANTS.WARNING_COLOUR,
        text: text,
        touchEnabled: false,
        // backgroundColor: '#FF0000',
    });
}
exports.BrokenWidgetTiView = BrokenWidgetTiView;
*/
