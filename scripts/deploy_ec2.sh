#!/bin/bash
# =====================================================
#   DEPLOY EC2 - TR4CTION Agent V2 (PROD)
#   Requisitos: domínio api.tr4ction.ai apontado p/ EC2
# =====================================================
set -euo pipefail

DOMAIN="api.tr4ction.ai"
EMAIL="seu-email@tr4ction.ai"   # ajuste
PROJECT_DIR="$(pwd)"

step() { echo -e "\n[+] $1"; }

step "Checando Docker e Compose..."
if ! command -v docker >/dev/null 2>&1; then
  echo "Instalando Docker..."
  sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
  sudo systemctl enable docker --now
  sudo usermod -aG docker "$USER" || true
fi

docker --version

docker compose version || true

step "Preparando .env (backend/.env)"
if [ ! -f "backend/.env" ]; then
  cp backend/.env.example backend/.env
  sed -i "s|SECRET_KEY=COLOQUE_AQUI_UM_HEX_DE_64|SECRET_KEY=$(openssl rand -hex 32)|" backend/.env
fi

echo "Mostrando variáveis essenciais:"
grep -E '^(ENVIRONMENT|DEBUG_MODE|ALLOWED_ORIGINS|DATABASE_URL|CHROMA_HOST|CHROMA_PORT)' backend/.env || true

step "Validando docker-compose.yml"
docker compose config >/dev/null

step "Subindo backend e chroma"
docker compose up -d --build backend chroma

step "Aplicando configuração temporária do Nginx (certbot)"
if [ ! -f nginx/nginx.conf.prod ]; then
  cp nginx/nginx.conf nginx/nginx.conf.prod
fi
cp nginx/nginx-certbot.conf nginx/nginx.conf
docker compose up -d nginx

echo "Aguardando Nginx (porta 80) subir..."
sleep 5

echo "Emitindo certificado para ${DOMAIN}"
docker compose run --rm --entrypoint "" certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email

step "Restaurando configuração de produção do Nginx"
cp nginx/nginx.conf.prod nginx/nginx.conf
docker compose restart nginx

step "Verificando /health via HTTPS"
curl -fsSL "https://${DOMAIN}/health" || (echo "Health check falhou" && exit 1)

echo -e "\n✅ Deploy finalizado: https://${DOMAIN}"