$ErrorActionPreference = "Stop"
echo "Installing msys packages..."
C:\tools\msys64\usr\bin\bash -l -c "pacman -S --noconfirm make yasm diffutils awk"
echo "Done."
