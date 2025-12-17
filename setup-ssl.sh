#!/bin/bash
# =====================================================
#   SCRIPT DE CONFIGURAÇÃO SSL - TR4CTION
#   Execute na EC2 para configurar HTTPS
# =====================================================

set -e

DOMAIN="54.144.92.71.sslip.io"
EMAIL="admin@tr4ction.com"  # Altere para seu email

echo "=========================================="
echo "  TR4CTION - Configuração SSL"
echo "=========================================="

cd /home/ubuntu/tr4ction

# Passo 1: Usar config temporária para certbot
echo "[1/5] Configurando Nginx para Certbot..."
cp nginx/nginx-certbot.conf nginx/nginx.conf.backup
docker compose stop nginx 2>/dev/null || true
docker compose up -d nginx

# Aguardar nginx subir
sleep 5

# Passo 2: Gerar certificado
echo "[2/5] Gerando certificado SSL..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Passo 3: Verificar se certificado foi criado
if [ ! -f "/home/ubuntu/tr4ction/certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "ERRO: Certificado não foi criado!"
    exit 1
fi

echo "[3/5] Certificado criado com sucesso!"

# Passo 4: Restaurar nginx.conf com HTTPS
echo "[4/5] Ativando configuração HTTPS..."
mv nginx/nginx.conf.backup nginx/nginx-certbot.conf

# Passo 5: Reiniciar nginx com SSL
echo "[5/5] Reiniciando Nginx com SSL..."
docker compose restart nginx

echo ""
echo "=========================================="
echo "  ✅ SSL CONFIGURADO COM SUCESSO!"
echo "=========================================="
echo ""
echo "  Backend HTTPS: https://$DOMAIN"
echo "  Health Check:  https://$DOMAIN/health"
echo ""
echo "  Próximo passo:"
echo "  Atualize NEXT_PUBLIC_API_URL na Vercel para:"
echo "  https://$DOMAIN"
echo ""
