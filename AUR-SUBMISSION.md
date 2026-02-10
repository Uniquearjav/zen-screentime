# AUR Submission Guide for zen-screentime

## Prerequisites

1. **Create an AUR account**: https://aur.archlinux.org/register
2. **Setup SSH key**: Add your SSH public key to your AUR account
3. **Install required tools**:
   ```bash
   sudo pacman -S base-devel git
   ```

## Steps to Upload to AUR

### 1. Create a GitHub Release

First, create a release on GitHub:

```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

Then go to: https://github.com/Uniquearjav/zen-screentime/releases/new
- Create a new release with tag `v1.0.0`
- GitHub will automatically create a tarball at:
  `https://github.com/Uniquearjav/zen-screentime/archive/v1.0.0.tar.gz`

### 2. Update PKGBUILD SHA256

Download the release tarball and calculate its checksum:

```bash
curl -L https://github.com/Uniquearjav/zen-screentime/archive/v1.0.0.tar.gz -o zen-screentime-1.0.0.tar.gz
sha256sum zen-screentime-1.0.0.tar.gz
```

Update the `sha256sums` line in PKGBUILD with the actual checksum (replace 'SKIP').

### 3. Update Maintainer Info in PKGBUILD

Edit PKGBUILD and replace:
```bash
# Maintainer: Your Name <your.email@example.com>
```
with your actual name and email.

### 4. Test the PKGBUILD Locally

```bash
# Test build
makepkg -si

# Test the application
zen-screentime

# Clean up
makepkg --cleanbuild
```

### 5. Generate .SRCINFO

```bash
makepkg --printsrcinfo > .SRCINFO
```

### 6. Clone AUR Repository

```bash
# Clone the empty AUR repository
git clone ssh://aur@aur.archlinux.org/zen-screentime.git aur-zen-screentime
cd aur-zen-screentime

# Copy files
cp ../PKGBUILD .
cp ../zen-screentime.desktop .
cp ../.SRCINFO .

# Add and commit
git add PKGBUILD zen-screentime.desktop .SRCINFO
git commit -m "Initial import: zen-screentime 1.0.0"

# Push to AUR
git push origin master
```

### 7. Verify Upload

Visit: https://aur.archlinux.org/packages/zen-screentime

## Updating the Package

When releasing a new version:

1. Update `pkgver` in PKGBUILD
2. Reset `pkgrel` to 1
3. Create new GitHub release
4. Update `sha256sums` with new tarball checksum
5. Generate new .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
6. Commit and push to AUR:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version X.Y.Z"
   git push
   ```

## Testing Installation from AUR

After uploading, users can install with:
```bash
# Using yay
yay -S zen-screentime

# Using paru
paru -S zen-screentime

# Manual installation
git clone https://aur.archlinux.org/zen-screentime.git
cd zen-screentime
makepkg -si
```

## Files Overview

- **PKGBUILD**: Build instructions for the package
- **zen-screentime.desktop**: Desktop entry file for application launcher
- **.SRCINFO**: Metadata file (auto-generated from PKGBUILD)

## Additional Resources

- AUR Submission Guidelines: https://wiki.archlinux.org/title/AUR_submission_guidelines
- PKGBUILD Reference: https://wiki.archlinux.org/title/PKGBUILD
- Creating Packages: https://wiki.archlinux.org/title/Creating_packages
