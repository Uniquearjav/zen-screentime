# Maintainer: Arjav Choudhary <arjavchoudhary608@gmail.com>
pkgname=zen-screentime
pkgver=1.0.0
pkgrel=1
pkgdesc="A lightweight GTK4 screen time tracker for Arch Linux with X11 and Wayland support"
arch=('any')
url="https://github.com/Uniquearjav/zen-screentime"
license=('MIT')
depends=(
    'python'
    'python-gobject'
    'gtk4'
    'libadwaita'
)
optdepends=(
    'xdotool: X11 session support'
    'xorg-xprop: X11 session support'
    'sway: Wayland (Sway) session support'
    'hyprland: Wayland (Hyprland) session support'
    'jq: JSON parsing for Wayland'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')  # Update this after creating a release

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Create necessary directories
    install -dm755 "$pkgdir/usr/lib/$pkgname"
    install -dm755 "$pkgdir/usr/bin"
    install -dm755 "$pkgdir/usr/share/applications"
    
    # Install main application
    install -Dm755 main.py "$pkgdir/usr/lib/$pkgname/main.py"
    
    # Install screentime module
    cp -r screentime "$pkgdir/usr/lib/$pkgname/"
    
    # Remove __pycache__ if present
    find "$pkgdir/usr/lib/$pkgname" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    
    # Create launcher script
    cat > "$pkgdir/usr/bin/$pkgname" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/zen-screentime/main.py "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/$pkgname"
    
    # Install desktop file
    install -Dm644 "$srcdir/$pkgname-$pkgver/$pkgname.desktop" \
        "$pkgdir/usr/share/applications/$pkgname.desktop"
    
    # Install documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
