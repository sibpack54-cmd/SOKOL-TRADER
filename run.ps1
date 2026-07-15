# ═══════════════════════════════════════════════════════════════════════
# SOKOL-TRADER v0.6 — Запуск для Windows PowerShell
# ═══════════════════════════════════════════════════════════════════════

# 1. Кодировка UTF-8 (для PowerShell 5.1 и 7+)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 2. Путь к модулям
$env:PYTHONPATH = "$PSScriptRoot\src"

# 3. Заголовок (латиница, чтобы не ломалось)
Write-Host ""
Write-Host "SOKOL-TRADER v0.6 starting..." -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor DarkGray
Write-Host ""

# 4. Запуск
python src/scheduler.py

# 5. Пауза, если упало
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error! Exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
}