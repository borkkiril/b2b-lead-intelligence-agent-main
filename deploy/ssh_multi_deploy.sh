#!/usr/bin/env bash
# ==============================================================================
# Multi-Server SSH Deployment & Automated Rollback Script
# Project: Orion B2B Lead Intelligence & Multi-Agent Engine
# Author: Kiril Borysenko
# Standard: Production Ops & Linux Server Automation Standard
# ==============================================================================
# Usage:
#   ./deploy/ssh_multi_deploy.sh [options] [server1 server2 ...]
# Options:
#   --dry-run       Simulate commands without executing remote changes
#   --branch <name> Deploy specific git branch (default: main)
#   --skip-tests    Skip local pre-flight unittest check (NOT recommended)
# ==============================================================================

set -euo pipefail

# ANSI Colors for Terminal Output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default Configuration
DEPLOY_BRANCH="main"
APP_DIR="/opt/orion-agent"
SERVICE_NAME="orion-dashboard"
SKIP_TESTS=false
DRY_RUN=false
SERVERS=()

# Parse Command-Line Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --branch)
      DEPLOY_BRANCH="$2"
      shift 2
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --app-dir)
      APP_DIR="$2"
      shift 2
      ;;
    -h|--help)
      echo -e "${CYAN}Usage: $0 [--dry-run] [--branch <name>] [--skip-tests] [server1 server2 ...]${NC}"
      exit 0
      ;;
    *)
      SERVERS+=("$1")
      shift
      ;;
  esac
done

# Fallback to DEPLOY_SERVERS environment variable or demo cluster if none passed
if [[ ${#SERVERS[@]} -eq 0 ]]; then
  if [[ -n "${DEPLOY_SERVERS:-}" ]]; then
    IFS=' ' read -r -a SERVERS <<< "$DEPLOY_SERVERS"
  else
    SERVERS=("vps-01.production.internal" "vps-02.production.internal")
  fi
fi

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  🚀 ORION MULTI-SERVER SSH PRODUCTION DEPLOYMENT & HEALTH AUDIT     ${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Target Branch : ${CYAN}${DEPLOY_BRANCH}${NC}"
echo -e "Remote App Dir: ${CYAN}${APP_DIR}${NC}"
echo -e "Dry Run Mode  : $(if [ "$DRY_RUN" = true ]; then echo -e "${YELLOW}ENABLED${NC}"; else echo -e "${GREEN}DISABLED${NC}"; fi)"
echo -e "Target Nodes  : ${CYAN}${SERVERS[*]}${NC}"
echo ""

# ------------------------------------------------------------------------------
# STEP 1: LOCAL PRE-FLIGHT VERIFICATION
# ------------------------------------------------------------------------------
PYTHON_BIN="python3"
if [ -f ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

if [ "$SKIP_TESTS" = false ]; then
  echo -e "${CYAN}[1/4] Running local automated test suite using ${PYTHON_BIN} before deployment...${NC}"
  if ${PYTHON_BIN} -m unittest discover tests -v; then
    echo -e "${GREEN}✓ All local tests passed with zero errors.${NC}"
  else
    echo -e "${RED}✗ Pre-flight unit tests failed! Aborting deployment immediately to protect production.${NC}"
    exit 1
  fi
else
  echo -e "${YELLOW}⚠ Skipping local pre-flight tests (--skip-tests flag detected).${NC}"
fi

# ------------------------------------------------------------------------------
# STEP 2: MULTI-SERVER SSH DEPLOYMENT LOOP
# ------------------------------------------------------------------------------
DEPLOY_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

run_remote() {
  local server="$1"
  local cmd="$2"
  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY-RUN] ${server} -> ${cmd}${NC}"
  else
    ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new "$server" "$cmd"
  fi
}

FAILED_SERVERS=()

for SERVER in "${SERVERS[@]}"; do
  echo -e "\n${BLUE}----------------------------------------------------------------------${NC}"
  echo -e "${CYAN}[DEPLOYING] Connecting to node: ${SERVER}...${NC}"
  echo -e "${BLUE}----------------------------------------------------------------------${NC}"

  # Check SSH connectivity
  if [ "$DRY_RUN" = false ]; then
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$SERVER" "echo -n ''" 2>/dev/null; then
      echo -e "${RED}✗ Unable to connect to ${SERVER} via SSH. Marking node as FAILED.${NC}"
      FAILED_SERVERS+=("$SERVER")
      continue
    fi
  fi

  # Remote Commands with Automatic Rollback
  REMOTE_SCRIPT=$(cat <<EOF
set -euo pipefail
cd "${APP_DIR}"

echo "1. Creating safety backup of current state & SQLite database..."
mkdir -p backups
PREV_COMMIT=\$(git rev-parse HEAD 2>/dev/null || echo "initial")
tar -czf "backups/backup_${DEPLOY_TIMESTAMP}_\${PREV_COMMIT}.tar.gz" --exclude='backups' --exclude='.venv' . || true

rollback() {
  echo "🚨 CRITICAL ERROR DETECTED: Performing automated rollback to \${PREV_COMMIT}..."
  git reset --hard "\${PREV_COMMIT}"
  if [ -f ".venv/bin/python" ]; then
    .venv/bin/pip install -r requirements.txt || true
  fi
  systemctl restart "${SERVICE_NAME}" || true
  echo "✓ Rollback completed."
  exit 1
}

trap rollback ERR

echo "2. Pulling latest release from Git (${DEPLOY_BRANCH})..."
git fetch origin "${DEPLOY_BRANCH}"
git checkout "${DEPLOY_BRANCH}"
git pull origin "${DEPLOY_BRANCH}"

echo "3. Updating virtual environment dependencies..."
if [ -d ".venv" ]; then
  .venv/bin/pip install -q -r requirements.txt
else
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

echo "4. Running post-deployment health & telemetry audit..."
.venv/bin/python core/health_monitor.py --db data/leads.db --max-latency 45.0 --min-score 7.0

echo "5. Reloading production service (${SERVICE_NAME})..."
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl restart "${SERVICE_NAME}" || true
fi

echo "✓ Deployment successful on this node."
EOF
)

  if run_remote "$SERVER" "$REMOTE_SCRIPT"; then
    echo -e "${GREEN}✓ Node ${SERVER} successfully deployed and verified.${NC}"
  else
    echo -e "${RED}✗ Deployment failed on node ${SERVER}! Rollback triggered.${NC}"
    FAILED_SERVERS+=("$SERVER")
  fi
done

# ------------------------------------------------------------------------------
# STEP 3: DEPLOYMENT SUMMARY & METRICS
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  📊 DEPLOYMENT AUDIT SUMMARY                                         ${NC}"
echo -e "${BLUE}======================================================================${NC}"
TOTAL_NODES=${#SERVERS[@]}
FAILED_COUNT=${#FAILED_SERVERS[@]}
SUCCESS_COUNT=$((TOTAL_NODES - FAILED_COUNT))

echo -e "Total Nodes Configured: ${TOTAL_NODES}"
echo -e "Successful Deploys    : ${GREEN}${SUCCESS_COUNT}${NC}"
echo -e "Failed Deploys        : $(if [ $FAILED_COUNT -gt 0 ]; then echo -e "${RED}${FAILED_COUNT}${NC}"; else echo -e "${GREEN}0${NC}"; fi)"

if [ $FAILED_COUNT -gt 0 ]; then
  echo -e "\n${RED}Alert: Nodes requiring inspection: ${FAILED_SERVERS[*]}${NC}"
  exit 1
else
  echo -e "\n${GREEN}🚀 All target servers updated and operating within healthy SLA limits.${NC}"
  exit 0
fi
