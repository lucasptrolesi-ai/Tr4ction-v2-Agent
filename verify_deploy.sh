#!/bin/bash
# ==========================================================================
# VERIFY DEPLOYMENT - TR4CTION AGENT V2
# ==========================================================================
# Usage: bash verify_deploy.sh
# Validates that all services are running and healthy
# ==========================================================================

set -e

echo "🔍 TR4CTION Agent V2 - Deployment Verification"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOMAIN="${1:-api.tr4ction.ai}"
LOCALHOST="${2:-localhost}"

# Counter
PASS=0
FAIL=0
WARN=0

# Functions
test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
}

# ========== Test 1: Docker Running ==========
echo ""
echo -e "${BLUE}[1/15]${NC} Checking Docker daemon..."
if docker ps > /dev/null 2>&1; then
    test_pass "Docker is running"
else
    test_fail "Docker is not running"
    exit 1
fi

# ========== Test 2: Docker Compose ==========
echo -e "${BLUE}[2/15]${NC} Checking Docker Compose..."
if docker compose version > /dev/null 2>&1; then
    test_pass "Docker Compose is installed"
else
    test_fail "Docker Compose is not installed"
    exit 1
fi

# ========== Test 3: All Containers Running ==========
echo -e "${BLUE}[3/15]${NC} Checking container status..."
TOTAL_CONTAINERS=$(docker compose ps --format json | grep -c '"State":"running"' || true)
if [ "$TOTAL_CONTAINERS" -ge 4 ]; then
    test_pass "All containers running ($TOTAL_CONTAINERS)"
else
    test_warn "Only $TOTAL_CONTAINERS containers running (expected 4+)"
fi

# ========== Test 4: Backend Container ==========
echo -e "${BLUE}[4/15]${NC} Checking backend container..."
if docker compose ps | grep -q "backend.*Up.*healthy"; then
    test_pass "Backend container is HEALTHY"
else
    test_fail "Backend container is not healthy"
fi

# ========== Test 5: Nginx Container ==========
echo -e "${BLUE}[5/15]${NC} Checking nginx container..."
if docker compose ps | grep -q "nginx.*Up"; then
    test_pass "Nginx container is running"
else
    test_fail "Nginx container is not running"
fi

# ========== Test 6: ChromaDB Container ==========
echo -e "${BLUE}[6/15]${NC} Checking ChromaDB container..."
if docker compose ps | grep -q "chroma.*Up"; then
    test_pass "ChromaDB container is running"
else
    test_warn "ChromaDB container is not running"
fi

# ========== Test 7: Health Check (Local) ==========
echo -e "${BLUE}[7/15]${NC} Testing health check (local)..."
HEALTH_RESPONSE=$(curl -s http://$LOCALHOST/health 2>/dev/null || echo "")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    test_pass "Health check responding: $HEALTH_RESPONSE"
else
    test_fail "Health check failed or not responding"
fi

# ========== Test 8: Backend Direct Connection ==========
echo -e "${BLUE}[8/15]${NC} Testing backend direct (port 8000)..."
if curl -s http://$LOCALHOST:8000/health 2>/dev/null | grep -q "healthy"; then
    test_fail "Backend exposed on port 8000 (security issue)"
else
    test_warn "Backend direct connection test skipped (expected in isolation)"
fi

# ========== Test 9: Database Initialization ==========
echo -e "${BLUE}[9/15]${NC} Checking database..."
if docker compose exec -T backend test -f /app/data/tr4ction.db 2>/dev/null; then
    test_pass "Database file exists"
else
    test_warn "Database file not found (may be initializing)"
fi

# ========== Test 10: Volumes Created ==========
echo -e "${BLUE}[10/15]${NC} Checking volumes..."
VOLUMES=$(docker volume ls --format "table {{.Name}}" | grep -c "tr4ction_" || true)
if [ "$VOLUMES" -ge 4 ]; then
    test_pass "All volumes present ($VOLUMES found)"
else
    test_fail "Missing volumes (found $VOLUMES, expected 6)"
fi

# ========== Test 11: Network Created ==========
echo -e "${BLUE}[11/15]${NC} Checking network..."
if docker network ls | grep -q "tr4ction_network"; then
    test_pass "tr4ction_network exists"
else
    test_fail "tr4ction_network not found"
fi

# ========== Test 12: Environment File ==========
echo -e "${BLUE}[12/15]${NC} Checking environment configuration..."
if [ -f "backend/.env" ]; then
    test_pass "Environment file exists"
    if grep -q "ENVIRONMENT=production" backend/.env; then
        test_pass "Production mode configured"
    else
        test_warn "Not configured for production"
    fi
else
    test_fail "Environment file not found"
fi

# ========== Test 13: Logs Available ==========
echo -e "${BLUE}[13/15]${NC} Checking logs..."
if docker compose logs backend 2>&1 | grep -q "Application startup complete"; then
    test_pass "Backend startup logs found"
else
    test_warn "Backend startup sequence not complete"
fi

# ========== Test 14: No Critical Errors ==========
echo -e "${BLUE}[14/15]${NC} Checking for critical errors..."
ERRORS=$(docker compose logs 2>&1 | grep -i "error\|exception\|failed" | wc -l || true)
if [ "$ERRORS" -eq 0 ]; then
    test_pass "No critical errors in logs"
else
    test_warn "Found $ERRORS error messages in logs"
fi

# ========== Test 15: Production Ready Check ==========
echo -e "${BLUE}[15/15]${NC} Production readiness..."
if [ "$FAIL" -eq 0 ]; then
    test_pass "System is production ready"
else
    test_warn "System has $FAIL failures - not production ready"
fi

# ========== Summary ==========
echo ""
echo "=============================================="
echo -e "${BLUE}📊 VERIFICATION SUMMARY${NC}"
echo "=============================================="
echo -e "  ${GREEN}Passed:  $PASS${NC}"
echo -e "  ${YELLOW}Warnings: $WARN${NC}"
echo -e "  ${RED}Failed:  $FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT VERIFICATION PASSED${NC}"
    echo ""
    echo "📝 Status Details:"
    docker compose ps
    echo ""
    echo "📊 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" 2>/dev/null || echo "  (Stats not available)"
    echo ""
    echo "🔗 Access Points:"
    echo "  - API: http://$LOCALHOST"
    echo "  - Health: http://$LOCALHOST/health"
    [ "$DOMAIN" != "$LOCALHOST" ] && echo "  - Production: https://$DOMAIN"
    echo ""
else
    echo -e "${RED}❌ DEPLOYMENT VERIFICATION FAILED${NC}"
    echo ""
    echo "Failed checks: $FAIL"
    echo "Review logs with: docker compose logs -f"
fi

echo ""
echo "=============================================="

exit $FAIL
