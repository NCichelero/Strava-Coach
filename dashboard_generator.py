"""
🎨 DASHBOARD GENERATOR v9.4
- Zonas FC corrigidas (Z3: 145-160, Z4: 161-175, Z5: 176-190)
- VO2max duplo (FC + Potência 5min)
- Aderência da Semana
- Form Curve Forecast (7 dias)
- Meta CTL
- Distribuição de Zonas (Polarização 80/20)
- TSS Semanal destacado
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

FTP = 210
PESO = 75.6
FC_MAX = 190
FC_REPOUSO = 39
META_CTL = 45  # Para FTP 220W
TSS_META_SEMANA = 420  # S1 target

ZONAS_FC = {
    'Z1': (115, 129),
    'Z2': (129, 145),
    'Z3': (145, 161),
    'Z4': (161, 176),
    'Z5': (176, 200),
}

# ─── Loaders ───────────────────────────────────────────────────────────────

def load_data():
    treinos, wellness, fitness = {}, [], {'ctl': 36, 'atl': 54, 'tsb': -18}
    if os.path.exists('data/treinos.json'):
        with open('data/treinos.json', 'r', encoding='utf-8') as f:
            treinos = json.load(f)
    if os.path.exists('data/wellness.json'):
        with open('data/wellness.json', 'r', encoding='utf-8') as f:
            wellness = json.load(f)
    if os.path.exists('data/fitness.json'):
        with open('data/fitness.json', 'r', encoding='utf-8') as f:
            fitness = json.load(f)
    return treinos, wellness, fitness

# ─── Zonas (corrigidas) ───────────────────────────────────────────────────

def zona_por_fc(fc):
    if fc <= 0: return '—'
    if fc < 129: return 'Z1'
    if fc < 145: return 'Z2'
    if fc < 161: return 'Z3'
    if fc < 176: return 'Z4'
    return 'Z5'

def zona_treino(t):
    if t.get('categoria') != 'ciclismo':
        return '—'
    fc = t.get('fc_avg', 0)
    pot = t.get('potencia_avg', 0)
    
    if fc > 50:
        return zona_por_fc(fc)
    if pot > 50:
        pct = pot / FTP
        if pct < 0.55: return 'Z1'
        elif pct < 0.75: return 'Z2'
        elif pct < 0.90: return 'Z3'
        elif pct < 1.05: return 'Z4'
        else: return 'Z5'
    return '—'

# ─── VO2max (duas fórmulas separadas) ──────────────────────────────────────

def vo2max_fc(fc_max=FC_MAX, fc_repouso=FC_REPOUSO):
    """VO2max = 15 * (FC_max / FC_repouso)"""
    if fc_repouso <= 0: return 0
    return round(15 * (fc_max / fc_repouso), 1)

def vo2max_potencia(treinos):
    """VO2max = 16.6 + (8.87 * W/kg em 5min) - últimas 2 semanas"""
    duas_sem = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    picos = [t.get('pico_5min', 0) for t in treinos.values() 
             if t.get('data', '') >= duas_sem and t.get('pico_5min', 0) > 0]
    
    if not picos:
        return 0, 0
    
    melhor_pico = max(picos)
    wkg_5min = melhor_pico / PESO
    vo2 = 16.6 + (8.87 * wkg_5min)
    return round(vo2, 1), melhor_pico

def classificar_vo2(vo2):
    if vo2 >= 55: return 'Excelente', '#10b981'
    elif vo2 >= 47: return 'Muito Bom', '#3b82f6'
    elif vo2 >= 41: return 'Bom', '#facc15'
    elif vo2 >= 33: return 'Regular', '#f97316'
    elif vo2 > 0: return 'Baixo', '#ef4444'
    return '—', '#888'

# ─── Cálculos básicos ──────────────────────────────────────────────────────

def calcular_nota(t):
    cat = t.get('categoria', 'outros')
    if cat == 'ciclismo':
        dur = t.get('duracao_min', 0)
        pot_avg = t.get('potencia_avg', 0)
        fc_avg = t.get('fc_avg', 0)
        pot_norm = t.get('potencia_norm', 0) or pot_avg
        
        if dur < 20: nd = 3
        elif dur < 45: nd = 7
        elif dur < 90: nd = 9
        elif dur < 180: nd = 10
        else: nd = 9.5
        
        if pot_avg > 50:
            pct = pot_avg / FTP
            if pct < 0.55: ni = 5
            elif pct < 0.75: ni = 7.5
            elif pct < 0.90: ni = 8.5
            elif pct < 1.05: ni = 9.5
            else: ni = 10
        elif fc_avg > 0:
            pct = fc_avg / FC_MAX
            if pct < 0.68: ni = 5
            elif pct < 0.76: ni = 7.5
            elif pct < 0.84: ni = 8.5
            elif pct < 0.92: ni = 9.5
            else: ni = 10
        else: ni = 6
        
        if pot_avg > 50 and fc_avg > 0:
            ne = min(10, (pot_avg / fc_avg) * 8)
        else: ne = 6
        
        if pot_norm > 50 and pot_avg > 50:
            vi = pot_norm / pot_avg
            if vi < 1.05: nv = 10
            elif vi < 1.15: nv = 8
            elif vi < 1.25: nv = 6
            else: nv = 4
        else: nv = 6
        
        return round((nd * 0.30) + (ni * 0.35) + (ne * 0.20) + (nv * 0.15), 1)
    elif cat == 'academia':
        dur = t.get('duracao_min', 0)
        if dur < 30: return 5.5
        elif dur < 45: return 6.5
        elif dur < 75: return 8.0
        else: return 8.5
    return 6.0

def tss_treino(t):
    dur = t.get('duracao_min', 0)
    pot_norm = t.get('potencia_norm', 0) or t.get('potencia_avg', 0)
    fc_avg = t.get('fc_avg', 0)
    
    if pot_norm > 50:
        return round(dur * (pot_norm / FTP) ** 2 * 100 / 60, 1)
    elif fc_avg > 0:
        return round(dur * (fc_avg / FC_MAX) ** 2 * 100 / 60, 1)
    return 0

def if_treino(t):
    np = t.get('potencia_norm', 0) or t.get('potencia_avg', 0)
    return round(np / FTP, 2) if np > 50 else 0

def vi_treino(t):
    np = t.get('potencia_norm', 0)
    ap = t.get('potencia_avg', 0)
    return round(np / ap, 2) if (np > 50 and ap > 50) else 0

# ─── Wellness Local + Forecast ─────────────────────────────────────────────

def calcular_wellness_local(treinos):
    """Histórico CTL/ATL/TSB de 60 dias passados + 7 dias forecast"""
    tss_diario = defaultdict(float)
    fc_diario = defaultdict(list)
    
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        tss_diario[data] += tss_treino(t)
        fc = t.get('fc_avg', 0)
        if fc > 0:
            fc_diario[data].append(fc)
    
    hoje = datetime.now().date()
    historico = []
    ctl = atl = 0
    
    for i in range(60, -1, -1):
        data = (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        tss = tss_diario.get(data, 0)
        ctl = ctl + (tss - ctl) / 42
        atl = atl + (tss - atl) / 7
        tsb = ctl - atl
        fc_d = statistics.mean(fc_diario[data]) if fc_diario.get(data) else 0
        
        historico.append({
            'data': data,
            'ctl': round(ctl, 1),
            'atl': round(atl, 1),
            'tsb': round(tsb, 1),
            'tss': round(tss, 1),
            'fc_avg': round(fc_d, 0) if fc_d else 0,
            'forecast': False
        })
    
    # FORECAST 7 dias baseado no plano semanal
    plano_tss = {0: 105, 1: 0, 2: 100, 3: 0, 4: 100, 5: 250, 6: 30}  # Seg-Dom
    
    ctl_fc = ctl
    atl_fc = atl
    
    for i in range(1, 8):
        d_futuro = hoje + timedelta(days=i)
        weekday = d_futuro.weekday()
        tss_plan = plano_tss.get(weekday, 0)
        
        ctl_fc = ctl_fc + (tss_plan - ctl_fc) / 42
        atl_fc = atl_fc + (tss_plan - atl_fc) / 7
        tsb_fc = ctl_fc - atl_fc
        
        historico.append({
            'data': d_futuro.strftime('%Y-%m-%d'),
            'ctl': round(ctl_fc, 1),
            'atl': round(atl_fc, 1),
            'tsb': round(tsb_fc, 1),
            'tss': tss_plan,
            'fc_avg': 0,
            'forecast': True
        })
    
    return historico

# ─── Aderência ─────────────────────────────────────────────────────────────

def calcular_aderencia(treinos):
    """Analisa última semana: treinos planejados vs realizados"""
    hoje = datetime.now()
    seg_atual = hoje - timedelta(days=hoje.weekday())
    
    # Treinos planejados (rotina padrão)
    planejado = {
        0: ('Segunda 05:30', 'ciclismo', 70),  # Z2
        1: ('Terça', 'academia', 60),
        2: ('Quarta 05:30', 'ciclismo', 70),   # Threshold
        3: ('Quinta', 'academia', 60),
        4: ('Sexta 05:30', 'ciclismo', 70),    # Sweet Spot
        5: ('Sábado', 'ciclismo', 180),        # Longo
        6: ('Domingo', 'recuperacao', 0),
    }
    
    # Treinos realizados nesta semana
    realizado = defaultdict(list)
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            if dt >= seg_atual and dt < seg_atual + timedelta(days=7):
                realizado[dt.weekday()].append(t)
        except: continue
    
    resultado = []
    tss_plan_total = 0
    tss_real_total = 0
    
    for wd in range(7):
        nome_plan, cat_plan, dur_plan = planejado[wd]
        tss_plan = {0: 60, 2: 70, 4: 65, 5: 200}.get(wd, 0)
        tss_plan_total += tss_plan
        
        treinos_dia = realizado.get(wd, [])
        tss_real_dia = sum(tss_treino(t) for t in treinos_dia)
        tss_real_total += tss_real_dia
        
        # Status
        if wd > hoje.weekday():
            status = 'futuro'
            icone = '⏳'
        elif treinos_dia:
            # Verifica se faz sentido
            categorias = [t.get('categoria') for t in treinos_dia]
            if cat_plan in categorias or cat_plan == 'recuperacao':
                status = 'ok'
                icone = '✅'
            else:
                status = 'parcial'
                icone = '⚠️'
        elif cat_plan == 'recuperacao':
            status = 'ok'
            icone = '✅'
        else:
            status = 'perdido'
            icone = '❌'
        
        resultado.append({
            'weekday': wd,
            'plan': nome_plan,
            'cat': cat_plan,
            'tss_plan': tss_plan,
            'tss_real': round(tss_real_dia, 1),
            'treinos': [t.get('nome', '') for t in treinos_dia],
            'status': status,
            'icone': icone
        })
    
    perdidos = sum(1 for r in resultado if r['status'] == 'perdido')
    aderencia_pct = round((1 - perdidos / 5) * 100) if perdidos <= 5 else 0  # 5 treinos planejados
    
    return {
        'dias': resultado,
        'tss_plan': tss_plan_total,
        'tss_real': round(tss_real_total, 1),
        'perdidos': perdidos,
        'aderencia_pct': aderencia_pct
    }

# ─── Distribuição de Zonas (Polarização 80/20) ────────────────────────────

def calcular_distribuicao_zonas(treinos):
    """% de tempo em cada zona nas últimas 4 semanas"""
    quatro_sem = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')
    
    tempo_zona = defaultdict(float)
    
    for t in treinos.values():
        if t.get('categoria') != 'ciclismo': continue
        if t.get('data', '') < quatro_sem: continue
        
        dur = t.get('duracao_min', 0)
        
        # Se tem laps detalhados, usa eles
        laps = t.get('laps', [])
        if laps:
            for lap in laps:
                zona = lap.get('zona', '—')
                if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
                    tempo_zona[zona] += lap.get('dur_min', 0)
        else:
            # Senão, atribui zona principal ao treino todo
            zona = zona_treino(t)
            if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
                tempo_zona[zona] += dur
    
    total = sum(tempo_zona.values())
    if total == 0:
        return None
    
    pcts = {z: round((tempo_zona[z] / total) * 100, 1) for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']}
    
    # Análise polarização
    baixa = pcts['Z1'] + pcts['Z2']
    media = pcts['Z3']
    alta = pcts['Z4'] + pcts['Z5']
    
    if baixa >= 75 and alta >= 10 and media <= 15:
        modelo = '🎯 Polarizado 80/20'
        cor = '#10b981'
        descricao = 'Distribuição ideal para evolução: muito Z2 + intervalados Z4/Z5'
    elif media >= 30:
        modelo = '⚠️ Piramidal (excesso Z3)'
        cor = '#facc15'
        descricao = 'Muito tempo em Z3 (sweet spot). Pode causar fadiga acumulada'
    elif baixa >= 90:
        modelo = '📉 Sub-polarizado'
        cor = '#9ca3af'
        descricao = 'Falta intensidade. Adicione intervalados Z4/Z5'
    else:
        modelo = '⚖️ Equilibrado'
        cor = '#3b82f6'
        descricao = 'Distribuição mista, pode otimizar'
    
    return {
        'pcts': pcts,
        'total_min': round(total),
        'modelo': modelo,
        'cor': cor,
        'descricao': descricao,
        'baixa': baixa,
        'media': media,
        'alta': alta
    }

# ─── Previsão FTP, Alertas ─────────────────────────────────────────────────

def prever_ftp(treinos):
    cic = [t for t in treinos.values() 
           if t.get('categoria') == 'ciclismo' and t.get('potencia_avg', 0) > 50]
    if len(cic) < 5: return None, None, None
    
    por_sem = defaultdict(list)
    for t in cic:
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            week = (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
            score = calcular_nota(t) + (1.5 if zona_treino(t) in ['Z4', 'Z5'] else 0)
            por_sem[week].append(score)
        except: pass
    
    if len(por_sem) < 3: return None, None, None
    
    sems = sorted(por_sem.keys())[-8:]
    scores = [statistics.mean(por_sem[w]) for w in sems]
    if len(scores) < 2: return None, None, None
    
    n = len(scores)
    x = list(range(n))
    mx = sum(x) / n
    my = sum(scores) / n
    num = sum((x[i] - mx) * (scores[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den == 0: return None, None, None
    
    slope = num / den
    ganho = slope * 0.3
    if ganho <= 0: return None, None, None
    
    return 220 - FTP, round((220 - FTP) / ganho), round(ganho, 1)

def gerar_alertas(fitness):
    al = []
    tsb = fitness.get('tsb', 0)
    if tsb < -30: al.append(('🔴', f'TSB {tsb:.0f} — Fadiga crítica. Descanse!'))
    elif tsb < -20: al.append(('🟠', f'TSB {tsb:.0f} — Fadiga alta.'))
    elif tsb < -10: al.append(('🟡', f'TSB {tsb:.0f} — Cuidado com carga.'))
    elif tsb > 10: al.append(('🟢', f'TSB {tsb:.0f} — Forma ótima!'))
    elif tsb > 5: al.append(('🟢', f'TSB {tsb:.0f} — Pronto para intensidade.'))
    return al

# ─── Suplementação ─────────────────────────────────────────────────────────

def calcular_suplementacao(dur_min, pct_max):
    if dur_min < 60: return ['Água + sal']
    eventos = ['⏱️ -30min: 1 fatia pão + doce de leite + banana (~50g carb)']
    if dur_min < 90:
        eventos.append('⏱️ 30min: 1 bananinha (36g) + 500ml água')
    elif dur_min < 150:
        eventos += [
            '⏱️ 30min: 1 bananinha (36g) + 500ml água',
            '⏱️ 60min: 30g carbo 2:1 em 500ml',
            '⏱️ 90min: 1 bananinha (36g)',
        ]
    else:
        eventos += [
            '⏱️ 30min: 1 bananinha (36g) + 500ml água',
            '⏱️ 60min: 1 bananinha (36g) + 500ml água',
            '⏱️ 90min: 40g carbo 2:1 em 500ml',
            '⏱️ 120min: 1 bananinha (36g) + 500ml água',
            '⏱️ 150min: 40g carbo 2:1 em 500ml',
        ]
        if dur_min >= 180:
            eventos.append('⏱️ 180min: 1 bananinha (36g)')
    eventos.append('⏱️ Pós (até 30min): Whey + banana + pão de queijo')
    return eventos

# ─── Plano Próxima Semana ──────────────────────────────────────────────────

def watts_pct(pmin, pmax):
    return f"{int(FTP * pmin)}-{int(FTP * pmax)}W"

def fc_zona_str(z):
    if z in ZONAS_FC:
        lo, hi = ZONAS_FC[z]
        return f"{lo}-{hi}bpm"
    return "—"

def plano_proxima_semana(intensidade):
    if intensidade == 'leve':
        return {
            'segunda': {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'terca': {'nome': '🏋️ Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            'quarta': {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'quinta': {'nome': '🏋️ Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            'sexta': {'nome': 'Z2 Light', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 60,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 baixa', 'dur': 40, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'sabado': {'nome': 'Longo Z2 Suave', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 150,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Main Z2', 'dur': 120, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            'domingo': {'nome': 'Descanso', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0,
                'blocos': [{'nome': 'Descanso total', 'dur': 0, 'detalhes': 'Recuperação completa'}]},
        }
    elif intensidade == 'forte':
        return {
            'segunda': {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.65, 'pct_max': 0.78, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'terca': {'nome': '🏋️ Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            'quarta': {'nome': 'VO2max 5x3min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 75,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 3min VO2max', 'dur': 3, 'pct_min': 1.10, 'pct_max': 1.20, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 3min VO2max', 'dur': 3, 'pct_min': 1.10, 'pct_max': 1.20, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '3º 3min VO2max', 'dur': 3, 'pct_min': 1.10, 'pct_max': 1.20, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '4º 3min VO2max', 'dur': 3, 'pct_min': 1.10, 'pct_max': 1.20, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '5º 3min VO2max', 'dur': 3, 'pct_min': 1.10, 'pct_max': 1.20, 'zona': 'Z5'},
                    {'nome': 'Cooldown', 'dur': 13, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'quinta': {'nome': '🏋️ Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            'sexta': {'nome': 'Threshold 3x15min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 90,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '3º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'sabado': {'nome': 'Longo + Sweet Spot', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 180,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Z2', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.75, 'zona': 'Z2'},
                    {'nome': 'Sweet Spot 1', 'dur': 20, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2 Recovery', 'dur': 10, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Sweet Spot 2', 'dur': 20, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            'domingo': {'nome': 'Recuperação', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0,
                'blocos': [{'nome': 'Descanso ou caminhada leve', 'dur': 30, 'detalhes': 'Conforme TSB'}]},
        }
    else:
        return {
            'segunda': {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.75, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'terca': {'nome': '🏋️ Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            'quarta': {'nome': 'Threshold 2x15min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 80,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 15min FTP', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.95, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 8, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 15min FTP', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.95, 'zona': 'Z4'},
                    {'nome': 'Z2', 'dur': 17, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'quinta': {'nome': '🏋️ Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            'sexta': {'nome': 'Sweet Spot 3x10min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 80,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 10min SS', 'dur': 10, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 10min SS', 'dur': 10, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '3º 10min SS', 'dur': 10, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2', 'dur': 15, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            'sabado': {'nome': 'Longo Z2', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 180,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1-Z2'},
                    {'nome': 'Endurance Z2', 'dur': 150, 'pct_min': 0.65, 'pct_max': 0.78, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            'domingo': {'nome': 'Recuperação Ativa', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0,
                'blocos': [{'nome': 'Descanso ou caminhada', 'dur': 30, 'detalhes': 'Conforme TSB'}]},
        }

# ─── Build Dashboard ───────────────────────────────────────────────────────

def build_dashboard(treinos, wellness, fitness):
    treinos_list = sorted(treinos.values(), key=lambda x: x.get('data', ''), reverse=True)
    total = len(treinos_list)
    cic = sum(1 for t in treinos_list if t.get('categoria') == 'ciclismo')
    acad = sum(1 for t in treinos_list if t.get('categoria') == 'academia')
    
    ftp_gap, sem_220, ganho_ftp = prever_ftp(treinos)
    alertas = gerar_alertas(fitness)
    wkg = round(FTP / PESO, 2)
    
    historico = calcular_wellness_local(treinos)
    aderencia = calcular_aderencia(treinos)
    distrib = calcular_distribuicao_zonas(treinos)
    
    # VO2max
    vo2_fc = vo2max_fc(FC_MAX, FC_REPOUSO)
    vo2_pot, melhor_5min = vo2max_potencia(treinos)
    
    label_fc, cor_fc = classificar_vo2(vo2_fc)
    label_pot, cor_pot = classificar_vo2(vo2_pot)
    
    por_semana = defaultdict(list)
    for t in treinos_list:
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            week = (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
            por_semana[week].append(t)
        except: pass
    
    hoje = datetime.now()
    seg_atual = (hoje - timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')
    
    # Último dia real (não forecast)
    ultimos_reais = [h for h in historico if not h.get('forecast')]
    ultimo = ultimos_reais[-1] if ultimos_reais else {'ctl': 36, 'atl': 54, 'tsb': -18, 'tss': 0, 'fc_avg': 0}
    ctl = ultimo['ctl']
    atl = ultimo['atl']
    tsb = ultimo['tsb']
    
    if tsb < -30: cor_tsb = '#f87171'
    elif tsb < -10: cor_tsb = '#fbbf24'
    elif tsb < 5: cor_tsb = '#9ca3af'
    else: cor_tsb = '#4ade80'
    
    # Meta CTL
    ctl_pct = round((ctl / META_CTL) * 100)
    if ctl_pct > 100: ctl_pct = 100
    
    # ─── Cards de Análise ──────────────────────────────────────────────────
    analises_html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px;">'
    
    if ftp_gap and sem_220:
        analises_html += f'''<div style="background:linear-gradient(135deg,#3b82f6,#1e40af);padding:16px;border-radius:10px;color:white;">
<div style="font-size:12px;opacity:0.9;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">📈 Previsão FTP</div>
<div style="font-size:24px;font-weight:700;margin-bottom:6px;">+{int(ftp_gap)}W</div>
<div style="font-size:11px;opacity:0.95;">FTP 220W em ~<strong>{sem_220} sem</strong> · +{ganho_ftp}W/sem</div>
</div>'''
    
    analises_html += f'''<div style="background:linear-gradient(135deg,#ec4899,#be185d);padding:16px;border-radius:10px;color:white;">
<div style="font-size:12px;opacity:0.9;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🏔️ W/kg</div>
<div style="font-size:24px;font-weight:700;margin-bottom:6px;">{wkg}</div>
<div style="font-size:11px;opacity:0.95;">FTP {FTP}W · {PESO}kg · Meta 3.0</div>
</div>
<div style="background:linear-gradient(135deg,#10b981,#047857);padding:16px;border-radius:10px;color:white;">
<div style="font-size:12px;opacity:0.9;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🎯 Meta CTL ({META_CTL})</div>
<div style="font-size:24px;font-weight:700;margin-bottom:6px;">{ctl_pct}%</div>
<div style="font-size:11px;opacity:0.95;">Atual: {ctl} · Faltam {max(0, META_CTL - ctl):.1f}</div>
<div style="background:rgba(255,255,255,0.2);height:4px;border-radius:2px;margin-top:6px;"><div style="background:white;height:100%;width:{ctl_pct}%;border-radius:2px;"></div></div>
</div>
</div>'''
    
    # VO2max duplo
    analises_html += f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
<div style="background:#111;padding:16px;border-radius:10px;border:1px solid #222;">
<div style="font-size:12px;color:#666;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🫁 VO₂max (Fórmula FC)</div>
<div style="font-size:28px;font-weight:700;color:{cor_fc};">{vo2_fc} <span style="font-size:14px;color:#666;">ml/kg/min</span></div>
<div style="font-size:11px;color:#888;margin-top:4px;">15 × (FC_max/FC_rep) = 15 × ({FC_MAX}/{FC_REPOUSO})</div>
<div style="font-size:11px;color:{cor_fc};margin-top:6px;font-weight:600;">{label_fc}</div>
</div>
<div style="background:#111;padding:16px;border-radius:10px;border:1px solid #222;">
<div style="font-size:12px;color:#666;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🫁 VO₂max (Potência 5min)</div>
<div style="font-size:28px;font-weight:700;color:{cor_pot};">{vo2_pot if vo2_pot > 0 else "—"} <span style="font-size:14px;color:#666;">ml/kg/min</span></div>
<div style="font-size:11px;color:#888;margin-top:4px;">16.6 + (8.87 × {round(melhor_5min/PESO, 2) if melhor_5min > 0 else "—"} W/kg) · Pico 5min: {melhor_5min}W</div>
<div style="font-size:11px;color:{cor_pot};margin-top:6px;font-weight:600;">{label_pot if vo2_pot > 0 else "Dados insuficientes (14d)"}</div>
</div>
</div>'''
    
    if alertas:
        ai = ''.join([f'<div style="display:flex;gap:8px;align-items:start;padding:8px;background:#0a0a0a;border-radius:6px;"><span style="font-size:14px;">{n}</span><div style="flex:1;font-size:11px;color:#ddd;">{m}</div></div>' for n, m in alertas])
        analises_html += f'<div style="background:#1a1a1a;border-radius:10px;padding:12px;margin-bottom:20px;border-left:3px solid #facc15;"><div style="font-size:12px;font-weight:600;color:#fbbf24;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;">⚡ Alertas</div><div style="display:flex;flex-direction:column;gap:8px;">{ai}</div></div>'
    
    # ─── Aderência da Semana ───────────────────────────────────────────────
    aderencia_html = '<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aderencia_html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
    aderencia_html += '<h3 style="font-size:14px;color:#fff;">📉 Aderência da Semana Atual</h3>'
    
    cor_ader = '#4ade80' if aderencia['aderencia_pct'] >= 80 else ('#facc15' if aderencia['aderencia_pct'] >= 50 else '#f87171')
    aderencia_html += f'<div style="font-size:20px;font-weight:700;color:{cor_ader};">{aderencia["aderencia_pct"]}%</div>'
    aderencia_html += '</div>'
    
    aderencia_html += '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:12px;">'
    dias_pt = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SÁB', 'DOM']
    for i, dia in enumerate(aderencia['dias']):
        cor_dia = {'ok': '#4ade8033', 'perdido': '#f8717133', 'parcial': '#fbbf2433', 'futuro': '#1a1a1a'}[dia['status']]
        borda_dia = {'ok': '#4ade80', 'perdido': '#f87171', 'parcial': '#fbbf24', 'futuro': '#333'}[dia['status']]
        aderencia_html += f'<div style="background:{cor_dia};border:1px solid {borda_dia};padding:8px;border-radius:6px;text-align:center;">'
        aderencia_html += f'<div style="font-size:9px;color:#888;margin-bottom:4px;">{dias_pt[i]}</div>'
        aderencia_html += f'<div style="font-size:18px;margin-bottom:4px;">{dia["icone"]}</div>'
        aderencia_html += f'<div style="font-size:9px;color:#aaa;">TSS</div>'
        aderencia_html += f'<div style="font-size:11px;color:#ddd;font-weight:600;">{int(dia["tss_real"])}/{dia["tss_plan"]}</div>'
        aderencia_html += '</div>'
    aderencia_html += '</div>'
    
    # TSS planejado vs realizado
    tss_pct = round((aderencia['tss_real'] / aderencia['tss_plan']) * 100) if aderencia['tss_plan'] > 0 else 0
    cor_tss = '#4ade80' if 80 <= tss_pct <= 120 else ('#facc15' if 60 <= tss_pct <= 140 else '#f87171')
    aderencia_html += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">'
    aderencia_html += f'<div><div style="font-size:10px;color:#666;margin-bottom:4px;">TSS PLANEJADO</div><div style="font-size:18px;font-weight:700;color:#3b82f6;">{aderencia["tss_plan"]}</div></div>'
    aderencia_html += f'<div><div style="font-size:10px;color:#666;margin-bottom:4px;">TSS REALIZADO</div><div style="font-size:18px;font-weight:700;color:{cor_tss};">{int(aderencia["tss_real"])}</div></div>'
    aderencia_html += f'<div><div style="font-size:10px;color:#666;margin-bottom:4px;">CUMPRIMENTO</div><div style="font-size:18px;font-weight:700;color:{cor_tss};">{tss_pct}%</div></div>'
    aderencia_html += '</div>'
    
    # Recomendação
    if aderencia['perdidos'] >= 2:
        aderencia_html += '<div style="margin-top:10px;padding:10px;background:#1a0a0a;border-radius:6px;border-left:3px solid #f87171;font-size:11px;color:#fca5a5;">⚠️ Você perdeu ' + str(aderencia['perdidos']) + ' treinos. Próxima semana será automaticamente LEVE para recuperação.</div>'
    elif aderencia['perdidos'] == 1:
        aderencia_html += '<div style="margin-top:10px;padding:10px;background:#1a1500;border-radius:6px;border-left:3px solid #fbbf24;font-size:11px;color:#fde68a;">⚠️ 1 treino perdido. Considere ajustar intensidade na próxima sessão para compensar.</div>'
    else:
        aderencia_html += '<div style="margin-top:10px;padding:10px;background:#0a1a0a;border-radius:6px;border-left:3px solid #4ade80;font-size:11px;color:#86efac;">✅ Excelente aderência! Continue assim.</div>'
    
    aderencia_html += '</div>'
    
    # ─── Distribuição de Zonas ─────────────────────────────────────────────
    distrib_html = ''
    if distrib:
        distrib_html = '<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
        distrib_html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        distrib_html += '<h3 style="font-size:14px;color:#fff;">🎯 Distribuição de Zonas (últimas 4 semanas)</h3>'
        distrib_html += f'<div style="font-size:12px;color:{distrib["cor"]};font-weight:600;">{distrib["modelo"]}</div>'
        distrib_html += '</div>'
        
        distrib_html += f'<div style="font-size:11px;color:#888;margin-bottom:14px;">{distrib["descricao"]}</div>'
        
        # Barras das zonas
        cores_z = {'Z1': '#9ca3af', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}
        
        distrib_html += '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">'
        for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
            pct = distrib['pcts'][z]
            min_zona = int((pct / 100) * distrib['total_min'])
            distrib_html += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;">'
            distrib_html += f'<div style="font-size:11px;color:{cores_z[z]};font-weight:600;margin-bottom:4px;">{z}</div>'
            distrib_html += f'<div style="font-size:18px;font-weight:700;color:#fff;">{pct}%</div>'
            distrib_html += f'<div style="font-size:9px;color:#666;margin-top:2px;">{min_zona}min</div>'
            distrib_html += f'<div style="background:#1a1a1a;height:3px;border-radius:2px;margin-top:6px;"><div style="background:{cores_z[z]};height:100%;width:{pct}%;border-radius:2px;"></div></div>'
            distrib_html += '</div>'
        distrib_html += '</div>'
        
        # Resumo polarização
        distrib_html += f'<div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:11px;">'
        distrib_html += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Baixa Intensidade:</span> <strong style="color:#4ade80;">{distrib["baixa"]:.0f}%</strong></div>'
        distrib_html += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Média (Z3):</span> <strong style="color:#facc15;">{distrib["media"]:.0f}%</strong></div>'
        distrib_html += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Alta (Z4-Z5):</span> <strong style="color:#f87171;">{distrib["alta"]:.0f}%</strong></div>'
        distrib_html += '</div>'
        
        distrib_html += '</div>'
    
    # ─── Histórico ────────────────────────────────────────────────────────
    sem_ord = sorted(por_semana.keys(), 
                    key=lambda w: (0 if w == seg_atual else 1, -datetime.strptime(w, '%Y-%m-%d').timestamp()))
    
    hist_html = ''
    for week in sem_ord[:8]:
        t_sem = por_semana[week]
        dt_seg = datetime.strptime(week, '%Y-%m-%d')
        dt_dom = dt_seg + timedelta(days=6)
        label = f"{dt_seg.strftime('%d/%m')} — {dt_dom.strftime('%d/%m')}"
        is_atual = week == seg_atual
        
        border = 'border:1px solid #facc15;' if is_atual else 'border:1px solid #222;'
        atual_b = '<span style="color:#facc15;font-weight:600;font-size:10px;margin-left:8px;">▶ SEMANA ATUAL</span>' if is_atual else ''
        
        tss_total = sum(tss_treino(t) for t in t_sem)
        
        # TSS classificação (meta: 420 TSS/semana)
        if 380 <= tss_total <= 460:
            tss_cor = '#4ade80'
            tss_label = '✅ Ideal'
        elif tss_total < 250:
            tss_cor = '#9ca3af'
            tss_label = '📉 Baixa'
        elif tss_total < 380:
            tss_cor = '#facc15'
            tss_label = '⚖️ Moderada'
        elif tss_total <= 550:
            tss_cor = '#fb923c'
            tss_label = '🔥 Alta'
        else:
            tss_cor = '#f87171'
            tss_label = '⚠️ Excesso'
        
        hist_html += f'<div class="week-block" style="background:#111;border-radius:10px;padding:14px;margin-bottom:10px;{border}">'
        hist_html += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        hist_html += f'<div style="font-size:13px;font-weight:600;color:#ddd;">{label}<span style="color:#666;font-weight:400;margin-left:10px;">{len(t_sem)} treinos</span>{atual_b}</div>'
        hist_html += f'<div style="display:flex;gap:10px;align-items:center;">'
        hist_html += f'<div style="font-size:11px;color:#666;">TSS Semana:</div>'
        hist_html += f'<div style="font-size:18px;font-weight:700;color:{tss_cor};">{int(tss_total)}</div>'
        hist_html += f'<div style="font-size:10px;color:{tss_cor};font-weight:600;padding:2px 8px;background:{tss_cor}22;border-radius:4px;">{tss_label}</div>'
        hist_html += f'<div style="font-size:10px;color:#666;">/ Meta {TSS_META_SEMANA}</div>'
        hist_html += f'</div></div>'
        
        for idx, t in enumerate(t_sem):
            cat = t.get('categoria', 'outros')
            icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '🏃')
            cor_cat = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
            
            nota = calcular_nota(t)
            zona = zona_treino(t)
            tss_t = tss_treino(t)
            if_v = if_treino(t)
            vi_v = vi_treino(t)
            laps_t = t.get('laps', [])
            pico5 = t.get('pico_5min', 0)
            
            uid = f"treino-{week}-{idx}"
            
            hist_html += f'<div class="treino-item" data-categoria="{cat}" style="background:#0a0a0a;border-radius:6px;margin-bottom:6px;border-left:3px solid {cor_cat};overflow:hidden;">'
            hist_html += f'<div class="treino-header" onclick="toggleTreino(\'{uid}\')" style="padding:10px 12px;cursor:pointer;user-select:none;">'
            hist_html += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            hist_html += f'<div style="font-size:12px;color:#ddd;"><span style="font-size:14px;">{icon}</span> <strong>{t.get("nome", "Sem nome")}</strong> <span style="color:#666;font-weight:400;font-size:10px;margin-left:6px;">▼</span></div>'
            hist_html += f'<div style="font-size:10px;color:#666;">{t.get("data", "")} · Nota: {nota}/10 · TSS: {tss_t}</div>'
            hist_html += f'</div>'
            hist_html += f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;font-size:10px;color:#888;">'
            hist_html += f'<div>Zona<br><span style="color:#ddd;font-weight:600;">{zona}</span></div>'
            hist_html += f'<div>Dist<br><span style="color:#ddd;font-weight:600;">{t.get("distancia_km", 0)}km</span></div>'
            hist_html += f'<div>Tempo<br><span style="color:#ddd;font-weight:600;">{int(t.get("duracao_min", 0))}min</span></div>'
            hist_html += f'<div>Watts<br><span style="color:#ddd;font-weight:600;">{int(t.get("potencia_avg", 0))}W</span></div>'
            hist_html += f'<div>FC<br><span style="color:#ddd;font-weight:600;">{int(t.get("fc_avg", 0))}bpm</span></div>'
            hist_html += f'</div></div>'
            
            hist_html += f'<div id="{uid}" class="treino-details" style="display:none;padding:12px;background:#050505;border-top:1px solid #1a1a1a;">'
            
            if cat == 'ciclismo':
                hist_html += '<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">📊 Métricas</div>'
                hist_html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">'
                
                metricas = [
                    ('TSS', f'{tss_t}', '#3b82f6'),
                    ('IF', f'{if_v}', '#a855f7'),
                    ('VI', f'{vi_v}' if vi_v > 0 else '—', '#ec4899'),
                    ('NP', f'{int(t.get("potencia_norm", 0))}W' if t.get('potencia_norm', 0) > 0 else '—', '#f59e0b'),
                    ('Pot. Máx', f'{int(t.get("potencia_max", 0))}W' if t.get('potencia_max', 0) > 0 else '—', '#ef4444'),
                    ('Pico 5min', f'{pico5}W' if pico5 > 0 else '—', '#8b5cf6'),
                    ('FC Máx', f'{int(t.get("fc_max", 0))}bpm' if t.get('fc_max', 0) > 0 else '—', '#dc2626'),
                    ('Elevação', f'{int(t.get("elevacao", 0))}m', '#0ea5e9'),
                    ('Vel. Média', f'{t.get("velocidade_avg", 0)}km/h', '#06b6d4'),
                    ('Vel. Máx', f'{t.get("velocidade_max", 0)}km/h' if t.get('velocidade_max', 0) > 0 else '—', '#0891b2'),
                    ('Cadência', f'{int(t.get("cadence_avg", 0))}rpm' if t.get('cadence_avg', 0) > 0 else '—', '#8b5cf6'),
                    ('Calorias', f'{int(t.get("calorias", 0))}cal' if t.get('calorias', 0) > 0 else '—', '#f97316'),
                ]
                
                for lbl, val, c in metricas:
                    hist_html += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">{lbl}</div><div style="font-size:14px;font-weight:700;color:{c};">{val}</div></div>'
                hist_html += '</div>'
                
                # Laps
                if laps_t and len(laps_t) > 1:
                    hist_html += f'<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">🔄 Voltas ({len(laps_t)})</div>'
                    hist_html += '<div style="background:#0a0a0a;border-radius:6px;overflow:hidden;">'
                    hist_html += '<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;background:#1a1a1a;font-size:10px;color:#666;text-transform:uppercase;">'
                    hist_html += '<div>#</div><div>Nome</div><div>Tempo</div><div>Dist</div><div>Watts</div><div>Máx</div><div>FC</div><div>Zona</div></div>'
                    
                    for lap in laps_t:
                        zl = lap.get('zona', '—')
                        cz = {'Z1': '#9ca3af', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}.get(zl, '#888')
                        ds = lap.get('dur_seg', 0)
                        ts = f"{ds//3600}h{(ds%3600)//60:02d}m" if ds >= 3600 else f"{ds//60}m{ds%60:02d}s"
                        
                        hist_html += f'<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;border-top:1px solid #1a1a1a;font-size:11px;align-items:center;">'
                        hist_html += f'<div style="color:#666;font-weight:600;">{lap.get("idx", "—")}</div>'
                        hist_html += f'<div style="color:#ddd;">{lap.get("nome", "")[:30]}</div>'
                        hist_html += f'<div style="color:#999;">{ts}</div>'
                        hist_html += f'<div style="color:#999;">{lap.get("dist_km", 0)}km</div>'
                        hist_html += f'<div style="color:#ddd;font-weight:600;">{lap.get("pot_avg", 0)}W</div>'
                        hist_html += f'<div style="color:#999;font-size:10px;">{lap.get("pot_max", 0)}W</div>'
                        hist_html += f'<div style="color:#ddd;">{lap.get("fc_avg", 0)}bpm</div>'
                        hist_html += f'<div style="color:{cz};font-weight:600;">{zl}</div>'
                        hist_html += '</div>'
                    hist_html += '</div>'
            else:
                hist_html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">'
                hist_html += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">CATEGORIA</div><div style="font-size:14px;font-weight:700;">{cat.upper()}</div></div>'
                hist_html += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">TIPO</div><div style="font-size:14px;font-weight:700;">{t.get("tipo", "—")}</div></div>'
                hist_html += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">FC MÁX</div><div style="font-size:14px;font-weight:700;color:#ef4444;">{int(t.get("fc_max", 0))}bpm</div></div>'
                hist_html += '</div>'
            
            hist_html += '</div></div>'
        
        hist_html += '</div>'
    
    # ─── Condicionamento ──────────────────────────────────────────────────
    hist_json = json.dumps(historico)
    
    wellness_html = '<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    wellness_html += f'<h3 style="font-size:14px;color:#fff;margin-bottom:6px;">📊 Condicionamento</h3>'
    wellness_html += f'<div style="font-size:11px;color:#666;margin-bottom:14px;">Último dia real: {ultimo["data"]} · Forecast 7 dias incluso</div>'
    
    wellness_html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">'
    wellness_html += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">CTL (Fitness)</div><div style="font-size:22px;font-weight:700;color:#3b82f6;">{ultimo["ctl"]}</div></div>'
    wellness_html += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">ATL (Fadiga)</div><div style="font-size:22px;font-weight:700;color:#fb923c;">{ultimo["atl"]}</div></div>'
    wellness_html += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">TSB (Forma)</div><div style="font-size:22px;font-weight:700;color:{cor_tsb};">{ultimo["tsb"]}</div></div>'
    wellness_html += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">TSS Hoje</div><div style="font-size:22px;font-weight:700;color:#10b981;">{int(ultimo["tss"])}</div></div>'
    wellness_html += '</div>'
    
    wellness_html += '''<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;">
<div style="font-size:11px;color:#666;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;">📈 Métricas (toggle)</div>
<div id="metric-toggles" style="display:flex;flex-wrap:wrap;gap:8px;">
<button class="metric-btn active" data-metric="ctl" data-color="#3b82f6">CTL</button>
<button class="metric-btn active" data-metric="atl" data-color="#fb923c">ATL</button>
<button class="metric-btn active" data-metric="tsb" data-color="#4ade80">TSB</button>
<button class="metric-btn" data-metric="tss" data-color="#a855f7">TSS</button>
</div>
</div>'''
    
    wellness_html += '<div style="background:#0a0a0a;padding:14px;border-radius:8px;"><canvas id="wellnessChart" style="width:100%;height:400px;"></canvas></div>'
    wellness_html += '</div>'
    
    # ─── Próxima Semana ─────────────────────────────────────────────────────
    # AJUSTE: se perdidos >= 2, força LEVE
    if aderencia['perdidos'] >= 2:
        intensidade = 'leve'
        intens_badge = '🟢 LEVE — Recuperação (ajuste por aderência baixa)'
        intens_cor = '#4ade80'
    elif tsb < -15:
        intensidade = 'leve'
        intens_badge = '🟢 LEVE — Recuperação'
        intens_cor = '#4ade80'
    elif tsb > 5:
        intensidade = 'forte'
        intens_badge = '🔴 FORTE — Overreach'
        intens_cor = '#f87171'
    else:
        intensidade = 'normal'
        intens_badge = '🟡 NORMAL — Construção'
        intens_cor = '#facc15'
    
    plano = plano_proxima_semana(intensidade)
    dias_pt = {'segunda': 'Segunda', 'terca': 'Terça', 'quarta': 'Quarta', 'quinta': 'Quinta',
               'sexta': 'Sexta', 'sabado': 'Sábado', 'domingo': 'Domingo'}
    
    prox_html = f'<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    prox_html += f'<div style="font-size:14px;font-weight:600;color:{intens_cor};margin-bottom:14px;">{intens_badge}</div>'
    
    for dk in ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']:
        if dk not in plano: continue
        tr = plano[dk]
        cat = tr['tipo']
        icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
        cor_tr = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
        
        prox_html += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor_tr};">'
        prox_html += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
        prox_html += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon} {dias_pt[dk]} <span style="color:#888;font-weight:400;margin-left:6px;">{tr["horario"]}</span></div>'
        prox_html += f'<div style="font-size:11px;color:#fbbf24;">{tr["nome"]} · {tr["dur_total"]}min</div>'
        prox_html += f'</div>'
        
        if cat == 'ciclismo':
            prox_html += '<div style="margin-top:8px;">'
            prox_html += '<div style="display:grid;grid-template-columns:170px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;"><div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
            
            for b in tr['blocos']:
                watts = watts_pct(b['pct_min'], b['pct_max'])
                pct_s = f"{int(b['pct_min']*100)}-{int(b['pct_max']*100)}%"
                fc_s = fc_zona_str(b['zona'])
                pavg = (b['pct_min'] + b['pct_max']) / 2
                
                if pavg < 0.55: cb = '#9ca3af'
                elif pavg < 0.75: cb = '#4ade80'
                elif pavg < 0.90: cb = '#facc15'
                elif pavg < 1.05: cb = '#fb923c'
                else: cb = '#f87171'
                
                prox_html += f'<div style="display:grid;grid-template-columns:170px 60px 1fr 1fr 90px;gap:8px;font-size:11px;padding:6px 8px;margin-bottom:2px;border-left:2px solid {cb};background:#0f0f0f;border-radius:3px;align-items:center;">'
                prox_html += f'<div style="color:#ddd;font-weight:500;">{b["nome"]}</div>'
                prox_html += f'<div style="color:#999;">{b["dur"]}min</div>'
                prox_html += f'<div style="color:{cb};font-weight:600;">{watts}</div>'
                prox_html += f'<div style="color:#999;">{pct_s}</div>'
                prox_html += f'<div style="color:#999;font-size:10px;">{b["zona"]} ({fc_s})</div>'
                prox_html += '</div>'
            prox_html += '</div>'
            
            pct_max_tr = max(b['pct_max'] for b in tr['blocos'])
            sups = calcular_suplementacao(tr['dur_total'], pct_max_tr)
            
            prox_html += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
            prox_html += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">🍌 Suplementação</div>'
            for e in sups:
                prox_html += f'<div style="font-size:11px;color:#ddd;padding:4px 0;">{e}</div>'
            prox_html += '</div>'
        else:
            for b in tr['blocos']:
                prox_html += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;"><strong>{b["nome"]}</strong> · {b["dur"]}min'
                if 'detalhes' in b: prox_html += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
                prox_html += '</div>'
        
        prox_html += '</div>'
    prox_html += '</div>'
    
    # ─── HTML completo ─────────────────────────────────────────────────────
    
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🚴 Strava Coach v9.4</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'DM Sans', -apple-system, sans-serif; background: #0a0a0a; color: #eee; padding: 20px; }}
.container {{ max-width: 1280px; margin: 0 auto; }}
.header {{ text-align: center; margin-bottom: 24px; }}
.header h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 4px; }}
.header p {{ color: #666; font-size: 13px; }}
.fitness-bar {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }}
.fc-card {{ background: #111; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #222; }}
.fc-card .label {{ font-size: 10px; color: #666; text-transform: uppercase; margin-bottom: 6px; }}
.fc-card .value {{ font-size: 22px; font-weight: 700; }}
.fc-card .sub {{ font-size: 10px; color: #555; margin-top: 4px; }}
.tabs {{ display: flex; gap: 6px; margin-bottom: 16px; border-bottom: 1px solid #222; }}
.tab {{ background: none; border: none; color: #888; padding: 10px 16px; font-size: 12px; font-weight: 600; cursor: pointer; border-radius: 8px 8px 0 0; }}
.tab.active {{ background: #1a1a1a; color: #fff; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.filtros {{ display: flex; gap: 12px; margin-bottom: 16px; padding: 12px; background: #111; border-radius: 10px; align-items: center; }}
.filtros label {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #ddd; cursor: pointer; }}
.filtros input[type="checkbox"] {{ cursor: pointer; width: 16px; height: 16px; }}
.filtros .label-title {{ font-size: 11px; color: #666; text-transform: uppercase; margin-right: 8px; }}
.treino-item.hidden {{ display: none; }}
.treino-header:hover {{ background: #0f0f0f; }}
.metric-btn {{ background: #1a1a1a; border: 1px solid #2a2a2a; color: #888; padding: 6px 12px; font-size: 11px; border-radius: 6px; cursor: pointer; }}
.metric-btn.active {{ background: #2a2a2a; color: #fff; border-color: #444; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
<h1>🚴 Strava Coach v9.4</h1>
<p>Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>

<div class="fitness-bar">
<div class="fc-card"><div class="label">CTL</div><div class="value" style="color:#3b82f6;">{ctl}</div></div>
<div class="fc-card"><div class="label">ATL</div><div class="value" style="color:#fb923c;">{atl}</div></div>
<div class="fc-card"><div class="label">TSB</div><div class="value" style="color:{cor_tsb};">{tsb}</div></div>
<div class="fc-card"><div class="label">FTP</div><div class="value">{FTP}W</div><div class="sub">{wkg} W/kg</div></div>
<div class="fc-card"><div class="label">Peso</div><div class="value">{PESO}</div><div class="sub">kg</div></div>
</div>

{analises_html}

<div class="tabs">
<button class="tab active" data-tab="historico">📅 Histórico</button>
<button class="tab" data-tab="wellness">📊 Condicionamento</button>
<button class="tab" data-tab="proxima">🎯 Próxima Semana</button>
</div>

<div id="historico" class="tab-content active">
{distrib_html}
<div class="filtros">
<span class="label-title">Filtrar:</span>
<label><input type="checkbox" class="filter-cat" data-cat="ciclismo" checked> 🚴 Ciclismo</label>
<label><input type="checkbox" class="filter-cat" data-cat="academia" checked> 🏋️ Academia</label>
<label><input type="checkbox" class="filter-cat" data-cat="outros" checked> 🏃 Outros</label>
</div>
{hist_html}
</div>

<div id="wellness" class="tab-content">{wellness_html}</div>
<div id="proxima" class="tab-content">{prox_html}</div>

</div>

<script>
const wellnessData = {hist_json};

document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'wellness') renderChart();
    }});
}});

document.querySelectorAll('.filter-cat').forEach(cb => {{
    cb.addEventListener('change', () => {{
        const cats = {{}};
        document.querySelectorAll('.filter-cat').forEach(c => {{ cats[c.dataset.cat] = c.checked; }});
        document.querySelectorAll('.treino-item').forEach(item => {{
            const cat = item.dataset.categoria;
            if (cats[cat]) item.classList.remove('hidden');
            else item.classList.add('hidden');
        }});
    }});
}});

function toggleTreino(uid) {{
    const el = document.getElementById(uid);
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}}

let chartInstance = null;

function renderChart() {{
    const ctx = document.getElementById('wellnessChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();
    
    const labels = wellnessData.map(d => d.data.slice(5));
    const datasets = [];
    
    // Encontrar índice onde começa forecast
    const forecastStart = wellnessData.findIndex(d => d.forecast);
    
    document.querySelectorAll('.metric-btn').forEach(btn => {{
        if (btn.classList.contains('active')) {{
            const metric = btn.dataset.metric;
            const color = btn.dataset.color;
            const label = btn.textContent;
            
            // Dados reais (até forecast)
            const dataReal = wellnessData.map((d, i) => i < forecastStart || forecastStart === -1 ? d[metric] : null);
            // Dados forecast (a partir de forecast)
            const dataForecast = wellnessData.map((d, i) => i >= forecastStart && forecastStart !== -1 ? d[metric] : null);
            
            datasets.push({{
                label: label,
                data: dataReal,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 0,
                yAxisID: metric === 'fc_avg' ? 'y1' : 'y'
            }});
            
            if (forecastStart !== -1) {{
                datasets.push({{
                    label: label + ' (Forecast)',
                    data: dataForecast,
                    borderColor: color,
                    backgroundColor: color + '10',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.3,
                    pointRadius: 3,
                    pointStyle: 'rectRot',
                    yAxisID: metric === 'fc_avg' ? 'y1' : 'y'
                }});
            }}
        }}
    }});
    
    chartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{ mode: 'index', intersect: false }},
            plugins: {{
                legend: {{ labels: {{ color: '#ddd', font: {{ size: 11 }}, filter: (item) => !item.text.includes('Forecast') }} }},
                tooltip: {{ backgroundColor: '#000', borderColor: '#444', borderWidth: 1 }},
                annotation: {{}}
            }},
            scales: {{
                x: {{ ticks: {{ color: '#666', maxRotation: 0, autoSkipPadding: 20 }}, grid: {{ color: '#1a1a1a' }} }},
                y: {{ type: 'linear', position: 'left', ticks: {{ color: '#666' }}, grid: {{ color: '#1a1a1a' }} }},
                y1: {{ type: 'linear', position: 'right', ticks: {{ color: '#ec4899' }}, grid: {{ drawOnChartArea: false }} }}
            }}
        }}
    }});
}}

document.querySelectorAll('.metric-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        btn.classList.toggle('active');
        if (document.getElementById('wellness').classList.contains('active')) renderChart();
    }});
}});
</script>

</body>
</html>'''
    
    return html

def main():
    print("🎨 Dashboard v9.4\n")
    treinos, wellness, fitness = load_data()
    print(f"✅ {len(treinos)} treinos\n")
    
    html = build_dashboard(treinos, wellness, fitness)
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ dashboard.html gerado ({len(html):,} bytes)")

if __name__ == '__main__':
    main()
