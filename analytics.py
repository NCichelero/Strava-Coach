"""
📊 ANALYTICS MODULE v11.8
Análises avançadas: Power Curve, Decoupling, TSS Balance, Forecast, Rolo/Rua, Teste FTP Auto
NOVO v11.8: Efficiency Factor (EF) + Histórico FTP estimado
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = 'data'
FTP = 210
PESO = 75.6

def carregar(arquivo):
    path = os.path.join(DATA_DIR, arquivo)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar(arquivo, dados):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, arquivo)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# ─── POWER CURVE ────────────────────────────────────────────────────────────

def calcular_power_curve(treinos_dict, dias=90):
    """Calcula picos de potência"""
    intervalos_seg = [5, 15, 30, 60, 180, 300, 600, 1200, 3600]
    picos_geral = {f"{s}s": 0 for s in intervalos_seg}

    limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    for tid, t in treinos_dict.items():
        if t.get('categoria') != 'ciclismo' or t.get('data', '') < limite:
            continue

        pot_max = t.get('potencia_max', 0) or 0
        pot_norm = t.get('potencia_norm', 0) or 0
        laps = t.get('laps', [])

        for s in intervalos_seg:
            campo = f"{s}s"
            pico = 0

            for lap in laps:
                if lap.get('dur_seg', 0) >= s:
                    pico = max(pico, lap.get('pot_avg', 0))

            if s <= 30:
                pico = max(pico, pot_max)

            if pico == 0 and s in [300, 1200, 3600]:
                if s == 300 and pot_norm > 0:
                    pico = int(pot_norm * 1.15)
                elif pot_norm > 0:
                    pico = int(pot_norm * 0.95)

            if pico > picos_geral[campo]:
                picos_geral[campo] = pico

    pico_20min = picos_geral.get('1200s', 0)
    pico_60min = picos_geral.get('3600s', 0)
    ftp_estimado = int(pico_20min * 0.95) if pico_20min > 0 else (pico_60min if pico_60min > 0 else FTP)

    return {
        'picos': picos_geral,
        'ftp_atual': FTP,
        'ftp_estimado': ftp_estimado,
        'diferenca': ftp_estimado - FTP,
        'sugere_teste': ftp_estimado > FTP * 1.025,
        'percentual_acima': round((ftp_estimado / FTP - 1) * 100, 1) if ftp_estimado > FTP else 0,
        'wkg_estimado': round(ftp_estimado / PESO, 2)
    }

# ─── DECOUPLING ─────────────────────────────────────────────────────────────

def calcular_decoupling(treino):
    """Eficiência aeróbica: < 5% excelente"""
    dur_min = treino.get('duracao_min', 0)
    if dur_min < 60:
        return None

    laps = treino.get('laps', [])
    if len(laps) < 2:
        return None

    total_dur = sum(lap.get('dur_seg', 0) for lap in laps)
    meio = total_dur / 2

    primeira_pot = primeira_fc = primeira_dur = 0
    segunda_pot = segunda_fc = segunda_dur = 0
    acumulado = 0

    for lap in laps:
        dur = lap.get('dur_seg', 0)
        pot = lap.get('pot_avg', 0)
        fc = lap.get('fc_avg', 0)

        if pot == 0 or fc == 0:
            continue

        if acumulado + dur <= meio:
            primeira_pot += pot * dur
            primeira_fc += fc * dur
            primeira_dur += dur
        else:
            segunda_pot += pot * dur
            segunda_fc += fc * dur
            segunda_dur += dur

        acumulado += dur

    if primeira_dur == 0 or segunda_dur == 0:
        return None

    p1, fc1 = primeira_pot / primeira_dur, primeira_fc / primeira_dur
    p2, fc2 = segunda_pot / segunda_dur, segunda_fc / segunda_dur

    razao1 = p1 / fc1 if fc1 > 0 else 0
    razao2 = p2 / fc2 if fc2 > 0 else 0

    if razao1 == 0:
        return None

    decoupling = ((razao1 - razao2) / razao1) * 100

    return {
        'decoupling_pct': round(decoupling, 1),
        'qualidade': 'excelente' if decoupling < 5 else ('bom' if decoupling < 10 else 'ruim')
    }

# ─── TSS BALANCE ─────────────────────────────────────────────────────────────

def calcular_tss_balance(treinos_dict, dias=28):
    """Distribuição de TSS por zona"""
    tss_por_zona = {'Z1': 0, 'Z2': 0, 'Z3': 0, 'Z4': 0, 'Z5': 0}
    limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    for t in treinos_dict.values():
        if t.get('categoria') != 'ciclismo' or t.get('data', '') < limite:
            continue

        for lap in t.get('laps', []):
            zona = lap.get('zona', 'Z2')
            tss_por_zona[zona] = tss_por_zona.get(zona, 0) + (lap.get('tss', 0) or 0)

    total = sum(tss_por_zona.values())
    if total == 0:
        return None

    tss_pct = {z: round((v / total) * 100, 1) for z, v in tss_por_zona.items()}
    baixa = tss_pct['Z1'] + tss_pct['Z2']

    return {
        'tss_pct': tss_pct,
        'modelo': 'polarizado' if baixa >= 75 else ('piramidal' if baixa >= 65 else 'base'),
        'ideal_para': 'VO2max' if baixa >= 75 else ('Threshold' if baixa >= 65 else 'Base')
    }

# ─── FORECAST ───────────────────────────────────────────────────────────────

def forecast_fitness(fitness_atual, dias=28):
    """Projeta CTL/ATL/TSB 28 dias"""
    ctl = fitness_atual.get('ctl', 36)
    atl = fitness_atual.get('atl', 54)

    plano = {0: 55, 1: 0, 2: 90, 3: 0, 4: 90, 5: 175, 6: 100}
    forecast = []

    for i in range(1, dias + 1):
        data = datetime.now().date() + timedelta(days=i)
        wd = data.weekday()
        tss_dia = plano.get(wd, 0)

        ctl = ctl + (tss_dia - ctl) / 42
        atl = atl + (tss_dia - atl) / 7
        tsb = ctl - atl

        forecast.append({
            'data': data.strftime('%Y-%m-%d'),
            'ctl': round(ctl, 1),
            'atl': round(atl, 1),
            'tsb': round(tsb, 1)
        })

    melhor = max(forecast, key=lambda x: x['tsb'])
    maior_ctl = max(forecast, key=lambda x: x['ctl'])

    return {
        'forecast': forecast,
        'melhor_tsb': melhor,
        'maior_ctl': maior_ctl
    }

# ─── ROLO vs RUA ────────────────────────────────────────────────────────────

def analisar_rolo_vs_rua(treinos_dict, subjetivos_dict, dias=28):
    """Onde foram os treinos"""
    limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    rolo = {'count': 0, 'tss_total': 0, 'pot_avg': 0, 'pot_amostras': 0}
    rua = {'count': 0, 'tss_total': 0, 'pot_avg': 0, 'pot_amostras': 0}

    for tid, t in treinos_dict.items():
        if t.get('categoria') != 'ciclismo' or t.get('data', '') < limite:
            continue

        local = subjetivos_dict.get(tid, {}).get('local_real')
        tss = t.get('tss', 0) or 0
        pot = t.get('potencia_norm', 0) or t.get('potencia_avg', 0) or 0

        if local == 'rolo':
            rolo['count'] += 1
            rolo['tss_total'] += tss
            if pot > 0:
                rolo['pot_avg'] += pot
                rolo['pot_amostras'] += 1
        elif local == 'rua':
            rua['count'] += 1
            rua['tss_total'] += tss
            if pot > 0:
                rua['pot_avg'] += pot
                rua['pot_amostras'] += 1

    if rolo['pot_amostras'] > 0:
        rolo['pot_avg'] = round(rolo['pot_avg'] / rolo['pot_amostras'], 0)
    if rua['pot_amostras'] > 0:
        rua['pot_avg'] = round(rua['pot_avg'] / rua['pot_amostras'], 0)

    total = rolo['count'] + rua['count']

    return {
        'rolo': rolo,
        'rua': rua,
        'total': total,
        'rolo_pct': round((rolo['count'] / total) * 100, 1) if total > 0 else 0,
        'rua_pct': round((rua['count'] / total) * 100, 1) if total > 0 else 0
    }

# ─── TESTE FTP AUTO ─────────────────────────────────────────────────────────

def analisar_necessidade_teste_ftp(power_curve, forecast, fitness):
    """Detecta quando fazer teste FTP"""
    ftp_atual = power_curve.get('ftp_atual', FTP)
    ftp_estimado = power_curve.get('ftp_estimado', FTP)
    diferenca = ftp_estimado - ftp_atual
    pct_diff = (diferenca / ftp_atual * 100) if ftp_atual > 0 else 0

    recomendado = pct_diff > 2.5

    melhor_data = None
    melhor_tsb = -999

    if forecast and 'forecast' in forecast:
        for dia in forecast['forecast']:
            tsb = dia.get('tsb', 0)
            if 5 < tsb < 15 and tsb > melhor_tsb:
                melhor_tsb = tsb
                melhor_data = dia.get('data')

    dias = 0
    if melhor_data:
        try:
            data_obj = datetime.strptime(melhor_data, '%Y-%m-%d').date()
            dias = (data_obj - datetime.now().date()).days
        except:
            dias = 0

    if recomendado:
        if pct_diff > 5:
            urgencia = 'alta'
        elif pct_diff > 3:
            urgencia = 'média'
        else:
            urgencia = 'baixa'
    else:
        urgencia = 'nenhuma'

    protocolo = 'Ramp Test'
    if ftp_estimado >= 280:
        protocolo = 'CP6 Test (6 min máximo)'
    elif ftp_estimado >= 200:
        protocolo = 'Sweet Spot Test (2x8min)'

    return {
        'recomendado': recomendado,
        'urgencia': urgencia,
        'ftp_atual': ftp_atual,
        'ftp_estimado': ftp_estimado,
        'diferenca': int(diferenca),
        'pct_diferenca': round(pct_diff, 1),
        'melhor_data': melhor_data,
        'dias_ate_teste': dias,
        'melhor_tsb': round(melhor_tsb, 1),
        'protocolo': protocolo,
        'status': 'pendente' if recomendado else 'ok'
    }

# ─── EFFICIENCY FACTOR (novo v11.8) ─────────────────────────────────────────

def calcular_ef_tendencia(treinos_dict, dias=56):
    """
    Efficiency Factor: potência média / FC média em treinos Z2.
    Tendência crescente = adaptação aeróbica em curso.
    Valores típicos treinados: 1.5–2.5
    """
    limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
    pontos = []

    for tid, t in sorted(treinos_dict.items(), key=lambda x: x[1].get('data', '')):
        if t.get('categoria') != 'ciclismo':
            continue
        data = t.get('data', '')
        if not data or data < limite:
            continue

        fc_avg = t.get('fc_avg', 0) or 0
        pot_avg = t.get('potencia_avg', 0) or 0
        dur = t.get('duracao_min', 0) or 0

        if fc_avg <= 0 or pot_avg <= 0 or dur < 45:
            continue

        pct_ftp = pot_avg / FTP
        # Z2 por FC (129–150) ou por potência (60–78% FTP)
        is_z2 = (129 <= fc_avg <= 152) or (0.60 <= pct_ftp <= 0.78)

        if is_z2:
            ef = round(pot_avg / fc_avg, 3)
            pontos.append({
                'data': data,
                'ef': ef,
                'pot': round(pot_avg),
                'fc': round(fc_avg),
                'dur': dur
            })

    if not pontos:
        return None

    n = len(pontos)
    ef_atual = pontos[-1]['ef']
    ef_media = round(sum(p['ef'] for p in pontos) / n, 3)

    # Tendência: primeira metade vs segunda metade
    tendencia_pct = 0
    if n >= 4:
        m = n // 2
        ef1 = sum(p['ef'] for p in pontos[:m]) / m
        ef2 = sum(p['ef'] for p in pontos[m:]) / (n - m)
        tendencia_pct = round(((ef2 - ef1) / ef1) * 100, 1) if ef1 > 0 else 0

    if ef_atual >= 2.0:
        qualidade, cor = 'Excelente', '#10b981'
    elif ef_atual >= 1.7:
        qualidade, cor = 'Bom', '#4ade80'
    elif ef_atual >= 1.4:
        qualidade, cor = 'Regular', '#facc15'
    else:
        qualidade, cor = 'Baixo', '#f87171'

    return {
        'pontos': pontos[-20:],   # últimos 20 para sparkline
        'ef_atual': ef_atual,
        'ef_media': ef_media,
        'tendencia_pct': tendencia_pct,
        'qualidade': qualidade,
        'cor': cor,
        'n_treinos': n
    }

# ─── HISTÓRICO FTP ESTIMADO (novo v11.8) ─────────────────────────────────────

def calcular_historico_ftp_estimado(treinos_dict):
    """
    Estima FTP mês a mês pelo melhor esforço de ~20min × 0.95.
    Útil para visualizar progressão mesmo sem testes formais.
    """
    por_mes = defaultdict(list)

    for tid, t in treinos_dict.items():
        if t.get('categoria') != 'ciclismo':
            continue
        data = t.get('data', '')
        if not data:
            continue
        mes = data[:7]  # YYYY-MM

        pico_20 = 0

        # 1) laps com duração ~20min (1100–1350s)
        for lap in t.get('laps', []):
            dur_seg = lap.get('dur_seg', 0) or 0
            if 1050 <= dur_seg <= 1400:
                pico_20 = max(pico_20, lap.get('pot_avg', 0) or 0)

        # 2) campo direto
        if pico_20 == 0:
            pico_20 = t.get('pico_20min', 0) or 0

        # 3) treino inteiro ~20min com NP
        if pico_20 == 0:
            dur_min = t.get('duracao_min', 0) or 0
            if 17 <= dur_min <= 26:
                pico_20 = t.get('potencia_norm', 0) or t.get('potencia_avg', 0) or 0

        if pico_20 > 100:  # sanity
            por_mes[mes].append(int(pico_20 * 0.95))

    historico = []
    for mes in sorted(por_mes.keys()):
        melhor = max(por_mes[mes])
        historico.append({
            'mes': mes,
            'ftp_est': melhor,
            'wkg': round(melhor / PESO, 2)
        })

    # Garante que o FTP atual apareça no mês corrente
    mes_atual = datetime.now().strftime('%Y-%m')
    meses = [p['mes'] for p in historico]
    if mes_atual not in meses:
        historico.append({'mes': mes_atual, 'ftp_est': FTP, 'wkg': round(FTP / PESO, 2)})

    return historico

# ─── MAIN ────────────────────────────────────────────────────────────────────

def gerar_analytics_completo():
    """Executa todas análises"""
    print("📊 Gerando análises avançadas...")

    treinos = carregar('treinos.json')
    fitness = carregar('fitness.json')
    subjetivos = carregar('subjetivos.json')

    if not treinos:
        print("❌ Sem treinos")
        return {}

    print("  → Power Curve...")
    power = calcular_power_curve(treinos)

    print("  → TSS Balance...")
    tss_balance = calcular_tss_balance(treinos)

    print("  → Forecast 28 dias...")
    forecast = forecast_fitness(fitness, dias=28)

    print("  → Rolo vs Rua...")
    rolo_rua = analisar_rolo_vs_rua(treinos, subjetivos)

    print("  → Decoupling...")
    decoupling_treinos = {}
    for tid, t in treinos.items():
        if t.get('categoria') == 'ciclismo' and t.get('duracao_min', 0) >= 60:
            dec = calcular_decoupling(t)
            if dec and dec.get('decoupling_pct') is not None:
                decoupling_treinos[tid] = dec

    print("  → Teste FTP...")
    teste_ftp = analisar_necessidade_teste_ftp(power, forecast, fitness)

    print("  → Efficiency Factor (v11.8)...")
    ef_data = calcular_ef_tendencia(treinos)

    print("  → Histórico FTP estimado (v11.8)...")
    historico_ftp = calcular_historico_ftp_estimado(treinos)

    analytics = {
        'gerado_em': datetime.now().isoformat(),
        'power_curve': power,
        'tss_balance': tss_balance,
        'forecast': forecast,
        'rolo_rua': rolo_rua,
        'decoupling': decoupling_treinos,
        'teste_ftp': teste_ftp,
        'ef_tendencia': ef_data,
        'historico_ftp': historico_ftp,
    }

    salvar('analytics.json', analytics)
    print(f"\n✅ Analytics salvo")

    print(f"\n📊 RESUMO:")
    print(f"  Power Curve: FTP est {power['ftp_estimado']}W")
    if power['sugere_teste']:
        print(f"  ⚡ TESTE FTP RECOMENDADO!")
    print(f"  TSS Balance: {tss_balance['modelo'] if tss_balance else 'N/A'}")
    print(f"  Forecast: CTL {forecast['maior_ctl']['ctl']} em {forecast['maior_ctl']['data']}")
    print(f"  Decoupling: {len(decoupling_treinos)} treinos")
    print(f"  Rolo vs Rua: {rolo_rua['rolo_pct']}% / {rolo_rua['rua_pct']}%")
    if ef_data:
        print(f"  EF atual: {ef_data['ef_atual']} ({ef_data['qualidade']}) | tendência {ef_data['tendencia_pct']:+.1f}%")
    print(f"  Histórico FTP: {len(historico_ftp)} meses")

    return analytics

if __name__ == '__main__':
    gerar_analytics_completo()
