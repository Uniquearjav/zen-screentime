<!-- # File: README.md -->
<!-- # Location: README.md -->
# Screentime - GTK Screen Time Tracker for Arch Linux

A lightweight GTK4 GUI to track and visualize your screen time on Arch Linux. Supports both X11 and Wayland.

## Features

- 🪟 GTK4 + Libadwaita desktop UI
- 📊 Track active window and application usage
- 🎯 Support for both X11 and Wayland
- 💾 Local SQLite database storage
- 🔄 Background tracking while the GUI is open

## Installation

### System dependencies (Arch)

```bash
sudo pacman -S python-gobject gobject-introspection gtk4 libadwaita
```

### Tracker dependencies (choose your session)

**X11:**
```bash
sudo pacman -S xdotool xorg-xprop
```

**Wayland (Sway):**
```bash
sudo pacman -S sway jq
```

**Wayland (Hyprland):**
```bash
sudo pacman -S hyprland jq
```

## Usage

Run the GTK GUI:
```bash
python3 main.py
```

If you use a virtual environment, create it with system packages so `gi` is available:
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
python3 main.py
```

## Data Storage

Database path:
```
~/.local/share/screentime/screentime.db
```
