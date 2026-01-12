#!/bin/bash
# ======================================================
# TR4CTION Agent V2 - Health Check Script
# ======================================================
# Este script verifica se o backend está rodando corretamente
# Uso: bash healthcheck.sh [HOST] [PORT]
# Exemplo: bash healthcheck.sh localhost 8000

HOST="${1:-localhost}"
PORT="${2:-8000}"
HEALTH_URL="http://${HOST}:${PORT}/health"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🏥 =========================================="
echo "   TR4CTION Agent V2 - Health Check"
echo "=========================================="
echo ""
echo "Testando: $HEALTH_URL"
echo ""

# Verificar se curl está instalado
if ! command -v curl &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} curl não está instalado!"
    echo "Instale com: sudo apt install curl -y"
    exit 1
fi

# Fazer requisição com timeout
RESPONSE=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 10 "$HEALTH_URL" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "HTTP Status Code: $HTTP_CODE"
echo "Response Body: $BODY"
echo ""

# Verificar resultado
if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q '"status".*"ok"'; then
        echo -e "${GREEN}✅ [OK]${NC} Backend está rodando corretamente!"
        echo ""
        echo "📊 Endpoints disponíveis:"
        echo "  • API Docs: http://${HOST}:${PORT}/docs"
        echo "  • Health: http://${HOST}:${PORT}/health"
        echo "  • Root: http://${HOST}:${PORT}/"
        echo ""
        exit 0
    else
        echo -e "${YELLOW}[WARN]${NC} Backend respondeu, mas status não é 'ok'"
        echo "Response: $BODY"
        exit 1
    fi
elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    echo -e "${RED}❌ [ERROR]${NC} Não foi possível conectar ao backend!"
    echo ""
    echo "Possíveis causas:"
    echo "  1. Backend não está rodando"
    echo "  2. Porta $PORT bloqueada por firewall"
    echo "  3. Host $HOST incorreto"
    echo ""
    echo "Soluções:"
    echo "  • Iniciar backend: bash deploy-ec2.sh"
    echo "  • Verificar processo: lsof -i :$PORT"
    echo "  • Verificar logs: tail -f logs/backend.log"
    exit 1
else
    echo -e "${RED}❌ [ERROR]${NC} Backend retornou status HTTP $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi
