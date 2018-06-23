..  documentation/source/misc/wishlist.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

Wishlist and blue-sky thoughts
==============================

**Server-side “all tasks in full” view, like a clinical text view but for researchers?**

A “research multi-task view” would be an easy extension to the task collection
classes used for trackers and CTVs, if there is demand.

**Improvements to “camcops merge_db” facility**

The merge facility doesn’t yet allow you to say “ID#8 in database A means
something different to ID#8 in database B; don’t merge that”. Should it?
(Example: “research ID” that is group-specific, versus “NHS number” that isn’t.)
More generally: should some ID numbers be visible only to certain groups?

**Server-side ability to edit existing (finalized) task instances?**

Would be done in a generic way, i.e. offer table with {fieldname, comment, old
value, new value}; constrain to min/max or permitted values where applicable; at
first “submit”, show differences and ask for confirmation; audit changes. For
BLOBs, allow option to upload file (or leave unchanged).

**Client-side index of tasks by patient ID, to speed up lookup on the tablet?**

Might be worthwhile on the client side as the number of tasks grows. (The server
already has indexing by patient ID.)

**MRI triggering on task side**

For example: CamCOPS tasks running on a desktop and communicating via TCP/IP
with a tool that talks to an MRI scanner for pulse synchronization and response.

**Further internationalization of task strings**

Should we add an extra field for an ISO-639-1 two-letter language code (e.g.
“en” for English) to the extra strings? Not clear this is required; different
servers can already distribute whichever language they want, so the feature
would only be relevant for “simultaneously multilingual” environments. Deferred
for now.
