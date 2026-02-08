#!/bin/bash
# Quick setup script for Screentime

echo "=== Screentime Setup ==="
echo ""

# Detect display server
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
elif [ -n "$DISPLAY" ]; then
    echo "✓ Detected X11 session"
    
    # Check for required tools
    if ! command -v xdotool &> /dev/null; then
        echo "⚠ xdotool not found. Installing..."
        sudo pacman -S --needed xdotool
    else
        echo "✓ xdotool installed"
    fi
    
    if ! command -v xprop &> /dev/null; then
        echo "⚠ xprop not found. Installing..."
        sudo pacman -S --needed xorg-xprop
    else
        echo "✓ xprop installed"
    fi
else
    echo "⚠ Could not detect display server"
fi

echo ""
echo "Installing Python dependencies..."
sudo pacman -S --needed python-click

echo ""
echo "Making screentime.py executable..."
chmod +x screentime.py

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Quick start:"
echo "  ./screentime.py start --daemon   # Start tracking in background"
echo "  ./screentime.py stats            # View today's stats"
echo "  ./screentime.py --help           # See all commands"
echo ""
echo "Optional: Create system-wide command"
echo "  sudo ln -s $(pwd)/screentime.py /usr/local/bin/screentime"
echo ""
