# 🚴 STRAVA COACH v9.4 — REFERÊNCIA RÁPIDA

## 📊 STATUS FINAL ✅

- ✅ Dashboard publicado em produção
- ✅ Automação rodando 3x/dia (09h, 15h, 22h BRT)
- ✅ Dados do Strava sincronizados
- ✅ GitHub Pages ativo

---

## 🌐 ACESSAR DASHBOARD

**URL:** `https://ncichelero.github.io/Strava-Coach/dashboard.html`

**Adicionar ao celular:**
- iPhone: Compartilhar → "Adicionar à Tela de Início"
- Android: 3 pontinhos → "Adicionar à tela inicial"

---

## 📁 ESTRUTURA DE ARQUIVOS

```
C:\Users\nicol\Desktop\Agente Ciclismo\
├── strava_coach.py           ← Busca dados do Strava
├── dashboard_generator.py    ← Gera dashboard.html
├── strava_auth.py            ← Regenera tokens (se expirar)
├── .env                       ← Credenciais (NÃO COMMITAR)
├── .gitignore                ← Protege .env
├── dashboard.html            ← Saída (gerado automaticamente)
├── index.html                ← Redirect (gerado)
├── .github/workflows/sync.yml ← Automação GitHub Actions
└── data/
    ├── treinos.json          ← Atividades do Strava
    ├── wellness.json         ← Dados Intervals.icu
    └── fitness.json          ← CTL/ATL/TSB
```

---

## 🔐 CREDENCIAIS (.env)

```
CLAUDE_API_KEY=sk-ant-api03-...
INTERVALS_API_KEY=2m92pnebq7b1oh685mmsg83da
STRAVA_CLIENT_ID=234497
STRAVA_CLIENT_SECRET=...
STRAVA_REFRESH_TOKEN=...
```

⚠️ **Nunca commitar .env** — está no .gitignore.

---

## ⏰ AUTOMAÇÃO (3x/dia)

| Hora BRT | Hora UTC | O que faz |
|---|---|---|
| 09:00 | 12:00 | Roda strava_coach.py + gera dashboard |
| 15:00 | 18:00 | Idem |
| 22:00 | 01:00 | Idem |

**Como disparar manual:**
1. https://github.com/NCichelero/Strava-Coach/actions
2. "Sync Strava Coach" → "Run workflow"

---

## 🔄 ROTINA LOCAL (Quando Precisar)

```powershell
cd "C:\Users\nicol\Desktop\Agente Ciclismo"
python strava_coach.py           # Busca Strava
python dashboard_generator.py    # Gera HTML
git add -A
git commit -m "Manual update"
git push
```

---

## 🔑 SE TOKEN EXPIRAR

```powershell
python strava_auth.py
```

1. Pede `STRAVA_CLIENT_SECRET`
2. Abre navegador para autorizar
3. Salva novo token no `.env`
4. Atualizar Secret no GitHub:
   - https://github.com/NCichelero/Strava-Coach/settings/secrets/actions
   - Update `STRAVA_REFRESH_TOKEN`

---

## 📊 DASHBOARD — O QUE TEM

**Cartões superiores:**
- CTL / ATL / TSB / FTP / W/kg
- VO2max (2 fórmulas): FC + Potência 5min
- Previsão FTP / Meta CTL / Alertas

**Abas:**
1. **Histórico** — Treinos últimas 4 semanas
   - Expandir: métricas detalhadas + laps
   - Filtro: Ciclismo/Academia/Outros
   - TSS semanal com cor (Ideal/Alta/Baixa)
   - Distribuição de zonas (polarização 80/20)

2. **Condicionamento** — CTL/ATL/TSB + Forecast 7 dias
   - Gráfico interativo
   - Toggle: CTL/ATL/TSB/TSS

3. **Próxima Semana** — Plano detalhado
   - Blocos de treino com watts/zonas
   - Suplementação automática por duração

---

## 🎯 DADOS CALCULADOS

- **VO2max (FC):** `15 × (FC_max/FC_repouso)`
- **VO2max (Potência):** `16.6 + (8.87 × W/kg 5min)` — últimas 2 semanas
- **Zonas FC:** Z1(115-129) | Z2(129-145) | Z3(145-161) | Z4(161-176) | Z5(176+)
- **TSS:** `duracao × (pot/FTP)² × 100/60`
- **CTL/ATL:** Exponential moving average (42d / 7d)

---

## 🐛 TROUBLESHOOTING

| Erro | Solução |
|---|---|
| Workflow falha | Ver detalhes em Actions → sync → Run Strava Coach |
| URL dá 404 | Pages pode estar desativado (settings/pages) |
| Dashboard vazio | Rodar `python strava_coach.py` localmente |
| Token expirado | Rodar `python strava_auth.py` |
| Conflito git | `git pull --rebase` + `git push` |

---

## 📞 REPOSITÓRIO

**GitHub:** https://github.com/NCichelero/Strava-Coach
**Branch:** main
**Workflows:** .github/workflows/sync.yml

---

## 🎯 PRÓXIMOS PASSOS (Se Modificar)

1. **Adicionar métrica nova?** → Editar `dashboard_generator.py`
2. **Mudar horário automático?** → Editar `.github/workflows/sync.yml` (cron)
3. **Atualizar zonas FC?** → Linha 19 em `dashboard_generator.py`
4. **Regenerar dashboard** → `python dashboard_generator.py`

**Sempre:** `git add -A` → `git commit` → `git push`

---

**Última atualização:** 19 de maio de 2026
**Versão:** v9.4 (Laps + Streams + VO2max duplo + Distribuição zonas + TSS semanal)
