/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var DBNAME = "junk.db",
    PKVAL = 1,
    ICONSIZE = 48,
    IM_PR = "/images/camcops/",  // image filename prefix
    ICON_RADIO_UNSELECTED = IM_PR + 'radio_unselected.png',
    ICON_RADIO_UNSELECTED_T = IM_PR + 'radio_unselected_T.png',
    ICON_RADIO_SELECTED = IM_PR + 'radio_selected.png',
    ICON_RADIO_SELECTED_T = IM_PR + 'radio_selected_T.png',
    view = Titanium.UI.createView({
        layout: 'vertical',
        backgroundColor: '#FFFFFF'
    }),
    button = Titanium.UI.createButton({
        width: ICONSIZE,
        height: ICONSIZE,
        touchEnabled: true,
        backgroundImage: ICON_RADIO_UNSELECTED,
        backgroundSelectedImage: ICON_RADIO_UNSELECTED_T,
    }),
    state = false,
    win = Titanium.UI.createWindow();

function rnd(min, max) {
    return Math.random() * (max - min) + min;
}

function standalone_execute_noreturn(query, args) {
    var db = Titanium.Database.open(DBNAME),
        cursor;
    if (args === undefined) {
        cursor = db.execute(query);
    } else {
        cursor = db.execute(query, args);
    }
    if (cursor !== null) {
        cursor.close();
    }
    db.close();
}

function access_db() {
    Titanium.API.info("access_db: start");
    standalone_execute_noreturn(
        "UPDATE t SET value = ? WHERE pk = ?",
        [rnd(0, 1000), PKVAL]
    );
    Titanium.API.info("access_db: end");
}

function makedb() {
    standalone_execute_noreturn(
        "CREATE TABLE IF NOT EXISTS t (pk INTEGER, value INTEGER)"
    );
}

function toggle_appearance() {
    Titanium.API.info("toggle_appearance: start");
    state = !state;
    if (state) {
        button.setBackgroundImage(ICON_RADIO_SELECTED);
        button.setBackgroundSelectedImage(ICON_RADIO_SELECTED_T);
    } else {
        button.setBackgroundImage(ICON_RADIO_UNSELECTED);
        button.setBackgroundSelectedImage(ICON_RADIO_UNSELECTED_T);
    }
    Titanium.API.info("toggle_appearance: end");
}

function click() {
    access_db();
    toggle_appearance();
}

makedb();
button.addEventListener("click", click);
view.add(button);
win.add(view);
win.open();
