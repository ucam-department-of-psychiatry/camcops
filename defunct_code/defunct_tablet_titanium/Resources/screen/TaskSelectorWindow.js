// TaskSelectorWindow.js

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

/*jslint node: true */
"use strict";

var lang = require('lib/lang'),
    TaskWindowCommon = require('screen/TaskWindowCommon');

function TaskSelectorWindow(tasktype, tasktitle, taskhtml) {
    TaskWindowCommon.call(this, false, tasktype, tasktitle, taskhtml);
    // call base constructor
}
lang.inheritPrototype(TaskSelectorWindow, TaskWindowCommon);
// lang.extendPrototype(TaskSelectorWindow, {});
module.exports = TaskSelectorWindow;
