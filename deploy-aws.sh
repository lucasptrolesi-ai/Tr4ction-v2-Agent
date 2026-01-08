#!/bin/bash
# ==========================================================================
# AWS EC2 DEPLOYMENT SCRIPT - TR4CTION AGENT V2
# ==========================================================================
# Usage: bash deploy-aws.sh
# Prerequisites: EC2 running Ubuntu 22.04, Docker/Docker Compose installed
# ==========================================================================

set -e

echo "🚀 TR4CTION Agent V2 - AWS EC2 Deployment Script"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/tr4ction"
DOMAIN="api.tr4ction.ai"
EMAIL="admin@tr4ction.ai"
BRANCH="${1:-main}"

# Functions
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ========== STEP 1: Verify Prerequisites ==========
log_info "STEP 1: Verifying prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
fi
log_success "Docker found"

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed"
fi
log_success "Docker Compose found"

# ========== STEP 2: Clone/Update Repository ==========
log_info "STEP 2: Cloning/updating repository..."

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$(dirname $PROJECT_DIR)"
    cd "$(dirname $PROJECT_DIR)"
    git clone https://github.com/tr4ction/tr4ction-agent-v2.git tr4ction
    log_success "Repository cloned"
else
    cd "$PROJECT_DIR"
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
    log_success "Repository updated"
fi

cd "$PROJECT_DIR"

# ========== STEP 3: Create Environment File ==========
log_info "STEP 3: Creating environment configuration..."

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    
    # Generate JWT Secret
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Update .env with values
    sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|g" backend/.env
    sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" backend/.env
    sed -i "s|DEBUG_MODE=.*|DEBUG_MODE=false|g" backend/.env
    
    log_success "Environment file created with generated JWT secret"
    log_info "⚠️  Please review backend/.env and update any additional secrets needed"
else
    log_success "Environment file already exists"
fi

# ========== STEP 4: Create Docker Resources ==========
log_info "STEP 4: Creating Docker volumes and network..."

# Create volumes
docker volume create tr4ction_chroma_data 2>/dev/null || true
docker volume create tr4ction_backend_data 2>/dev/null || true
docker volume create tr4ction_backend_logs 2>/dev/null || true
docker volume create tr4ction_nginx_logs 2>/dev/null || true
docker volume create tr4ction_certbot_conf 2>/dev/null || true
docker volume create tr4ction_certbot_www 2>/dev/null || true

# Create network
docker network create tr4ction_network 2>/dev/null || true

log_success "Volumes and network created"

# ========== STEP 5: Build and Start Services ==========
log_info "STEP 5: Building and starting services..."

docker compose down 2>/dev/null || true
docker compose build
docker compose up -d

log_success "Services started"

# ========== STEP 6: Wait for Services to be Healthy ==========
log_info "STEP 6: Waiting for services to be healthy..."

echo "Waiting for backend to be healthy..."
for i in {1..30}; do
    if docker compose ps backend | grep -q "healthy"; then
        log_success "Backend is healthy"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        log_error "Backend failed to become healthy"
    fi
done

# ========== STEP 7: Verify DNS ==========
log_info "STEP 7: Verifying DNS resolution..."

if ! dig +short $DOMAIN | grep -q .; then
    log_error "DNS not configured yet. Please configure: $DOMAIN → $(curl -s http://checkip.amazonaws.com)"
fi
log_success "DNS resolves correctly"

# ========== STEP 8: Generate SSL Certificate ==========
log_info "STEP 8: Generating SSL certificate with Let's Encrypt..."

docker compose exec -it certbot certbot certonly \
    --webroot -w /var/www/certbot \
    -d $DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive || log_error "SSL certificate generation failed"

log_success "SSL certificate generated"

# ========== STEP 9: Enable HTTPS Configuration ==========
log_info "STEP 9: Enabling HTTPS configuration..."

# Update docker-compose.yml to use production nginx config
sed -i "s|./nginx/nginx-dev.conf|./nginx/nginx.conf|g" docker-compose.yml

docker compose restart nginx

log_success "HTTPS configuration activated"

# ========== STEP 10: Validate Deployment ==========
log_info "STEP 10: Validating deployment..."

sleep 5

if curl -s https://$DOMAIN/health | grep -q "healthy"; then
    log_success "✅ DEPLOYMENT SUCCESSFUL"
    echo ""
    echo "🎉 API is running at: https://$DOMAIN"
    echo "🎉 Health Check: https://$DOMAIN/health"
else
    log_error "API health check failed"
fi

# ========== STEP 11: Display System Status ==========
log_info "STEP 11: System status..."

echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "📦 Volume Status:"
docker volume ls | grep tr4ction

echo ""
echo "🔒 SSL Certificate Info:"
docker compose exec -it certbot certbot certificates -d $DOMAIN 2>/dev/null || echo "Certificate not yet available"

echo ""
echo "📝 System Logs (last 10 lines):"
docker compose logs --tail=10

# ========== FINAL SUMMARY ==========
echo ""
echo "=================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "📌 Important Information:"
echo "  - API URL: https://$DOMAIN"
echo "  - Health Check: https://$DOMAIN/health"
echo "  - Frontend: https://tr4ction-v2-agent.vercel.app"
echo "  - Logs Location: View with 'docker compose logs -f backend'"
echo ""
echo "🔐 Security:"
echo "  - JWT Secret: $(grep JWT_SECRET_KEY backend/.env | cut -d'=' -f2 | cut -c1-10)..."
echo "  - Admin Account: admin@tr4ction.com (check password in backend/.env)"
echo "  - SSL Auto-Renewal: Certbot running"
echo ""
echo "📚 Documentation:"
echo "  - Status: DEPLOYMENT_STATUS.md"
echo "  - Quick Ref: DEPLOYMENT_QUICK_REFERENCE.md"
echo "  - Validation: DEPLOYMENT_VALIDATION_REPORT.md"
echo ""
echo "🚀 Next Steps:"
echo "  1. Verify backend data persistence"
echo "  2. Test API endpoints from frontend"
echo "  3. Configure monitoring/alerts"
echo "  4. Set up daily backups"
echo ""
echo "❓ Troubleshooting:"
echo "  - View logs: docker compose logs -f backend"
echo "  - Restart backend: docker compose restart backend"
echo "  - Reset database: docker compose exec backend python reset_db.py"
echo ""
echo "=================================================="

exit 0
