"""
🎨 DASHBOARD CARDS v11.7
Cards HTML para aba Analytics
"""

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

def build_aba_analytics(analytics_data, subjetivos={}):
    """Aba Analytics - retorna apenas grid de cards"""
    if not analytics_data:
        return '<div style="color:#888;padding:20px;text-align:center;">Nenhuma análise disponível</div>'
    
    h = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">'
    
    h += build_card_teste_ftp(analytics_data.get('teste_ftp', {}))
    h += build_card_power_curve(analytics_data)
    h += build_card_decoupling(analytics_data.get('decoupling', {}))
    h += build_card_forecast(analytics_data.get('forecast', {}))
    h += build_card_rolo_rua(analytics_data.get('rolo_rua', {}))
    
    h += '</div>'
    return h
