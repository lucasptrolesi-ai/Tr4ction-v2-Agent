#!/bin/bash

# Script para limpar e consolidar instâncias duplicadas de ChromaDB

set -e

echo "🧹 Limpando instâncias de ChromaDB duplicadas..."
echo ""

# Definir caminho principal
MAIN_CHROMA_DB="./backend/data/chroma_db"
BACKUP_DIR="./backups/chroma_backups_$(date +%Y%m%d_%H%M%S)"

echo "✅ Caminho principal de ChromaDB: $MAIN_CHROMA_DB"
echo ""

# Criar backup
echo "📦 Criando backup das instâncias existentes..."
mkdir -p "$BACKUP_DIR"

# Backup das instâncias duplicadas
if [ -d "./chroma_db" ]; then
  echo "  - Backupeando ./chroma_db..."
  cp -r ./chroma_db "$BACKUP_DIR/chroma_db_root" 2>/dev/null || true
fi

if [ -d "./backend/chroma_data" ]; then
  echo "  - Backupeando ./backend/chroma_data..."
  cp -r ./backend/chroma_data "$BACKUP_DIR/chroma_data" 2>/dev/null || true
fi

if [ -d "./backend/http/chroma8000" ]; then
  echo "  - Backupeando ./backend/http/chroma8000..."
  cp -r ./backend/http/chroma8000 "$BACKUP_DIR/chroma8000" 2>/dev/null || true
fi

echo "✅ Backups criados em: $BACKUP_DIR"
echo ""

# Remover instâncias duplicadas
echo "🗑️  Removendo instâncias duplicadas..."

if [ -d "./chroma_db" ] && [ -d "$MAIN_CHROMA_DB" ]; then
  echo "  - Removendo ./chroma_db (duplicate)"
  rm -rf ./chroma_db
fi

if [ -d "./backend/chroma_data" ]; then
  echo "  - Removendo ./backend/chroma_data (duplicate)"
  rm -rf ./backend/chroma_data
fi

if [ -d "./backend/http/chroma8000" ]; then
  echo "  - Removendo ./backend/http/chroma8000 (duplicate)"
  rm -rf ./backend/http/chroma8000
fi

echo "✅ Limpeza concluída!"
echo ""

# Verificar estrutura final
echo "📁 Estrutura final de ChromaDB:"
find ./backend/data -name "*chroma*" -type d 2>/dev/null || echo "  (nenhuma pasta chroma encontrada)"

echo ""
echo "✨ Consolidação de ChromaDB concluída com sucesso!"
echo "📝 Backups preservados em: $BACKUP_DIR"
