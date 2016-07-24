#pragma once

#include <QString>


// ============================================================================
// Sizes
// ============================================================================

const int ICONSIZE = 48;
const int SPACE = 4;
const int BIGSPACE = 16;
const int MEDIUMSPACE = 8;

// ============================================================================
// Images
// ============================================================================

#define camcops_icon(filename) (":/images/camcops/" filename)

const QString ICON_TABLE_CHILDARROW = camcops_icon("hasChild.png");
const QString ICON_CHAIN = camcops_icon("chain.png");

// ============================================================================
// Stylesheets
// ============================================================================

#define camcops_stylesheet(filename) (":/stylesheets/" filename)

const QString CSS_CAMCOPS = camcops_stylesheet("camcops.css");
const QString CSS_CAMCOPS_MENU = camcops_stylesheet("camcops_menu.css");
