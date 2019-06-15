// html_to_attributed_string.js

/*
===============================================================================
AttributedString from HTML
===============================================================================

As of Appcelerator 4.0, you can do bold/italic etc. _within_ a string.
But it's a bit fiddly. You use an AttributedString, and then pass that to the
attributedString attribute of createLabel().

API:
- http://docs.appcelerator.com/platform/latest/#!/guide/Attributed_Strings
- http://docs.appcelerator.com/platform/latest/#!/api/Titanium.UI.AttributedString

Others' HTML-to-AS conversion:
- http://www.tidev.io/2014/11/13/using-basic-html-in-labels-on-ios-like-android/
  - https://github.com/FokkeZB/ti-html2as/blob/master/index.js
  - ... but this uses a callback; would have to modify to use a direct HTML parser

Amenable to a simple transformation in the calling function, as below.

===============================================================================
TESTING
===============================================================================
On Mac OS X:

sudo npm install -g n  # use Node Package Manager to install 'n'
# sudo n stable  # use 'n' to latest stable version of node
sudo n 0.12  # confirmed with Titanium

# For Titanium:
titanium sdk
titanium sdk install 4.0.0.GA
titanium setup

# sudo npm install -g gittio  # gitTio module manager; repeat if fails at first

# gittio install -g  # see http://gitt.io/cli
# [from project directory]
# gittio info ti-htmlparser2  # WORKS
# gittio install ti-htmlparser2  # NOT WORKING

# $ sudo npm install htmlparser2
# $ sudo npm install entities

*/

/*jslint node: true, regexp: true */
"use strict";
/*global Titanium */

var htmlparser = require("htmlparser2"),
    entities = require("entities"),
    // References to the full namespace to they get packaged for device builds:
    references = [
        Titanium.UI.AttributedString
    ],
    ns = Titanium.UI;

if (parseInt(Titanium.version.split('.')[0], 10) < 4) {
    references.push(Titanium.UI.iOS.AttributedString);
    ns = Titanium.UI.iOS;
}

function walker(node, parameters, outerFont) {
    var innerFont = null,
        offset,
        length;

    if (node.type === 'text') {
        parameters.text += entities.decodeHTML(node.data);
    } else if (node.type === 'tag' && node.children) {
        // clone font property from wrapping tags
        if (outerFont) {
            innerFont = {};
            if (outerFont.fontWeight) {
                innerFont.fontWeight = outerFont.fontWeight;
            }
            if (outerFont.fontFamily) {
                innerFont.fontFamily = outerFont.fontFamily;
            }
            if (outerFont.fontSize) {
                innerFont.fontSize = outerFont.fontSize;
            }
        }

        // override font properties from this tag
        if (node.name === 'strong' || node.name === 'b') {
            innerFont = innerFont || {};
            innerFont.fontWeight = 'bold';

        } else if (node.name === 'font' && node.attribs) {

            if (node.attribs.face) {
                innerFont = innerFont || {};
                innerFont.fontFamily = node.attribs.face;
            }

            if (node.attribs.size) {
                innerFont = innerFont || {};
                innerFont.fontSize = node.attribs.size;
            }
        }

        // save length before children
        offset = parameters.text.length;

        // walk children
        node.children.forEach(function onEach(child) {
            parameters = walker(child, parameters, innerFont);
        });

        // calculate length of (grant)children text nodes
        length = parameters.text.length - offset;

        // only apply attributes if we wrap text
        if (length > 0) {

            if (node.name === 'a' && node.attribs && node.attribs.href) {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_LINK,
                    value: node.attribs.href,
                    range: [offset, length]
                });

            } else if (node.name === 'u') {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_UNDERLINES_STYLE,
                    value: ns.ATTRIBUTE_UNDERLINE_STYLE_SINGLE,
                    range: [offset, length]
                });

            } else if (node.name === 'i' || node.name === 'em') {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_OBLIQUENESS,
                    value: 0.25,
                    range: [offset, length]
                });

            } else if (node.name === 'strike' || node.name === 'del' || node.name === 's') {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_STRIKETHROUGH_STYLE,
                    value: ns.ATTRIBUTE_UNDERLINE_STYLE_SINGLE,
                    range: [offset, length]
                });

            } else if (node.name === 'effect') {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_TEXT_EFFECT,
                    value: ns.ATTRIBUTE_LETTERPRESS_STYLE,
                    range: [offset, length]
                });

            } else if (node.name === 'kern' && node.attribs && node.attribs.value) {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_KERN,
                    value: node.attribs.value,
                    range: [offset, length]
                });

            } else if (node.name === 'expansion' && node.attribs && node.attribs.value) {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_EXPANSION,
                    value: node.attribs.value,
                    range: [offset, length]
                });

            } else if (node.name === 'font' && node.attribs && node.attribs.color) {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_FOREGROUND_COLOR,
                    value: node.attribs.color,
                    range: [offset, length]
                });
            }

            // if we have a font to set
            if (innerFont) {
                parameters.attributes.unshift({
                    type: ns.ATTRIBUTE_FONT,
                    value: innerFont,
                    range: [offset, length]
                });
            }
        }
    }
    return parameters;
}

function parseCallback(html, callback) {
    var parser = new htmlparser.Parser(new htmlparser.DomHandler(function (error, dom) {
        if (error) {
            callback(error);
        } else {
            var parameters = walker(
                    {type: 'tag', children: dom},
                    {text: '', attributes: []}
                ),
                attr = ns.createAttributedString(parameters);
            callback(null, attr);
        }
    }));
    // remove newlines
    html = html.replace(/[\r\n]+/gm, ' ').replace(/\s+/g, ' ');
    // replace <br> with newlines
    html = html.replace(/<br[^>]*>/gm, '\n');
    parser.parseComplete(html);
}
exports.parseCallback = parseCallback;

function parseSynchronous(html) {
    // This is the RNC bit.
    var attributedString,
        parameters,
        parser;
    function parserCallback(error, dom) {
        if (error) {
            attributedString = null;
        } else {
            parameters = walker(
                {type: 'tag', children: dom},
                {text: '', attributes: []}
            );
            attributedString = ns.createAttributedString(parameters);
        }
    }
    parser = new htmlparser.Parser(new htmlparser.DomHandler(parserCallback));
    Titanium.API.info("starting");
    // remove newlines
    html = html.replace(/[\r\n]+/gm, ' ').replace(/\s+/g, ' ');
    // replace <br> with newlines
    html = html.replace(/<br[^>]*>/gm, '\n');
    // parse HTML
    parser.parseComplete(html);
    Titanium.API.info("finishing");
    return attributedString;
}
exports.parseSynchronous = parseSynchronous;
