================================================================================
TEMA 1: ROLO vs RUA (Indoor vs Outdoor)
================================================================================

PROBLEMA:
Alguns treinos são mais eficientes no rolo (maior precisão de watts) enquanto
outros podem ser feitos na rua. Precisamos recomendar qual ambiente é melhor.

SOLUÇÃO:
O dashboard_generator.py v10.2 agora recomenda automaticamente:

🏠 ROLO (Melhor para intervalados)
├─ Threshold (precisa manter watts exatos)
├─ VO2max (watts variáveis prejudicam adaptação)
├─ 30/30 Billat (recuperação ativa no rolo é fácil)
├─ Over-Under (mudanças rápidas de intensidade)
├─ Testes FTP (reprodutibilidade)
├─ Sprints (ambiente controlado)
└─ Razão: Sem interrupções (semáforos, curvas), watts precisos, watts normalizados

🚴 RUA (OK para endurance)
├─ Long rides Z2 (psicológico, paisagem, treino real)
├─ Endurance Z2 (variabilidade natural é benéfica)
├─ Recovery spins (sem exigência de precisão)
└─ Razão: Treino mais realista, mental, sem monotonia

↔️ AMBOS (indiferente)
├─ Qualquer coisa não listada acima
└─ Razão: Flexibilidade total

VISUALIZAÇÃO NO DASHBOARD:
Cada dia mostra um badge no treino:
┌─────────────────────────────────────────┐
│ 🎯 Próxima Semana                       │
├─────────────────────────────────────────┤
│ 🚴 Quarta | 05:30                       │
│ 🚀 VO2max 5x3min @ 115% FTP · 🏠 ROLO │
└─────────────────────────────────────────┘

PRIORIDADES:
1️⃣ Se planejou 🏠 ROLO mas está chovendo → use o rolo (não saia)
2️⃣ Se planejou 🚴 RUA mas precisa treinar → pode fazer no rolo (menos ideal mas funciona)
3️⃣ Se planejou ↔️ AMBOS → escolha baseado no tempo

LÓGICA DE RECOMENDAÇÃO (em dashboard_generator.py):

def recomendar_local(nome_treino):
    """Recomenda ROLO ou RUA baseado no tipo de treino"""
    nome_lower = nome_treino.lower()
    
    rolo_melhor = ['threshold', 'vo2max', '30/30', 'billat', 'rønnestad', 
                   'criss', 'over-under', 'interval', 'test', 'ftp', 'sprint']
    rua_ok = ['long', 'longo', 'endurance', 'z2', 'recovery', 'spin']
    
    if any(k in nome_lower for k in rolo_melhor):
        return 'ROLO', '🏠', '#3b82f6', 'Melhor no rolo (precisão controlada)'
    elif any(k in nome_lower for k in rua_ok):
        return 'RUA', '🚴', '#10b981', 'Rua OK (treino psicológico)'
    else:
        return 'AMBOS', '↔️', '#fbbf24', 'Rua ou rolo (indiferente)'

PRÓXIMOS PASSOS:
□ Adicionar histórico de onde foi feito (rolo/rua) em cada treino realizado
□ Calcular % de treinos rolo vs rua por bloco
□ Dashboard opcional mostrando performance rolo vs rua (watts, stabilidade)

================================================================================
TEMA 2: TIMEZONE GITHUB ACTIONS (UTC → BRT)
================================================================================

PROBLEMA:
GitHub Actions rode em UTC (Coordinated Universal Time), mas você está em
São Paulo (BRT = UTC-3). Os workflows estavam rodando em horários errados.

Exemplo:
- Seu comentário dizia "22:00 BRT"
- Mas o cron era "0 1 * * *" (01:00 UTC)
- 01:00 UTC = 22:00 BRT do DIA ANTERIOR
- Resultado: workflow rodava "de madrugada" (noturno)

CONVERSÃO BRT ↔ UTC:
Fórmula: UTC = BRT + 3 horas

Exemplos:
├─ 08:00 BRT → 08:00 + 3 = 11:00 UTC
├─ 14:00 BRT → 14:00 + 3 = 17:00 UTC
└─ 21:00 BRT → 21:00 + 3 = 00:00 UTC (próximo dia)

CRON FORMAT:
minute hour day_of_month month day_of_week

0 11 * * *  ← 11:00 UTC todo dia = 08:00 BRT
0 17 * * *  ← 17:00 UTC todo dia = 14:00 BRT
0 0  * * *  ← 00:00 UTC todo dia = 21:00 BRT (anterior)

ARQUIVOS ATUALIZADOS:
1. .github/workflows/sync.yml (novo arquivo com horários corretos)

Horários implementados:
├─ 08:00 BRT  (cron: 0 11) — início do dia, antes do trabalho
├─ 14:00 BRT  (cron: 0 17) — meio da tarde, horário de almoço/descanso
└─ 21:00 BRT  (cron: 0 0)  — noite, horário de planejamento

DASHBOARD STATUS:
O dashboard já exibe o timestamp em BRT:
"Atualizado em 20/05/2026 22:59 (BRT)"
Isso é feito pela função agora() que usa timezone UTC-3.

VERIFICAR SE ESTÁ CORRETO:
1. Vá ao GitHub → seu repo Strava-Coach
2. Clique em "Actions" no topo
3. Procure "Sync Strava Coach" na lista
4. Clique no workflow mais recente
5. Verifique:
   ✅ Hora de criação (deve ser ~08:00, ~14:00 ou ~21:00 BRT)
   ✅ Log mostra data/hora em UTC
   
Exemplo de log correto:
"2026-05-20 14:00:00 UTC" = 2026-05-20 11:00:00 BRT ← 08:00 BRT ✓

PRÓXIMAS EXECUÇÕES (estimadas):
├─ 2026-05-21 11:00 UTC = 2026-05-21 08:00 BRT ✓
├─ 2026-05-21 17:00 UTC = 2026-05-21 14:00 BRT ✓
└─ 2026-05-22 00:00 UTC = 2026-05-21 21:00 BRT ✓

TROUBLESHOOTING:
❌ "Workflow rodou mas dashboard não atualizou"
   → Verificar STRAVA_REFRESH_TOKEN expirou
   → Verificar CLAUDE_API_KEY está correto em GitHub Secrets
   
❌ "Workflow rodou de madrugada"
   → Seu sync.yml estava em UTC puro, sem conversão BRT
   → Atualize o arquivo para usar os novos crons

✅ "Quer testar agora?"
   → GitHub Actions → Sync Strava Coach → "Run workflow" (botão azul)
   → Isso roda imediatamente (ignora schedule)

SUMÁRIO DE MUDANÇAS v10.2:
┌────────────────────────────────────────────────────────┐
│ ✅ dashboard_generator.py                              │
│    ├─ Função recomendar_local(nome_treino)             │
│    ├─ Badge 🏠 ROLO / 🚴 RUA / ↔️ AMBOS em cada dia   │
│    └─ Semana Atual + Próxima Semana (ambas)           │
│                                                        │
│ ✅ sync.yml (.github/workflows/)                      │
│    ├─ Cron UTC correto: 11, 17, 0 (em vez de 12, 18, 1) │
│    ├─ Comentários explicam conversão BRT              │
│    └─ Workflow agora roda nos horários certos         │
│                                                        │
│ ✅ SESSAO_RESUMO.txt                                   │
│    └─ Documentação atualizada                         │
└────────────────────────────────────────────────────────┘

IMPLEMENTAÇÃO LOCAL:
Copie o novo sync.yml para seu repo:
C:\Users\nicol\Desktop\Agente Ciclismo\.github\workflows\sync.yml

Depois faça push:
git add .github/workflows/sync.yml
git commit -m "Fix: timezone UTC→BRT nos crons do GitHub Actions"
git push

Confirme no GitHub Actions que o próximo workflow roda no horário certo.

================================================================================
RESUMO FINAL
================================================================================

ROLO vs RUA:
• Dashboard recomenda automaticamente (🏠 vs 🚴 vs ↔️)
• Você tem liberdade de ignorar se necessário (p.ex., chuva)
• Historicamente não rastreia ainda, mas pode adicionar

Timezone GitHub:
• Workflows agora rodam em BRT certo (08:00, 14:00, 21:00)
• Arquivo sync.yml atualizado com crons corretos
• Dashboard sempre mostra timestamp em BRT

Próxima vez que workflow rodar, deve estar no horário certo!
