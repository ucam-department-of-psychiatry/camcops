// inherit.js

// http://js-bits.blogspot.co.uk/2010/08/javascript-inheritance-done-right.html

/*jslint node: true */
"use strict";

function SurrogateCtor() {
    return;
}

function extend(base, sub) {
    // Titanium.API.trace("extend()");
    // Copy the prototype from the base to setup inheritance
    SurrogateCtor.prototype = base.prototype;
    // Tricky huh?
    sub.prototype = new SurrogateCtor();
    // Remember the constructor property was set wrong, let's fix it
    sub.prototype.constructor = sub;
}
exports.extend = extend;

// Inheritance: http://stackoverflow.com/questions/1595611/
// Advantage of prototype method: efficiency
// Advantage of closure method: all methods bound to the specific instance that
// owns it
