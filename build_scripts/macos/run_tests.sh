#!/bin/bash
# Run all tests (macOS)

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================"
echo "Running Test Suite"
echo "========================================"
echo ""

# Use venv if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests
python -m unittest discover -s tests -p "test_*.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "TESTS FAILED!"
    exit 1
else
    echo ""
    echo "ALL TESTS PASSED!"
    exit 0
fi
#!/bin/bash
# Run all tests (Linux/macOS)

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================"
echo "Running Test Suite"
echo "========================================"
echo ""

# Use venv if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests
python -m unittest discover -s tests -p "test_*.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "TESTS FAILED!"
    exit 1
else
    echo ""
    echo "ALL TESTS PASSED!"
    exit 0
fi

