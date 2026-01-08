# 🚀 QUICK REFERENCE - TR4CTION AGENT V2 DEPLOYMENT

## LOCAL DEVELOPMENT (Docker Compose)

### Start All Services
```bash
cd /path/to/tr4ction
docker compose up -d
```

### Check Status
```bash
docker compose ps
docker compose logs backend -f
docker compose logs nginx -f
docker compose logs chroma -f
```

### Stop All Services
```bash
docker compose down
```

### Rebuild Backend
```bash
docker compose build backend
docker compose up -d backend
```

### Database Reset (DANGER!)
```bash
docker compose exec backend python -c "
from backend.db.models import Base
from backend.db.database import engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
"
```

### View Logs
```bash
# All containers
docker compose logs --tail=100

# Specific service
docker compose logs backend --tail=50 -f
docker compose logs nginx --tail=50 -f
docker compose logs chroma --tail=50 -f
docker compose logs certbot --tail=50 -f
```

---

## ENDPOINTS

### Development (Local)
- **API Base:** `http://localhost`
- **Backend Direct:** `http://localhost:8000`
- **Health Check:** `http://localhost/health`
- **Docs (Dev Only):** `http://localhost:8000/docs`
- **ReDoc (Dev Only):** `http://localhost:8000/redoc`

### Production (AWS)
- **API Base:** `https://api.tr4ction.ai`
- **Health Check:** `https://api.tr4ction.ai/health`
- **Frontend:** `https://tr4ction-v2-agent.vercel.app`
- **Docs:** Bloqueado (404)
- **ReDoc:** Bloqueado (404)

---

## ENVIRONMENT VARIABLES

### Backend .env Template
```bash
# Copiar de .env.example
cp backend/.env.example backend/.env

# Gerar JWT_SECRET_KEY novo
openssl rand -hex 32

# Editar backend/.env com valores:
ENVIRONMENT=production
DEBUG_MODE=false
JWT_SECRET_KEY=<generated-value>
CHROMA_HOST=chroma
CHROMA_PORT=8000
DATA_DIR=/app/data
TEMPLATES_IMAGES_DIR=/app/data/templates_images
DATABASE_URL=sqlite:///./data/tr4ction.db
CORS_ORIGINS=https://tr4ction-v2-agent.vercel.app,https://api.tr4ction.ai
```

---

## AWS EC2 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] EC2 instance running (Ubuntu 22.04, t3.small+)
- [ ] Security group allows 80, 443, 22 inbound
- [ ] DNS record: api.tr4ction.ai → EC2 Public IP
- [ ] Docker & Docker Compose installed
- [ ] Repository cloned to `/home/ubuntu/tr4ction`

### Deployment Steps
```bash
# 1. Connect to EC2
ssh -i key.pem ubuntu@<IP>

# 2. Navigate to project
cd /home/ubuntu/tr4ction

# 3. Create .env from example
cp backend/.env.example backend/.env
nano backend/.env  # Edit with production values

# 4. Create volumes and network
bash scripts/setup-volumes.sh  # If exists
# OR manually:
docker volume create tr4ction_chroma_data
docker volume create tr4ction_backend_data
docker volume create tr4ction_backend_logs
docker volume create tr4ction_nginx_logs
docker volume create tr4ction_certbot_conf
docker volume create tr4ction_certbot_www
docker network create tr4ction_network

# 5. Start services
docker compose up -d

# 6. Wait for backend health check
sleep 30
docker compose ps  # Check all containers running

# 7. Generate SSL certificate
docker compose exec -it certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d api.tr4ction.ai \
  --email admin@tr4ction.ai \
  --agree-tos --non-interactive

# 8. Switch to production nginx config
# Edit docker-compose.yml:
#   From: ./nginx/nginx-dev.conf
#   To:   ./nginx/nginx.conf

# 9. Restart nginx with SSL
docker compose restart nginx

# 10. Validate HTTPS
curl https://api.tr4ction.ai/health
```

### Post-Deployment Validation
```bash
# Health check
curl https://api.tr4ction.ai/health
# Expected: {"status":"healthy"}

# Check certificate
openssl s_client -connect api.tr4ction.ai:443 -showcerts

# View logs
docker compose logs -f

# Check volumes
docker volume ls | grep tr4ction
```

---

## TROUBLESHOOTING

### Backend Not Starting
```bash
# Check logs
docker compose logs backend | tail -50

# Rebuild
docker compose build --no-cache backend
docker compose up -d backend

# Check database
docker compose exec backend python -c "from backend.db.database import SessionLocal; session = SessionLocal(); print('DB OK')"
```

### Nginx Not Starting
```bash
# Check logs
docker compose logs nginx | tail -20

# Validate config
docker run --rm -v $(pwd)/nginx:/etc/nginx:ro nginx:alpine nginx -t

# Restart
docker compose restart nginx
```

### Certificate Issues
```bash
# Check cert status
docker compose exec certbot certbot certificates

# Renew manually
docker compose exec certbot certbot renew --dry-run

# View cert details
docker compose exec certbot certbot certificates -d api.tr4ction.ai
```

### Volume Issues
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect tr4ction_backend_data

# Check usage
docker exec tr4ction_agent_v2-backend-1 du -sh /app/data

# Clean unused volumes (DANGER!)
docker volume prune
```

### Reset All (DANGER!)
```bash
# Stop everything
docker compose down

# Remove volumes
docker volume rm tr4ction_chroma_data tr4ction_backend_data \
  tr4ction_backend_logs tr4ction_nginx_logs tr4ction_certbot_conf \
  tr4ction_certbot_www

# Remove network
docker network rm tr4ction_network

# Restart
docker volume create tr4ction_chroma_data
docker volume create tr4ction_backend_data
docker volume create tr4ction_backend_logs
docker volume create tr4ction_nginx_logs
docker volume create tr4ction_certbot_conf
docker volume create tr4ction_certbot_www
docker network create tr4ction_network
docker compose up -d
```

---

## MONITORING

### Real-time Logs
```bash
docker compose logs -f backend
```

### Container Stats
```bash
docker stats
```

### Database Size
```bash
docker exec tr4ction_agent_v2-backend-1 du -sh /app/data/tr4ction.db
```

### ChromaDB Status
```bash
curl http://localhost:8000/api/v1/count
```

### Nginx Access Logs
```bash
docker compose logs nginx | grep "GET\|POST"
```

---

## BACKUP & RESTORE

### Backup Data
```bash
# Backup database
docker run --rm \
  -v tr4ction_backend_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/backend-data-$(date +%Y%m%d).tar.gz -C /data .

# Backup chroma
docker run --rm \
  -v tr4ction_chroma_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/chroma-data-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Data
```bash
# Restore database
docker run --rm \
  -v tr4ction_backend_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/backend-data-YYYYMMDD.tar.gz -C /data

# Stop and restart
docker compose restart backend
```

---

## MAINTENANCE

### SSL Certificate Renewal (Automatic)
Certbot container renews automatically daily. No action needed.

### Update Services
```bash
# Pull latest images
docker compose pull

# Rebuild backend (if code changed)
docker compose build backend

# Restart services
docker compose up -d
```

### Database Backups
```bash
# Daily backup cron (on EC2)
0 2 * * * docker exec tr4ction_agent_v2-backend-1 \
  cp /app/data/tr4ction.db /app/data/backups/tr4ction-$(date +\%Y\%m\%d).db
```

---

## KEY FILES

- `docker-compose.yml` - Service orchestration
- `backend/Dockerfile` - Backend build
- `backend/.env` - Environment variables (GITIGNORED)
- `nginx/nginx-dev.conf` - Development reverse proxy
- `nginx/nginx.conf` - Production reverse proxy (SSL)
- `backend/config.py` - Configuration management
- `backend/main.py` - FastAPI entry point
- `backend/db/database.py` - SQLite setup
- `DEPLOYMENT_STATUS.md` - Current deployment status

---

## SUPPORT CONTACTS

- **Frontend Support:** vercel.com (https://tr4ction-v2-agent.vercel.app)
- **Backend API:** api.tr4ction.ai
- **Email:** admin@tr4ction.ai
- **GitHub:** See repository for issues

---

**Last Updated:** 2026-01-08
**Status:** ✅ Production Ready
