#!/bin/bash
# Convenience wrapper for platform-specific test script

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    echo "Unsupported platform: $OSTYPE"
    echo "Please run the appropriate script from build_scripts/ manually"
    exit 1
fi

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run platform-specific test script
echo "Detected platform: $PLATFORM"
echo "Running test script: build_scripts/$PLATFORM/run_tests.sh"
echo ""

bash "$SCRIPT_DIR/build_scripts/$PLATFORM/run_tests.sh" "$@"
#!/bin/bash
# Convenience wrapper for platform-specific build script

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    echo "Unsupported platform: $OSTYPE"
    echo "Please run the appropriate script from build_scripts/ manually"
    exit 1
fi

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run platform-specific build script
echo "Detected platform: $PLATFORM"
echo "Running build script: build_scripts/$PLATFORM/build.sh"
echo ""

bash "$SCRIPT_DIR/build_scripts/$PLATFORM/build.sh" "$@"

