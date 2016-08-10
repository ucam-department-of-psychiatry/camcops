#pragma once
#include <QAbstractButton>
#include <QLabel>
#include <QObject>
#include <QString>

#define iconFilename(filename) (":/images/camcops/" filename)
#define iconPngFilename(stem) iconFilename(stem ".png")
#define iconTouchedPngFilename(stem) iconFilename(stem "_T.png")

// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap getPixmap(const QString& filename);

// ============================================================================
// Icons
// ============================================================================

QLabel* iconWidget(const QString& filename,
                   QWidget* parent = nullptr,
                   bool scale = true);
#define makeIconWidget(filename, parent) \
    iconWidget(iconFilename(filename), parent)

#define ICON_CAMCOPS(parent) makeIconWidget("camcops.png", parent)
#define ICON_CHAIN(parent) makeIconWidget("chain.png", parent)
#define ICON_TABLE_CHILDARROW(parent) \
    iconWidget(iconFilename("hasChild.png"), parent, false)

// ============================================================================
// Buttons
// ============================================================================

QAbstractButton* iconButton(const QString& normal_filename,
                            const QString& pressed_filename = "",
                            QWidget* parent = nullptr);
#define makeIconButton(stem, parent) \
    iconButton(iconPngFilename(stem), iconTouchedPngFilename(stem), parent)

#define CAMCOPS_BUTTON_BACK(parent) makeIconButton("back", parent)
#define CAMCOPS_BUTTON_LOCKED(parent) makeIconButton("locked", parent)
#define CAMCOPS_BUTTON_PRIVILEGED(parent) makeIconButton("privileged", parent)
#define CAMCOPS_BUTTON_UNLOCKED(parent) makeIconButton("unlocked", parent)

// ============================================================================
// Killing the app
// ============================================================================

void stopApp(const QString& error);

// ============================================================================
// Alerts
// ============================================================================

void alert(const QString& text, const QString& title = QObject::tr("Alert"));
