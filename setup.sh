#!/bin/bash
# File: setup.sh
# Location: setup.sh
# Quick setup script for Screentime GTK GUI

set -euo pipefail

echo "=== Screentime GTK Setup ==="

echo "Installing GTK dependencies..."
sudo pacman -S --needed python-gobject gobject-introspection gtk4 libadwaita

echo "Detecting display server..."
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "✓ Detected Wayland session"

    if command -v swaymsg &> /dev/null; then
        echo "✓ Sway detected"
    elif command -v hyprctl &> /dev/null; then
        echo "✓ Hyprland detected"
    else
        echo "⚠ Warning: No supported Wayland compositor detected"
        echo "  Please install Sway or Hyprland"
    fi
elif [ -n "${DISPLAY:-}" ]; then
    echo "✓ Detected X11 session"

    if ! command -v xdotool &> /dev/null; then
        echo "Installing xdotool..."
        sudo pacman -S --needed xdotool
    else
        echo "✓ xdotool installed"
    fi

    if ! command -v xprop &> /dev/null; then
        echo "Installing xorg-xprop..."
        sudo pacman -S --needed xorg-xprop
    else
        echo "✓ xorg-xprop installed"
    fi
else
    echo "⚠ Could not detect display server"
fi

echo ""
echo "=== Setup Complete ==="
echo "Run: python3 main.py"
