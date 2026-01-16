#!/bin/bash
# Interactive CLI output testing with Docker
# Usage: ./test-cli-output.sh [output-mode] [options]
#
# Examples:
#   ./test-cli-output.sh                    # Interactive mode (default)
#   ./test-cli-output.sh interactive        # Interactive mode with Rich
#   ./test-cli-output.sh ci                 # CI mode with annotations
#   ./test-cli-output.sh json               # JSON output
#   ./test-cli-output.sh quiet              # Quiet mode (errors only)
#   ./test-cli-output.sh interactive -v     # Verbose interactive mode
#
set -e

cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OUTPUT_MODE="${1:-interactive}"
shift 2>/dev/null || true
EXTRA_ARGS="$@"

echo -e "${BLUE}=== CLI Output Test ===${NC}"
echo -e "Output mode: ${GREEN}${OUTPUT_MODE}${NC}"
echo -e "Extra args: ${YELLOW}${EXTRA_ARGS}${NC}"
echo ""

# Check if Docker containers are running
check_containers() {
    if ! docker-compose -f integration/integration/docker/docker-compose.yml ps --quiet 2>/dev/null | grep -q .; then
        return 1
    fi

    # Check if containers are healthy
    local unhealthy=$(docker-compose -f integration/docker/docker-compose.yml ps 2>/dev/null | grep -E "(unhealthy|starting)" || true)
    if [ -n "$unhealthy" ]; then
        return 1
    fi

    return 0
}

# Start Docker containers if needed
start_containers() {
    echo -e "${YELLOW}Starting Docker containers...${NC}"
    docker-compose -f integration/docker/docker-compose.yml up -d

    echo -e "${YELLOW}Waiting for containers to be healthy...${NC}"
    local max_wait=60
    local waited=0
    while ! check_containers; do
        sleep 2
        waited=$((waited + 2))
        if [ $waited -ge $max_wait ]; then
            echo -e "${RED}Containers failed to start within ${max_wait}s${NC}"
            exit 1
        fi
        echo -n "."
    done
    echo ""
    echo -e "${GREEN}Containers ready!${NC}"
}

# Ensure rich is available
check_rich() {
    if ! python3 -c "import rich" 2>/dev/null; then
        echo -e "${YELLOW}Installing rich library...${NC}"
        pip3 install --user rich 2>/dev/null || pipx install rich 2>/dev/null || {
            echo -e "${RED}Failed to install rich. Please install manually: pip3 install rich${NC}"
            exit 1
        }
    fi
}

# Main
if ! check_containers; then
    start_containers
else
    echo -e "${GREEN}Docker containers already running${NC}"
fi

# Check rich for interactive mode
if [ "$OUTPUT_MODE" = "interactive" ]; then
    check_rich
fi

echo ""
echo -e "${BLUE}Running db_sync_tool in RECEIVER mode...${NC}"
echo -e "${YELLOW}Config: integration/scenario/receiver/typo3/typo3_env.json${NC}"
echo ""

# Build the command
CMD="python3 -m db_sync_tool"
CMD="$CMD -f integration/scenario/receiver/typo3/typo3_env.json"
CMD="$CMD --output $OUTPUT_MODE"
CMD="$CMD $EXTRA_ARGS"

echo -e "${BLUE}Command: ${NC}$CMD"
echo ""
echo -e "${BLUE}--- Output Start ---${NC}"
echo ""

# Run from project root
cd ..
$CMD

echo ""
echo -e "${BLUE}--- Output End ---${NC}"
echo ""
echo -e "${GREEN}Test complete!${NC}"
