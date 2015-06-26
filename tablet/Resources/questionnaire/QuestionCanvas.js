// QuestionCanvas.js
// Editable image display.

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

/*jslint node: true */

var platform = require('lib/platform');

if (platform.android) {
    // Android -- webview slow; Ti.Paint broken but I fixed it, then
    // customized it
    module.exports = require('questionnaire/QuestionCanvas_androidtipaint');
} else {
    // iOS -- Ti.Paint broken; on the other hand, webview faster.
    module.exports = require('questionnaire/QuestionCanvas_webview');
}

/*
    "Dirty" system:
    - manual reset: dirtyInFramework becomes true, canvas/dirty flag becomes
      false
    - draw lines: canvas/dirty flag becomes true

    - canvas/dirty flag becomes clear on setImage or clearImage
*/