# Advanced Windows Build Scripts

This folder contains advanced and specialized build scripts for Windows.

## Contents

### `build_all.bat`
Comprehensive build script that creates multiple build configurations:
- Standard PyInstaller build
- Nuitka build (alternative compiler)
- Debug builds
- Release builds

**Usage:**
```cmd
build_scripts\windows\advanced\build_all.bat
```

**When to use:**
- Creating multiple build variants
- Testing different compilers
- Preparing for release
- Comprehensive testing before distribution

---

### `build_installer.bat`
Creates a Windows installer (.exe) using Inno Setup.

**Prerequisites:**
- Inno Setup installed (https://jrsoftware.org/isinfo.php)
- Application already built (run `build.bat` first)
- `packaging/installer.iss` configured

**Usage:**
```cmd
REM 1. Build the application first
build_scripts\windows\build.bat

REM 2. Create installer
build_scripts\windows\advanced\build_installer.bat
```

**Output:**
- Windows installer in `Output/` folder
- Self-contained .exe that installs the application
- Includes uninstaller

---

### `nuitka_build.bat`
Alternative build using Nuitka compiler instead of PyInstaller.

**What is Nuitka?**
Nuitka is a Python-to-C++ compiler that can create faster executables than PyInstaller. It compiles Python code to C++ and then to native code.

**Advantages:**
- Potentially faster startup time
- Better performance
- True compilation (not just packaging)

**Disadvantages:**
- Longer compile time
- More dependencies
- Larger memory usage during build

**Prerequisites:**
```cmd
pip install nuitka
pip install -r requirements_nuitka.txt
```

**Usage:**
```cmd
build_scripts\windows\advanced\nuitka_build.bat
```

---

### `create_package.bat`
Creates a distribution package (ZIP) of the built application.

**What it does:**
- Bundles the built executable
- Includes VLC libraries
- Adds README and LICENSE
- Creates version-stamped ZIP file

**Usage:**
```cmd
REM 1. Build first
build_scripts\windows\build.bat

REM 2. Create package
build_scripts\windows\advanced\create_package.bat
```

**Output:**
- `ZedTV-IPTV-Player-v{version}.zip` ready for distribution
- Contains everything needed to run the app
- Can be distributed without installer

---

## When to Use These Scripts

### Regular Development
Use the standard build scripts:
```cmd
build_scripts\windows\build.bat       # Full build
build_scripts\windows\build_quick.bat # Quick build
```

### Release Preparation
Use advanced scripts:
```cmd
build_scripts\windows\advanced\build_all.bat        # All variants
build_scripts\windows\advanced\build_installer.bat  # Create installer
build_scripts\windows\advanced\create_package.bat   # Create ZIP
```

### Performance Testing
```cmd
build_scripts\windows\advanced\nuitka_build.bat  # Compile with Nuitka
```

## Comparison: PyInstaller vs Nuitka

| Feature | PyInstaller | Nuitka |
|---------|-------------|--------|
| Build time | Fast (minutes) | Slow (10-30 min) |
| Startup time | Good | Faster |
| Runtime performance | Good | Better |
| Compatibility | Excellent | Good |
| Ease of use | Simple | Complex |
| Best for | Quick iteration | Final release |

## File Requirements

These scripts may reference:
- `packaging/installer.iss` - Installer configuration
- `specs/ZedTV-IPTV-Player.spec` - PyInstaller spec
- `requirements_nuitka.txt` - Nuitka dependencies
- `src/libs/win/` - VLC libraries

## Notes

- All scripts should be run from project root (path resolution built-in)
- Scripts will activate `.venv` if present
- Check script output for errors
- Test all builds before distributing
- Always scan installers with antivirus before distribution

## Troubleshooting

### Inno Setup not found
Install from: https://jrsoftware.org/isinfo.php

### Nuitka build fails
```cmd
pip install --upgrade nuitka
pip install -r requirements_nuitka.txt
```

### Build succeeds but app won't run
- Check VLC libraries are bundled
- Verify all dependencies in dist folder
- Test in clean VM
- Check antivirus isn't blocking

## Related Documentation

- `build_scripts/README.md` - Main build system docs
- `packaging/README.md` - Packaging information
- `specs/README.md` - Spec file documentation

