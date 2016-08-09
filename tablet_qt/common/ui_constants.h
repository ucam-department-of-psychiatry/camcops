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

#define camcopsIcon(filename) (":/images/camcops/" filename)

const QString ICON_TABLE_CHILDARROW = camcopsIcon("hasChild.png");
const QString ICON_CHAIN = camcopsIcon("chain.png");

// ============================================================================
// Stylesheets
// ============================================================================

#define camcopsStylesheet(filename) (":/stylesheets/" filename)

const QString CSS_CAMCOPS = camcopsStylesheet("camcops.css");
const QString CSS_CAMCOPS_MENU = camcopsStylesheet("camcops_menu.css");
