# Build Scripts

This directory contains platform-specific build scripts for ZedTV IPTV Player.

## Structure

```
build_scripts/
├── windows/          # Windows build scripts (.bat files)
│   ├── build.bat     # Full build with tests
│   ├── build_quick.bat  # Quick build without tests
│   ├── run_tests.bat    # Run test suite
│   └── quick_test.bat   # Quick test pipeline
├── linux/            # Linux build scripts (.sh files)
│   ├── build.sh      # Full build with tests
│   └── run_tests.sh  # Run test suite
└── macos/            # macOS build scripts (.sh files)
    ├── build.sh      # Full build with tests
    └── run_tests.sh  # Run test suite
```

## Usage

### Windows

From the **project root**:

```cmd
# Full build (with tests)
build_scripts\windows\build.bat

# Quick build (without tests)
build_scripts\windows\build_quick.bat

# Run tests only
build_scripts\windows\run_tests.bat
```

Or use the convenience wrapper in the project root:
```cmd
build.bat
```

### Linux

From the **project root**:

```bash
# Full build (with tests)
bash build_scripts/linux/build.sh

# Run tests only
bash build_scripts/linux/run_tests.sh
```

Or use the convenience wrapper in the project root:
```bash
./build.sh
```

### macOS

From the **project root**:

```bash
# Full build (with tests)
bash build_scripts/macos/build.sh

# Run tests only
bash build_scripts/macos/run_tests.sh
```

Or use the convenience wrapper in the project root:
```bash
./build.sh
```

## What the Build Scripts Do

1. **Check Python installation** and activate virtual environment if present
2. **Install dependencies** from requirements.txt
3. **Run tests** using pytest (can be skipped with quick build)
4. **Clean old build files** (build/ and dist/ directories)
5. **Build executable** using PyInstaller with optimized settings
6. **Bundle VLC libraries** for the target platform from src/libs/{platform}/
7. **Create launcher scripts** (Linux/macOS only)
8. **Verify build** and report success/failure

## Platform-Specific VLC Bundling

### Windows
- Bundles from: `src/libs/win/`
- Output: `dist/ZedTV-IPTV-Player/libvlc.dll` + `plugins/`

### Linux
- Bundles from: `src/libs/linux/`
- Output: `dist/ZedTV-IPTV-Player/libs/linux/` + `run.sh` launcher
- Launcher sets `LD_LIBRARY_PATH` and `VLC_PLUGIN_PATH`

### macOS
- Bundles from: `src/libs/mac/`
- Output: `dist/ZedTV-IPTV-Player/libs/mac/` + `run.sh` launcher
- Launcher sets `DYLD_LIBRARY_PATH` and `VLC_PLUGIN_PATH`

## Output Location

All builds output to: **`dist/ZedTV-IPTV-Player/`**

- **Windows**: Run `ZedTV-IPTV-Player.exe`
- **Linux**: Run `./run.sh` (or `./ZedTV-IPTV-Player` if VLC is system-installed)
- **macOS**: Run `./run.sh` (or `./ZedTV-IPTV-Player` if VLC is system-installed)

## Requirements

- Python 3.7+
- pip
- Virtual environment (recommended)
- Platform-specific VLC libraries in `src/libs/{platform}/`

## Path Resolution

All scripts automatically resolve the project root directory, so they work correctly regardless of where they're called from:

- Windows: Uses `%~dp0..\..` to go up two levels
- Linux/macOS: Uses `$(cd "$SCRIPT_DIR/../.." && pwd)` to go up two levels

This means the scripts can be run from:
- The script directory itself
- The project root (via wrapper scripts)
- Any other location

## Troubleshooting

### "Python not found"
- Make sure Python is installed and in PATH
- On Linux/macOS, try `python3` instead of `python`

### "Tests failed"
- Run `run_tests.bat` (Windows) or `run_tests.sh` (Linux/macOS) to see details
- Fix failing tests before building

### "VLC libraries not found"
- Make sure VLC libraries are in `src/libs/{platform}/`
- See `QUICK_START_CROSSPLATFORM.md` for how to obtain them
- The app will try to use system VLC as fallback

### Build runs from wrong directory
- Scripts automatically change to project root
- Check the "Project root:" output line to verify

## Development Workflow

1. **Make changes** to source code
2. **Run quick test**: `quick_test.bat` (Windows) or similar
3. **Run full tests**: `run_tests.bat` or `run_tests.sh`
4. **Build executable**: `build.bat` or `build.sh`
5. **Test executable**: Run from `dist/ZedTV-IPTV-Player/`

## Distribution

After building:

- **Windows**: Distribute the entire `dist/ZedTV-IPTV-Player/` folder
- **Linux**: Consider creating an AppImage or .deb package
- **macOS**: Consider creating a .app bundle or .dmg file

See individual platform documentation for advanced packaging options.

