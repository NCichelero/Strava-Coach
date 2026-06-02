"""
🎨 DASHBOARD CARDS v11.8
Cards HTML para aba Analytics
NOVO v11.8:
  - build_card_distribuicao_vs_alvo  → zonas reais vs meta do bloco
  - build_card_ef_tendencia          → Efficiency Factor com sparkline
  - build_card_historico_ftp         → progressão FTP ao longo do tempo
  - build_card_ramp_rate             → ATL/CTL ratio com zona de segurança
  - build_card_tss_bloco             → TSS semana vs meta do bloco (420)
"""

import re

# ─── CARDS ORIGINAIS ─────────────────────────────────────────────────────────

def build_card_teste_ftp(teste_ftp_data):
    """Card: Teste FTP Automático"""
    if not teste_ftp_data:
        return ''

    recomendado = teste_ftp_data.get('recomendado', False)

    if not recomendado:
        return f'<div style="background:#1a2e1a;padding:16px;border-radius:8px;border:2px solid #10b981;"><h3 style="color:#10b981;margin:0;font-size:14px;">✅ FTP Atualizada</h3><div style="color:#10b981;font-size:12px;margin-top:4px;">FTP {teste_ftp_data["ftp_atual"]}W está atualizada.</div></div>'

    urgencia = teste_ftp_data.get('urgencia', 'baixa')
    diferenca = teste_ftp_data.get('diferenca', 0)
    pct = teste_ftp_data.get('pct_diferenca', 0)
    melhor_data = teste_ftp_data.get('melhor_data', '')
    dias = teste_ftp_data.get('dias_ate_teste', 0)
    protocolo = teste_ftp_data.get('protocolo', 'Ramp Test')

    cores = {'alta': '#f87171', 'média': '#facc15', 'baixa': '#60a5fa'}
    cor = cores.get(urgencia, '#60a5fa')
    label = {'alta': 'URGENTE', 'média': 'RECOMENDADO', 'baixa': 'SUGERIDO'}.get(urgencia)

    progresso = min(100, (abs(pct) / 10) * 100)

    return f'''<div style="background:linear-gradient(135deg,{cor}22,{cor}11);padding:16px;border-radius:8px;border:2px solid {cor};">
    <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
        <h3 style="color:{cor};margin:0;font-size:14px;">🧪 TESTE FTP {label}</h3>
        <span style="background:{cor};color:white;padding:4px 8px;border-radius:4px;font-size:10px;font-weight:bold;">+{abs(diferenca)}W ({pct:+.1f}%)</span>
    </div>
    <div style="background:#333;height:8px;border-radius:4px;overflow:hidden;margin-bottom:12px;"><div style="background:{cor};width:{progresso}%;height:100%;"></div></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div><div style="color:#888;font-size:10px;">FTP Atual</div><div style="color:#fff;font-size:18px;font-weight:bold;">{teste_ftp_data["ftp_atual"]}W</div></div>
        <div><div style="color:#888;font-size:10px;">FTP Estimada</div><div style="color:{cor};font-size:18px;font-weight:bold;">{teste_ftp_data["ftp_estimado"]}W</div></div>
    </div>
    <div style="background:{cor}11;border-left:3px solid {cor};padding:10px;border-radius:4px;">
        <div style="color:{cor};font-weight:bold;font-size:11px;">📅 MELHOR DATA</div>
        <div style="color:#fff;font-size:13px;font-weight:bold;margin-top:4px;">{melhor_data} <span style="color:#888;">({dias}d)</span></div>
        <div style="color:#ddd;font-size:10px;margin-top:2px;">TSB: {teste_ftp_data["melhor_tsb"]:+.1f} (ideal 5-15)</div>
    </div>
</div>'''


def build_card_power_curve(analytics):
    """Card: Power Curve"""
    if not analytics or 'power_curve' not in analytics:
        return ''

    pc = analytics['power_curve']
    picos = pc.get('picos', {})

    rows = ''
    for key, label in [('5s', '5s'), ('60s', '1min'), ('300s', '5min'), ('1200s', '20min'), ('3600s', '60min')]:
        val = picos.get(key, 0)
        if val > 0:
            rows += f'<tr><td style="padding:6px;color:#fff;font-size:11px;">{label}</td><td style="padding:6px;text-align:right;color:#fbbf24;font-weight:bold;">{val}W</td></tr>'

    return f'''<div style="background:#1a1a2e;padding:16px;border-radius:8px;border:1px solid #333;">
    <h3 style="color:#fbbf24;margin:0 0 12px 0;font-size:14px;">📈 Power Curve</h3>
    <table style="width:100%;border-collapse:collapse;font-size:11px;color:#ddd;">{rows}</table>
    <div style="margin-top:12px;padding:8px;background:#2e1a2e;border-radius:4px;color:#fbbf24;font-size:11px;">
        FTP Est: {pc.get("ftp_estimado")}W | +{pc.get("diferenca")}W ({pc.get("percentual_acima")}%)
    </div>
</div>'''


def build_card_decoupling(decoupling_dict):
    """Card: Aerobic Decoupling"""
    if not decoupling_dict:
        return ''

    valores = [d.get('decoupling_pct', 0) for d in decoupling_dict.values() if d.get('decoupling_pct')]
    if not valores:
        return ''

    media = sum(valores) / len(valores)

    if media < 5:
        cor, status = '#10b981', 'Excelente'
    elif media < 10:
        cor, status = '#facc15', 'Bom'
    else:
        cor, status = '#f87171', 'Atenção'

    return f'''<div style="background:#1a2e2e;padding:16px;border-radius:8px;border:1px solid #333;">
    <h3 style="color:#fbbf24;margin:0 0 12px 0;font-size:14px;">🫀 Aerobic Decoupling</h3>
    <div style="text-align:center;">
        <div style="color:{cor};font-size:32px;font-weight:bold;">{media:.1f}%</div>
        <div style="color:{cor};font-size:12px;font-weight:bold;">{status}</div>
        <div style="color:#888;font-size:10px;margin-top:8px;">Baseado em {len(valores)} treinos</div>
    </div>
</div>'''


def build_card_forecast(forecast_data):
    """Card: Fitness Forecast"""
    if not forecast_data:
        return ''

    maior_ctl = forecast_data.get('maior_ctl', {})
    melhor_tsb = forecast_data.get('melhor_tsb', {})

    return f'''<div style="background:#1a1e2e;padding:16px;border-radius:8px;border:1px solid #333;">
    <h3 style="color:#fbbf24;margin:0 0 12px 0;font-size:14px;">🔮 Forecast 28d</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div>
            <div style="color:#888;font-size:10px;">Maior CTL</div>
            <div style="color:#10b981;font-size:18px;font-weight:bold;">{maior_ctl.get("ctl", 0)}</div>
            <div style="color:#666;font-size:10px;">{maior_ctl.get("data", "")}</div>
        </div>
        <div>
            <div style="color:#888;font-size:10px;">Melhor TSB</div>
            <div style="color:#facc15;font-size:18px;font-weight:bold;">+{melhor_tsb.get("tsb", 0)}</div>
            <div style="color:#666;font-size:10px;">{melhor_tsb.get("data", "")}</div>
        </div>
    </div>
</div>'''


def build_card_rolo_rua(rolo_rua_data):
    """Card: Rolo vs Rua"""
    if not rolo_rua_data:
        return ''

    rolo_pct = rolo_rua_data.get('rolo_pct', 0)
    rua_pct = rolo_rua_data.get('rua_pct', 0)
    rolo = rolo_rua_data.get('rolo', {})
    rua = rolo_rua_data.get('rua', {})

    return f'''<div style="background:#2e1a2e;padding:16px;border-radius:8px;border:1px solid #333;">
    <h3 style="color:#fbbf24;margin:0 0 12px 0;font-size:14px;">🏠 Rolo vs 🚴 Rua</h3>
    <div style="display:flex;height:20px;border-radius:4px;overflow:hidden;margin-bottom:12px;background:#333;">
        <div style="background:#3b82f6;width:{rolo_pct}%;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:bold;">{rolo_pct}%</div>
        <div style="background:#10b981;width:{rua_pct}%;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:bold;">{rua_pct}%</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:11px;color:#ddd;">
        <div><div style="color:#3b82f6;font-weight:bold;">Rolo</div><div style="margin-top:4px;">{rolo.get("count", 0)} treinos</div></div>
        <div><div style="color:#10b981;font-weight:bold;">Rua</div><div style="margin-top:4px;">{rua.get("count", 0)} treinos</div></div>
    </div>
</div>'''


# ─── NOVOS CARDS v11.8 ───────────────────────────────────────────────────────

def build_card_distribuicao_vs_alvo(distrib, alvo_str=''):
    """
    Barras horizontais: zonas reais vs meta do bloco atual.
    distrib: retorno de calcular_distribuicao() do dashboard_generator
    alvo_str: ex. '85% Z1-Z2 | 15% Z3 | 0% Z4-Z5'
    """
    if not distrib:
        return ''

    pcts_real = distrib.get('pcts', {})

    # Parse alvo_str → {Z1: x, Z2: x, Z3: x, Z4: x, Z5: x}
    alvo = {'Z1': 0.0, 'Z2': 0.0, 'Z3': 0.0, 'Z4': 0.0, 'Z5': 0.0}
    if alvo_str:
        for parte in alvo_str.split('|'):
            parte = parte.strip()
            m = re.match(r'(\d+)%\s+(Z\d+(?:-Z\d+)?)', parte)
            if m:
                pct_val = float(m.group(1))
                zonas_raw = m.group(2).split('-')
                share = pct_val / len(zonas_raw)
                for z in zonas_raw:
                    if z in alvo:
                        alvo[z] = share

    cores_zona = {'Z1': '#6b7280', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}

    linhas = ''
    for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
        real = pcts_real.get(z, 0)
        meta = alvo.get(z, 0)
        cor = cores_zona[z]
        delta = real - meta
        delta_cor = '#10b981' if abs(delta) <= 5 else ('#facc15' if abs(delta) <= 15 else '#f87171')
        delta_str = f'{delta:+.0f}%'

        linhas += f'''
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:4px;">
                <span style="color:{cor};font-weight:700;">{z}</span>
                <span style="color:#888;">Meta: <b style="color:#ddd;">{meta:.0f}%</b> &nbsp;|&nbsp; Real: <b style="color:#fff;">{real:.0f}%</b> &nbsp;
                <span style="color:{delta_cor};font-weight:700;">{delta_str}</span></span>
            </div>
            <div style="position:relative;height:14px;background:#1a1a1a;border-radius:4px;overflow:visible;">
                <div style="position:absolute;top:0;left:0;height:100%;width:{min(real,100)}%;background:{cor};border-radius:4px;opacity:0.85;"></div>
                <!-- linha de meta -->
                <div style="position:absolute;top:-2px;bottom:-2px;left:{min(meta,100)}%;width:2px;background:#fff;border-radius:1px;opacity:0.7;"></div>
            </div>
        </div>'''

    return f'''<div style="background:#1a1a2e;padding:16px;border-radius:8px;border:1px solid #333;grid-column:span 2;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="color:#fbbf24;margin:0;font-size:14px;">🎯 Zonas Reais vs Meta do Bloco</h3>
        <span style="font-size:10px;color:#888;">▏ = meta &nbsp; barra = realizado</span>
    </div>
    {linhas}
    <div style="margin-top:8px;font-size:10px;color:{distrib.get('cor','#888')};">{distrib.get('modelo','')} — {distrib.get('descricao','')}</div>
</div>'''


def build_card_ef_tendencia(ef_data):
    """
    Efficiency Factor (Potência/FC) em treinos Z2 com sparkline SVG.
    Sobe = adaptação aeróbica acontecendo.
    """
    if not ef_data:
        return ''

    ef_atual = ef_data.get('ef_atual', 0)
    ef_media = ef_data.get('ef_media', 0)
    tendencia = ef_data.get('tendencia_pct', 0)
    qualidade = ef_data.get('qualidade', '—')
    cor = ef_data.get('cor', '#888')
    n = ef_data.get('n_treinos', 0)
    pontos = ef_data.get('pontos', [])

    tend_icone = '↗' if tendencia > 0.5 else ('↘' if tendencia < -0.5 else '→')
    tend_cor = '#10b981' if tendencia > 0.5 else ('#f87171' if tendencia < -0.5 else '#888')

    # SVG sparkline
    sparkline = ''
    if len(pontos) >= 3:
        vals = [p['ef'] for p in pontos]
        vmin, vmax = min(vals), max(vals)
        rng = vmax - vmin if vmax != vmin else 0.1
        w, h = 200, 40
        pts = []
        for i, v in enumerate(vals):
            x = int(i / (len(vals) - 1) * w)
            y = int(h - ((v - vmin) / rng) * (h - 4) - 2)
            pts.append(f'{x},{y}')
        polyline = ' '.join(pts)
        sparkline = f'''<svg viewBox="0 0 {w} {h}" style="width:100%;height:40px;overflow:visible;">
            <polyline points="{polyline}" fill="none" stroke="{cor}" stroke-width="2" stroke-linejoin="round"/>
            <circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" r="3" fill="{cor}"/>
        </svg>'''

    return f'''<div style="background:#1a2e1a;padding:16px;border-radius:8px;border:1px solid #333;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <h3 style="color:#fbbf24;margin:0;font-size:14px;">⚡ Efficiency Factor (EF)</h3>
        <span style="font-size:10px;color:#888;">{n} treinos Z2</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;">
        <div style="text-align:center;">
            <div style="color:#888;font-size:9px;text-transform:uppercase;">Atual</div>
            <div style="color:{cor};font-size:22px;font-weight:700;">{ef_atual:.3f}</div>
        </div>
        <div style="text-align:center;">
            <div style="color:#888;font-size:9px;text-transform:uppercase;">Média</div>
            <div style="color:#ddd;font-size:18px;font-weight:600;">{ef_media:.3f}</div>
        </div>
        <div style="text-align:center;">
            <div style="color:#888;font-size:9px;text-transform:uppercase;">Tendência</div>
            <div style="color:{tend_cor};font-size:18px;font-weight:700;">{tend_icone} {tendencia:+.1f}%</div>
        </div>
    </div>
    <div style="background:#0a0a0a;border-radius:4px;padding:8px;margin-bottom:8px;">{sparkline}</div>
    <div style="font-size:11px;color:{cor};font-weight:600;">{qualidade}
        <span style="color:#666;font-weight:400;margin-left:8px;">pot/FC em treinos Z2 &middot; ideal: 1.7–2.5</span>
    </div>
</div>'''


def build_card_historico_ftp(historico_ftp, ftp_atual=210, peso=75.6):
    """
    Gráfico de linha: progressão do FTP estimado mês a mês.
    """
    if not historico_ftp or len(historico_ftp) < 2:
        return ''

    labels = [p['mes'] for p in historico_ftp]
    valores = [p['ftp_est'] for p in historico_ftp]
    wkgs = [p['wkg'] for p in historico_ftp]

    # Ganho total
    ganho = valores[-1] - valores[0] if len(valores) >= 2 else 0
    ganho_cor = '#10b981' if ganho > 0 else ('#f87171' if ganho < 0 else '#888')
    ganho_str = f'{ganho:+d}W' if ganho != 0 else '='

    labels_js = str(labels).replace("'", '"')
    valores_js = str(valores)
    wkgs_js = str(wkgs)

    return f'''<div style="background:#1a1e2e;padding:16px;border-radius:8px;border:1px solid #333;grid-column:span 2;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h3 style="color:#fbbf24;margin:0;font-size:14px;">📈 Progressão FTP (estimado por pico 20min)</h3>
        <div style="text-align:right;font-size:11px;">
            <span style="color:#fff;font-weight:700;">{ftp_atual}W atual</span>
            <span style="margin-left:10px;color:{ganho_cor};font-weight:700;">{ganho_str} total</span>
        </div>
    </div>
    <canvas id="chart_ftp_hist" height="80"></canvas>
    <script>
    (function() {{
        var ctx = document.getElementById('chart_ftp_hist');
        if (!ctx) return;
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {labels_js},
                datasets: [
                    {{
                        label: 'FTP Estimado (W)',
                        data: {valores_js},
                        borderColor: '#fbbf24',
                        backgroundColor: 'rgba(251,191,36,0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: '#fbbf24',
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'W/kg',
                        data: {wkgs_js},
                        borderColor: '#ec4899',
                        backgroundColor: 'rgba(236,72,153,0.08)',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3,
                        borderDash: [4, 4],
                        yAxisID: 'y2'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{ legend: {{ labels: {{ color: '#ddd', font: {{ size: 10 }} }} }} }},
                scales: {{
                    y: {{
                        position: 'left',
                        ticks: {{ color: '#fbbf24', callback: v => v + 'W' }},
                        grid: {{ color: '#222' }}
                    }},
                    y2: {{
                        position: 'right',
                        ticks: {{ color: '#ec4899', callback: v => v.toFixed(2) }},
                        grid: {{ drawOnChartArea: false }}
                    }},
                    x: {{ ticks: {{ color: '#666' }}, grid: {{ color: '#1a1a1a' }} }}
                }}
            }}
        }});
    }})();
    </script>
</div>'''


def build_card_ramp_rate(ctl, atl):
    """
    Ramp Rate = ATL/CTL.
    < 1.0: destreinando | 1.0–1.3: carga saudável | 1.3–1.5: alto | > 1.5: risco overreaching
    """
    if ctl <= 0:
        return ''

    ratio = round(atl / ctl, 2)

    if ratio < 1.0:
        cor, status, desc = '#9ca3af', 'Destreinando', 'ATL < CTL — carga abaixo do nível de fitness'
    elif ratio <= 1.3:
        cor, status, desc = '#10b981', 'Carga Saudável', 'Zona ideal de progressão com segurança'
    elif ratio <= 1.5:
        cor, status, desc = '#facc15', 'Carga Alta', 'Monitore fadiga — limiar de overreaching próximo'
    else:
        cor, status, desc = '#f87171', '⚠️ Risco Overreaching', 'ATL/CTL > 1.5 — risco elevado de lesão ou burnout'

    # Barra: escala 0.5 → 1.8
    pos_pct = min(100, max(0, ((ratio - 0.5) / 1.3) * 100))
    marcas = [
        (int(((1.0 - 0.5) / 1.3) * 100), '1.0'),
        (int(((1.3 - 0.5) / 1.3) * 100), '1.3'),
        (int(((1.5 - 0.5) / 1.3) * 100), '1.5'),
    ]

    marcas_html = ''
    for mp, ml in marcas:
        marcas_html += f'<div style="position:absolute;left:{mp}%;top:-16px;font-size:9px;color:#666;transform:translateX(-50%);">{ml}</div>'
        marcas_html += f'<div style="position:absolute;left:{mp}%;top:0;bottom:0;width:1px;background:#444;"></div>'

    return f'''<div style="background:#1e1a2e;padding:16px;border-radius:8px;border:1px solid #333;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="color:#fbbf24;margin:0;font-size:14px;">📊 Ramp Rate (ATL/CTL)</h3>
        <span style="font-size:22px;font-weight:700;color:{cor};">{ratio}</span>
    </div>
    <div style="position:relative;margin:20px 0 10px;">
        {marcas_html}
        <div style="height:12px;background:linear-gradient(to right,#6b7280,#10b981,#facc15,#f87171);border-radius:6px;position:relative;">
            <div style="position:absolute;left:{pos_pct}%;top:-4px;width:4px;height:20px;background:#fff;border-radius:2px;transform:translateX(-50%);box-shadow:0 0 6px rgba(255,255,255,0.5);"></div>
        </div>
    </div>
    <div style="margin-top:10px;">
        <div style="color:{cor};font-weight:700;font-size:12px;">{status}</div>
        <div style="color:#888;font-size:11px;margin-top:3px;">{desc}</div>
        <div style="color:#555;font-size:10px;margin-top:6px;">ATL {atl:.1f} / CTL {ctl:.1f}</div>
    </div>
</div>'''


def build_card_tss_bloco(tss_semana_real, tss_meta_bloco=420):
    """
    TSS acumulado na semana vs meta do bloco S1 (420/sem).
    Exibido no topo do dashboard, abaixo do card Hoje.
    """
    pct = round((tss_semana_real / tss_meta_bloco) * 100) if tss_meta_bloco > 0 else 0
    pct_bar = min(pct, 150)

    if pct >= 90:
        cor, label = '#10b981', '✅ No alvo'
    elif pct >= 70:
        cor, label = '#4ade80', '📈 Bom progresso'
    elif pct >= 50:
        cor, label = '#facc15', '⚡ Acelerando'
    elif pct > 0:
        cor, label = '#fb923c', '⚠️ Abaixo do alvo'
    else:
        cor, label = '#6b7280', '—'

    falta = max(0, tss_meta_bloco - tss_semana_real)

    return f'''<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;border-left:3px solid {cor};">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <div style="font-size:12px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:1px;">📊 TSS Semana vs Meta Bloco S1</div>
        <div style="font-size:11px;color:{cor};font-weight:700;">{label}</div>
    </div>
    <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px;">
        <span style="font-size:28px;font-weight:700;color:{cor};">{int(tss_semana_real)}</span>
        <span style="font-size:14px;color:#666;">/ {tss_meta_bloco} TSS</span>
        <span style="font-size:16px;color:{cor};font-weight:700;margin-left:4px;">({pct}%)</span>
    </div>
    <div style="background:#1a1a1a;height:10px;border-radius:5px;overflow:hidden;margin-bottom:8px;">
        <div style="background:{cor};height:100%;width:{pct_bar}%;border-radius:5px;transition:width 0.3s;"></div>
    </div>
    <div style="font-size:10px;color:#555;">
        {f'Faltam <b style="color:#ddd;">{int(falta)} TSS</b> para atingir a meta semanal.' if falta > 0 else '<b style="color:#10b981;">Meta da semana atingida!</b>'}
    </div>
</div>'''


# ─── ABA ANALYTICS (atualizada) ──────────────────────────────────────────────

def build_aba_analytics(analytics_data, subjetivos={},
                         distrib=None, ctl=0, atl=0,
                         tss_meta_bloco=420, alvo_str=''):
    """
    Aba Analytics — grid de cards.
    Parâmetros novos v11.8:
      distrib         → calcular_distribuicao() do dashboard_generator
      ctl, atl        → valores atuais para Ramp Rate
      tss_meta_bloco  → meta semanal do bloco (padrão 420)
      alvo_str        → distribuição alvo do bloco ex. '85% Z1-Z2 | 15% Z3 | 0% Z4-Z5'
    """
    if not analytics_data:
        return '<div style="color:#888;padding:20px;text-align:center;">Nenhuma análise disponível</div>'

    h = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">'

    # Cards originais
    h += build_card_teste_ftp(analytics_data.get('teste_ftp', {}))
    h += build_card_power_curve(analytics_data)
    h += build_card_decoupling(analytics_data.get('decoupling', {}))
    h += build_card_forecast(analytics_data.get('forecast', {}))
    # rolo_rua removido v11.8.1

    # Novos cards v11.8
    h += build_card_ef_tendencia(analytics_data.get('ef_tendencia'))
    h += build_card_ramp_rate(ctl, atl)

    # Cards de largura dupla (span 2)
    h += build_card_distribuicao_vs_alvo(distrib, alvo_str)
    h += build_card_historico_ftp(
        analytics_data.get('historico_ftp', []),
        ftp_atual=analytics_data.get('teste_ftp', {}).get('ftp_atual', 210),
        peso=75.6
    )

    h += '</div>'
    return h
