#!/bin/bash
# ======================================================
# TR4CTION Agent V2 - Backup Script
# ======================================================
# Este script faz backup do banco de dados e ChromaDB
# Uso: bash backup.sh
# Para agendar: crontab -e -> 0 2 * * * /path/to/backup.sh

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📦 =========================================="
echo "   TR4CTION Agent V2 - Backup"
echo "=========================================="
echo ""

# Configurações
BACKUP_DIR="${HOME}/backups/tr4ction"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATE=$(date +%Y%m%d-%H%M%S)
KEEP_DAYS=7

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}[INFO]${NC} Diretório de backup: $BACKUP_DIR"
echo -e "${BLUE}[INFO]${NC} Data/hora: $DATE"
echo ""

# ======================================================
# Backup do SQLite
# ======================================================
echo -e "${BLUE}[INFO]${NC} Fazendo backup do banco de dados SQLite..."

if [ -f "$BACKEND_DIR/tr4ction.db" ]; then
    cp "$BACKEND_DIR/tr4ction.db" "$BACKUP_DIR/tr4ction-${DATE}.db"
    
    # Verificar tamanho
    SIZE=$(du -h "$BACKUP_DIR/tr4ction-${DATE}.db" | cut -f1)
    echo -e "${GREEN}[OK]${NC} Backup SQLite criado: tr4ction-${DATE}.db ($SIZE)"
else
    echo -e "${YELLOW}[WARN]${NC} Arquivo tr4ction.db não encontrado"
fi

# ======================================================
# Backup do ChromaDB
# ======================================================
echo -e "${BLUE}[INFO]${NC} Fazendo backup do ChromaDB..."

if [ -d "$BACKEND_DIR/data/chroma_db" ]; then
    tar -czf "$BACKUP_DIR/chroma-${DATE}.tar.gz" -C "$BACKEND_DIR" data/chroma_db/ 2>/dev/null || true
    
    if [ -f "$BACKUP_DIR/chroma-${DATE}.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/chroma-${DATE}.tar.gz" | cut -f1)
        echo -e "${GREEN}[OK]${NC} Backup ChromaDB criado: chroma-${DATE}.tar.gz ($SIZE)"
    else
        echo -e "${YELLOW}[WARN]${NC} Falha ao criar backup do ChromaDB"
    fi
else
    echo -e "${YELLOW}[WARN]${NC} Diretório data/chroma_db não encontrado"
fi

# ======================================================
# Backup do .env (com segurança)
# ======================================================
echo -e "${BLUE}[INFO]${NC} Fazendo backup do .env..."

if [ -f "$BACKEND_DIR/.env" ]; then
    # Criar backup criptografado (opcional - requer gpg)
    if command -v gpg &> /dev/null; then
        echo -e "${YELLOW}[WARN]${NC} .env contém dados sensíveis!"
        echo -e "${BLUE}[INFO]${NC} Para backup seguro, use: gpg -c $BACKEND_DIR/.env"
    else
        # Backup simples (não recomendado para produção)
        cp "$BACKEND_DIR/.env" "$BACKUP_DIR/.env-${DATE}.backup"
        chmod 600 "$BACKUP_DIR/.env-${DATE}.backup"
        echo -e "${YELLOW}[WARN]${NC} .env copiado sem criptografia - proteja este arquivo!"
    fi
else
    echo -e "${YELLOW}[WARN]${NC} Arquivo .env não encontrado"
fi

# ======================================================
# Backup dos uploads (se existir)
# ======================================================
echo -e "${BLUE}[INFO]${NC} Fazendo backup de uploads..."

if [ -d "$BACKEND_DIR/data/uploads" ] && [ "$(ls -A $BACKEND_DIR/data/uploads)" ]; then
    tar -czf "$BACKUP_DIR/uploads-${DATE}.tar.gz" -C "$BACKEND_DIR" data/uploads/ 2>/dev/null || true
    
    if [ -f "$BACKUP_DIR/uploads-${DATE}.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/uploads-${DATE}.tar.gz" | cut -f1)
        echo -e "${GREEN}[OK]${NC} Backup uploads criado: uploads-${DATE}.tar.gz ($SIZE)"
    fi
else
    echo -e "${BLUE}[INFO]${NC} Nenhum upload para fazer backup"
fi

# ======================================================
# Backup do knowledge base
# ======================================================
echo -e "${BLUE}[INFO]${NC} Fazendo backup de knowledge base..."

if [ -d "$BACKEND_DIR/data/knowledge" ] && [ "$(ls -A $BACKEND_DIR/data/knowledge)" ]; then
    tar -czf "$BACKUP_DIR/knowledge-${DATE}.tar.gz" -C "$BACKEND_DIR" data/knowledge/ 2>/dev/null || true
    
    if [ -f "$BACKUP_DIR/knowledge-${DATE}.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/knowledge-${DATE}.tar.gz" | cut -f1)
        echo -e "${GREEN}[OK]${NC} Backup knowledge criado: knowledge-${DATE}.tar.gz ($SIZE)"
    fi
else
    echo -e "${BLUE}[INFO]${NC} Nenhum knowledge base para fazer backup"
fi

# ======================================================
# Limpeza de backups antigos
# ======================================================
echo ""
echo -e "${BLUE}[INFO]${NC} Limpando backups antigos (mais de $KEEP_DAYS dias)..."

# Contar backups antes da limpeza
OLD_COUNT=$(find "$BACKUP_DIR" -type f -mtime +$KEEP_DAYS | wc -l)

if [ "$OLD_COUNT" -gt 0 ]; then
    find "$BACKUP_DIR" -type f -mtime +$KEEP_DAYS -delete
    echo -e "${GREEN}[OK]${NC} $OLD_COUNT arquivo(s) antigo(s) removido(s)"
else
    echo -e "${BLUE}[INFO]${NC} Nenhum backup antigo para remover"
fi

# ======================================================
# Relatório Final
# ======================================================
echo ""
echo "=========================================="
echo -e "${GREEN}[OK]${NC} Backup concluído com sucesso!"
echo "=========================================="
echo ""
echo "📊 Resumo:"
echo "  • Data/Hora: $DATE"
echo "  • Localização: $BACKUP_DIR"
echo "  • Retenção: $KEEP_DAYS dias"
echo ""

# Listar backups criados
echo "📁 Backups criados:"
ls -lh "$BACKUP_DIR"/*-${DATE}.* 2>/dev/null | awk '{print "  • " $9 " (" $5 ")"}'

echo ""
echo "💡 Dica: Para restaurar:"
echo "  SQLite: cp $BACKUP_DIR/tr4ction-${DATE}.db $BACKEND_DIR/tr4ction.db"
echo "  ChromaDB: tar -xzf $BACKUP_DIR/chroma-${DATE}.tar.gz -C $BACKEND_DIR"
echo ""

# ======================================================
# Log do backup
# ======================================================
echo "$(date) - Backup concluído: $DATE" >> "$BACKUP_DIR/backup.log"
