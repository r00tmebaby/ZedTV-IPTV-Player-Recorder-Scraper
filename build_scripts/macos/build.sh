#!/bin/bash
# Build script for ZedTV IPTV Player (macOS)
# This script tests the application and creates an executable

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "ZedTV IPTV Player - Build System (macOS)"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Project root is two levels up from build_scripts/macos/
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Use venv Python if present
if [ -d ".venv" ]; then
    echo "Using virtual environment..."
    source .venv/bin/activate
    PY="python"
    PIP="pip"
else
    PY="python3"
    PIP="pip3"
fi

echo "Step 0: Installing project dependencies..."
echo "----------------------------------------"
$PIP install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Could not install dependencies from requirements.txt${NC}"
fi

# Ensure pytest and pyinstaller are installed
$PIP install pytest pyinstaller -q

echo ""
echo "Step 1: Running tests (pytest)..."
echo "----------------------------------------"
$PY -m pytest -q
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Tests failed! Fix the errors before building.${NC}"
    exit 1
fi

echo ""
echo "Step 2: Cleaning old build files..."
echo "----------------------------------------"
rm -rf build dist

echo ""
echo "Step 3: Building executable..."
echo "----------------------------------------"
mkdir -p build/spec

$PY -m PyInstaller --clean --noconfirm --noupx \
    --name "ZedTV-IPTV-Player" \
    --onedir --windowed \
    --paths "src" \
    --icon "MEDIA/logo.ico" \
    --collect-all vlc \
    --specpath "build/spec" \
    src/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Build failed!${NC}"
    exit 1
fi

# Remove generated .spec files
rm -rf build/spec

echo ""
echo "Step 4: Bundling VLC runtime (libs + plugins)..."
echo "----------------------------------------"
if [ -d "src/libs/mac" ]; then
    echo "Copying VLC libraries to dist..."
    mkdir -p "dist/ZedTV-IPTV-Player/libs/mac"

    # Copy main libraries
    cp -v src/libs/mac/*.dylib "dist/ZedTV-IPTV-Player/libs/mac/" 2>/dev/null || true

    # Copy plugins
    if [ -d "src/libs/mac/plugins" ]; then
        echo "Copying VLC plugins..."
        cp -r "src/libs/mac/plugins" "dist/ZedTV-IPTV-Player/libs/mac/"
    fi

    echo -e "${GREEN}VLC libraries bundled successfully${NC}"
else
    echo -e "${YELLOW}[WARN] src/libs/mac not found; app will try to use system VLC${NC}"
fi

echo ""
echo "Step 5: Creating launcher script..."
echo "----------------------------------------"
cat > "dist/ZedTV-IPTV-Player/run.sh" << 'EOF'
#!/bin/bash
# Launcher script for ZedTV IPTV Player

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set VLC environment if bundled
if [ -d "libs/mac" ]; then
    export DYLD_LIBRARY_PATH="$SCRIPT_DIR/libs/mac:$DYLD_LIBRARY_PATH"
    export VLC_PLUGIN_PATH="$SCRIPT_DIR/libs/mac/plugins"
fi

# Run the application
./ZedTV-IPTV-Player "$@"
EOF

chmod +x "dist/ZedTV-IPTV-Player/run.sh"
chmod +x "dist/ZedTV-IPTV-Player/ZedTV-IPTV-Player" 2>/dev/null || true

echo ""
echo "Step 6: Code signing (if configured)..."
echo "----------------------------------------"
# Uncomment and configure if you have a Developer ID certificate
# codesign --force --deep --sign "Developer ID Application: Your Name" dist/ZedTV-IPTV-Player/ZedTV-IPTV-Player

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Executable location: dist/ZedTV-IPTV-Player/"
echo "Run with: cd dist/ZedTV-IPTV-Player && ./run.sh"
echo ""
echo "Note: For distribution, consider creating a .app bundle or .dmg"
echo ""
#!/bin/bash
# Build script for ZedTV IPTV Player (Linux)
# This script tests the application and creates an executable

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "ZedTV IPTV Player - Build System (Linux)"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Project root is two levels up from build_scripts/linux/
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Use venv Python if present
if [ -d ".venv" ]; then
    echo "Using virtual environment..."
    source .venv/bin/activate
    PY="python"
    PIP="pip"
else
    PY="python3"
    PIP="pip3"
fi

echo "Step 0: Installing project dependencies..."
echo "----------------------------------------"
$PIP install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Could not install dependencies from requirements.txt${NC}"
fi

# Ensure pytest and pyinstaller are installed
$PIP install pytest pyinstaller -q

echo ""
echo "Step 1: Running tests (pytest)..."
echo "----------------------------------------"
$PY -m pytest -q
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Tests failed! Fix the errors before building.${NC}"
    exit 1
fi

echo ""
echo "Step 2: Cleaning old build files..."
echo "----------------------------------------"
rm -rf build dist

echo ""
echo "Step 3: Building executable..."
echo "----------------------------------------"
mkdir -p build/spec

$PY -m PyInstaller --clean --noconfirm --noupx \
    --name "ZedTV-IPTV-Player" \
    --onedir --windowed \
    --paths "src" \
    --icon "MEDIA/logo.ico" \
    --collect-all vlc \
    --specpath "build/spec" \
    src/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Build failed!${NC}"
    exit 1
fi

# Remove generated .spec files
rm -rf build/spec

echo ""
echo "Step 4: Bundling VLC runtime (libs + plugins)..."
echo "----------------------------------------"
if [ -d "src/libs/linux" ]; then
    echo "Copying VLC libraries to dist..."
    mkdir -p "dist/ZedTV-IPTV-Player/libs/linux"

    # Copy main libraries
    cp -v src/libs/linux/*.so* "dist/ZedTV-IPTV-Player/libs/linux/" 2>/dev/null || true

    # Copy plugins
    if [ -d "src/libs/linux/plugins" ]; then
        echo "Copying VLC plugins..."
        cp -r "src/libs/linux/plugins" "dist/ZedTV-IPTV-Player/libs/linux/"
    fi

    echo -e "${GREEN}VLC libraries bundled successfully${NC}"
else
    echo -e "${YELLOW}[WARN] src/libs/linux not found; app will try to use system VLC${NC}"
fi

echo ""
echo "Step 5: Creating launcher script..."
echo "----------------------------------------"
cat > "dist/ZedTV-IPTV-Player/run.sh" << 'EOF'
#!/bin/bash
# Launcher script for ZedTV IPTV Player

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set VLC environment if bundled
if [ -d "libs/linux" ]; then
    export LD_LIBRARY_PATH="$SCRIPT_DIR/libs/linux:$LD_LIBRARY_PATH"
    export VLC_PLUGIN_PATH="$SCRIPT_DIR/libs/linux/plugins"
fi

# Run the application
./ZedTV-IPTV-Player "$@"
EOF

chmod +x "dist/ZedTV-IPTV-Player/run.sh"
chmod +x "dist/ZedTV-IPTV-Player/ZedTV-IPTV-Player" 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Executable location: dist/ZedTV-IPTV-Player/"
echo "Run with: cd dist/ZedTV-IPTV-Player && ./run.sh"
echo ""

