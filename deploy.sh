#!/bin/bash
# Script de deploy automático para Vercel
# Uso: bash deploy.sh "Mensagem de commit"

set -e

REPO="https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent.git"
COMMIT_MSG="${1:-Deploy automático $(date +'%d/%m/%Y %H:%M')}"

echo "🚀 =========================================="
echo "   DEPLOY - TR4CTION Agent para Vercel"
echo "=========================================="
echo ""

# Verificar se está no diretório correto
if [ ! -d ".git" ]; then
    echo "❌ Erro: Não estou no diretório raiz do projeto"
    exit 1
fi

echo "📊 Status atual:"
git status --short
echo ""

# Fazer add
echo "➕ Adicionando arquivos..."
git add .

# Fazer commit
echo "💾 Fazendo commit: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" || echo "⚠️  Nada para fazer commit"

# Fazer push
echo "📤 Fazendo push para GitHub..."
git push origin main

echo ""
echo "✅ =========================================="
echo "   DEPLOY ENVIADO PARA GITHUB!"
echo "=========================================="
echo ""
echo "🔗 GitHub: $REPO"
echo "🚀 Vercel Deploy: https://vercel.com/dashboard"
echo ""
echo "Status:"
echo "  • Frontend: Aguardando build no Vercel"
echo "  • Backend: Rodando em 54.144.92.71"
echo ""
