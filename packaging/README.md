# Packaging Files

This folder contains files related to packaging and distribution of ZedTV IPTV Player.

## Contents

### `installer.iss`
Inno Setup script for creating Windows installers (.exe).

**What it does:**
- Creates a professional Windows installer
- Handles file installation
- Creates Start Menu shortcuts
- Manages uninstallation
- Sets up registry entries if needed

**Usage:**
1. Install Inno Setup (https://jrsoftware.org/isinfo.php)
2. Open `installer.iss` in Inno Setup Compiler
3. Click "Compile" to build the installer
4. Find the installer in the `Output` folder

**Or use the build script:**
```cmd
build_scripts\windows\advanced\build_installer.bat
```

## Future Additions

This folder may eventually contain:
- **Linux packaging:**
  - `.deb` package scripts (Debian/Ubuntu)
  - `.rpm` package scripts (Fedora/RHEL)
  - AppImage configuration
  - Flatpak manifest
  - Snap configuration

- **macOS packaging:**
  - `.app` bundle scripts
  - `.dmg` creation scripts
  - `.pkg` installer scripts
  - Code signing configuration

- **Cross-platform:**
  - Distribution metadata
  - License files for packaging
  - Desktop entry files
  - Icon files in multiple formats

## Related Build Scripts

- `build_scripts/windows/advanced/build_installer.bat` - Builds Windows installer
- `build_scripts/windows/advanced/create_package.bat` - Creates distribution package

## Notes

- Windows installer requires Inno Setup to be installed
- Installer configuration can be customized in `installer.iss`
- Always test installers in clean VMs before distribution
- Update version numbers in `installer.iss` when releasing

