#include "widgetconst.h"

namespace widgetconst {

// Some of our height-for-width widgets call a function to set their parent's
// geometry during geometry calls, so there is a risk of infinite recursion.
// Allowing zero such calls gives duff visual results, and allowing any number
// leads to infinite-recursion crashes. So we set a finite limit, e.g. 5-10:

const int SET_GEOMETRY_MAX_REENTRY_DEPTH = 10;

}  // namespace widgetconst
