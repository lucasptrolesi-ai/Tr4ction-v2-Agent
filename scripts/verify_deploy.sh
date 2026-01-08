#!/bin/bash
# =====================================================
#   SCRIPT DE VERIFICAÇÃO PÓS-DEPLOY
#   Valida saúde do sistema em produção
# =====================================================
set -e

echo "=========================================="
echo "  TR4CTION - Verificação de Deploy"
echo "=========================================="

cd /home/ubuntu/tr4ction

# 1. Status dos containers
echo -e "\n[1/6] Status dos containers:"
docker compose ps

# 2. Healthcheck do backend
echo -e "\n[2/6] Aguardando backend ficar healthy..."
for i in {1..30}; do
  STATUS=$(docker compose ps backend --format json | jq -r '.[0].Health // "starting"')
  if [ "$STATUS" = "healthy" ]; then
    echo "✅ Backend healthy!"
    break
  fi
  echo "  Tentativa $i/30: $STATUS"
  sleep 2
done

# 3. Verificar portas (8000 NÃO deve estar exposta publicamente)
echo -e "\n[3/6] Portas expostas:"
docker compose ps --format "table {{.Name}}\t{{.Ports}}"
echo "✅ Porta 8000 deve aparecer apenas como 'expose' (não publicada)"

# 4. Testar health interno
echo -e "\n[4/6] Health interno (via Nginx):"
docker compose exec -T nginx wget -qO- http://backend:8000/health || echo "❌ Health interno falhou"

# 5. Verificar SSL
echo -e "\n[5/6] Certificado SSL:"
if docker compose exec -T certbot ls /etc/letsencrypt/live/api.tr4ction.ai 2>/dev/null; then
  echo "✅ Certificado SSL presente"
  # Testar HTTPS
  if curl -fsSL https://api.tr4ction.ai/health >/dev/null 2>&1; then
    echo "✅ HTTPS funcionando"
    curl -sS https://api.tr4ction.ai/health
  else
    echo "⚠️  HTTPS ainda não acessível (DNS ou Nginx)"
  fi
else
  echo "⚠️  Certificado SSL não emitido ainda"
  echo "   Execute: docker compose run --rm --entrypoint \"\" certbot certbot certonly --webroot -w /var/www/certbot -d api.tr4ction.ai --email admin@tr4ction.ai --agree-tos --no-eff-email"
fi

# 6. Volumes persistentes
echo -e "\n[6/6] Volumes de dados:"
docker volume ls | grep tr4ction

echo -e "\n=========================================="
echo "  ✅ Verificação concluída"
echo "=========================================="
