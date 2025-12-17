# Script para limpar e consolidar instâncias duplicadas de ChromaDB no Windows

Write-Host "[CLEANUP] Limpando instâncias de ChromaDB duplicadas..." -ForegroundColor Cyan
Write-Host ""

# Definir caminhos
$projectRoot = Get-Location
$mainChromaDb = Join-Path $projectRoot "backend\data\chroma_db"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $projectRoot "backups\chroma_backups_$timestamp"

Write-Host "[OK] Caminho principal de ChromaDB: $mainChromaDb" -ForegroundColor Green
Write-Host ""

# Criar backup
Write-Host "[BACKUP] Criando backup das instâncias existentes..." -ForegroundColor Yellow
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

$dirsToBackup = @(
    @{ path = ".\chroma_db"; name = "chroma_db_root" },
    @{ path = ".\backend\chroma_data"; name = "chroma_data" },
    @{ path = ".\backend\http\chroma8000"; name = "chroma8000" }
)

foreach ($dir in $dirsToBackup) {
    if (Test-Path $dir.path) {
        Write-Host "  - Backupeando $($dir.path)..." -ForegroundColor Gray
        $destPath = Join-Path $backupDir $dir.name
        Copy-Item -Path $dir.path -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[OK] Backups criados em: $backupDir" -ForegroundColor Green
Write-Host ""

# Remover instâncias duplicadas
Write-Host "[CLEANUP] Removendo instâncias duplicadas..." -ForegroundColor Yellow

$dirsToRemove = @(
    @{ path = ".\chroma_db"; reason = "duplicate (root)" },
    @{ path = ".\backend\chroma_data"; reason = "duplicate" },
    @{ path = ".\backend\http\chroma8000"; reason = "duplicate" }
)

foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir.path) {
        Write-Host "  - Removendo $($dir.path) ($($dir.reason))" -ForegroundColor Gray
        Remove-Item -Path $dir.path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[OK] Limpeza concluída!" -ForegroundColor Green
Write-Host ""

# Verificar estrutura final
Write-Host "[INFO] Estrutura final de ChromaDB:" -ForegroundColor Cyan
if (Test-Path $mainChromaDb) {
    Write-Host "  [OK] ChromaDB consolidado em: $mainChromaDb" -ForegroundColor Green
    Get-ChildItem -Path $mainChromaDb -Recurse -Directory | Select-Object -First 5 | ForEach-Object {
        $relativePath = $_.FullName.Replace($projectRoot.Path, ".")
        Write-Host "    - $relativePath" -ForegroundColor Gray
    }
} else {
    Write-Host "  [WARN] Pasta não encontrada: $mainChromaDb" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[SUCCESS] Consolidação de ChromaDB concluída com sucesso!" -ForegroundColor Green
Write-Host "[INFO] Backups preservados em: $backupDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "[TODO] Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Testar a aplicação para verificar se tudo está funcionando" -ForegroundColor Gray
Write-Host "  2. Se houver problemas, restaurar de: $backupDir" -ForegroundColor Gray
Write-Host "  3. Deletar backup se tudo estiver OK" -ForegroundColor Gray
