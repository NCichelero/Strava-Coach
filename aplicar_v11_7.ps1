# ════════════════════════════════════════════════════════════════════════
# 🚀 PATCH AUTOMÁTICO v11.7 - Strava Coach
# Aplica todas as mudanças no dashboard_generator.py automaticamente
# ════════════════════════════════════════════════════════════════════════

$arquivo = "dashboard_generator.py"

if (-not (Test-Path $arquivo)) {
    Write-Host "❌ Arquivo $arquivo não encontrado" -ForegroundColor Red
    exit
}

Write-Host "🔧 Aplicando patch v11.7..." -ForegroundColor Cyan

# Backup
Copy-Item $arquivo "$arquivo.backup" -Force
Write-Host "✅ Backup criado: $arquivo.backup" -ForegroundColor Green

# Ler arquivo
$conteudo = Get-Content $arquivo -Raw -Encoding UTF8

# ─── PATCH 1: Imports ──────────────────────────────────────────────────
if ($conteudo -notmatch "from analytics import") {
    $conteudo = $conteudo -replace "(import statistics)", @"
`$1

# v11.7: Analytics
from analytics import gerar_analytics_completo
from dashboard_cards_lite import build_aba_analytics
"@
    Write-Host "✅ Imports adicionados" -ForegroundColor Green
}

# ─── PATCH 2: load_data return ──────────────────────────────────────────
if ($conteudo -notmatch "analytics_data = gerar_analytics_completo") {
    $conteudo = $conteudo -replace "(\s+)return treinos, wellness, fitness, estado(\s*\n)", @"
`$1
`$1# v11.7: Gerar analytics
`$1print("📊 Gerando analytics...")
`$1analytics_data = gerar_analytics_completo()
`$1return treinos, wellness, fitness, estado, analytics_data`$2
"@
    Write-Host "✅ load_data() modificado" -ForegroundColor Green
}

# ─── PATCH 3: main() carregar dados ─────────────────────────────────────
$conteudo = $conteudo -replace "treinos, wellness, fitness, estado = load_data\(\)", "treinos, wellness, fitness, estado, analytics_data = load_data()"
Write-Host "✅ main() atualizado" -ForegroundColor Green

# ─── PATCH 4: build_dashboard call ──────────────────────────────────────
$conteudo = $conteudo -replace "html = build_dashboard\(treinos, wellness, fitness, estado\)", "html = build_dashboard(treinos, wellness, fitness, estado, analytics_data)"
Write-Host "✅ build_dashboard call atualizado" -ForegroundColor Green

# ─── PATCH 5: build_dashboard assinatura ────────────────────────────────
$conteudo = $conteudo -replace "def build_dashboard\(treinos, wellness, fitness, estado\):", "def build_dashboard(treinos, wellness, fitness, estado, analytics_data={}):"
Write-Host "✅ Assinatura build_dashboard atualizada" -ForegroundColor Green

# ─── PATCH 6: Botão aba Analytics ───────────────────────────────────────
if ($conteudo -notmatch 'data-tab="analytics"') {
    $conteudo = $conteudo -replace '(<button class="tab" data-tab="condicionamento">📈 Condicionamento</button>)', @"
`$1
<button class="tab" data-tab="analytics">📊 Analytics</button>
"@
    Write-Host "✅ Botão aba Analytics adicionado" -ForegroundColor Green
}

# ─── PATCH 7: Div da aba Analytics ──────────────────────────────────────
if ($conteudo -notmatch '<div id="analytics"') {
    $conteudo = $conteudo -replace '(<div id="condicionamento" class="tab-content">\{aba_cond\}</div>)', @"
`$1
<div id="analytics" class="tab-content">{build_aba_analytics(analytics_data)}</div>
"@
    Write-Host "✅ Div aba Analytics adicionada" -ForegroundColor Green
}

# ─── PATCH 8: Versão ────────────────────────────────────────────────────
$conteudo = $conteudo -replace "Strava Coach v10\.\d+", "Strava Coach v11.7"
$conteudo = $conteudo -replace "Dashboard Generator v10\.\d+", "Dashboard Generator v11.7"
Write-Host "✅ Versão atualizada para v11.7" -ForegroundColor Green

# Salvar
$conteudo | Out-File -FilePath $arquivo -Encoding UTF8 -NoNewline
Write-Host "`n✅ ARQUIVO ATUALIZADO!" -ForegroundColor Cyan
Write-Host "`n🧪 Testando..." -ForegroundColor Yellow

# Testar
python analytics.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ analytics.py OK" -ForegroundColor Green
    python dashboard_generator.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 SUCESSO!" -ForegroundColor Green
        Write-Host "Abra dashboard.html no navegador" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Erro no dashboard_generator.py" -ForegroundColor Red
        Write-Host "Restaurando backup..." -ForegroundColor Yellow
        Copy-Item "$arquivo.backup" $arquivo -Force
    }
} else {
    Write-Host "❌ Erro no analytics.py" -ForegroundColor Red
}
