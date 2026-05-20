"""
🎨 DASHBOARD GENERATOR v10.0
- Aba 1: Semana Atual (Seg-Dom completo: realizados + planejados)
- Aba 2: Próxima Semana (Adaptativa híbrida: TSB + Aderência)
- Aba 3: Histórico (últimas semanas + condicionamento + distribuição)
- Estado persistido em data/estado.json
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# ─── Configuração Atleta ────────────────────────────────────────────────────

FTP = 210
PESO = 75.6
FC_MAX = 190
FC_REPOUSO = 39
META_CTL = 45
TSS_META_SEMANA = 420

ZONAS_FC = {
    'Z1': (115, 129),
    'Z2': (129, 145),
    'Z3': (145, 161),
    'Z4': (161, 176),
    'Z5': (176, 200),
}

# ─── Loaders ───────────────────────────────────────────────────────────────

def load_data():
    treinos, wellness, fitness, estado = {}, [], {'ctl': 36, 'atl': 54, 'tsb': -18}, {}
    if os.path.exists('data/treinos.json'):
        with open('data/treinos.json', 'r', encoding='utf-8') as f:
            treinos = json.load(f)
    if os.path.exists('data/wellness.json'):
        with open('data/wellness.json', 'r', encoding='utf-8') as f:
            wellness = json.load(f)
    if os.path.exists('data/fitness.json'):
        with open('data/fitness.json', 'r', encoding='utf-8') as f:
            fitness = json.load(f)
    if os.path.exists('data/estado.json'):
        with open('data/estado.json', 'r', encoding='utf-8') as f:
            estado = json.load(f)
    return treinos, wellness, fitness, estado

def save_estado(estado):
    os.makedirs('data', exist_ok=True)
    with open('data/estado.json', 'w', encoding='utf-8') as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

# ─── Zonas FC ──────────────────────────────────────────────────────────────

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

# ─── VO2max ────────────────────────────────────────────────────────────────

def vo2max_fc(fc_max=FC_MAX, fc_repouso=FC_REPOUSO):
    if fc_repouso <= 0: return 0
    return round(15 * (fc_max / fc_repouso), 1)

def vo2max_potencia(treinos):
    duas_sem = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    picos = [t.get('pico_5min', 0) for t in treinos.values()
             if t.get('data', '') >= duas_sem and t.get('pico_5min', 0) > 0]
    if not picos:
        return 0, 0
    melhor = max(picos)
    return round(16.6 + (8.87 * (melhor / PESO)), 1), melhor

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

# ─── Wellness + Forecast ───────────────────────────────────────────────────

def calcular_wellness_historico(treinos):
    """Histórico 60d real + 7d forecast"""
    tss_diario = defaultdict(float)
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        tss_diario[data] += tss_treino(t)

    hoje = datetime.now().date()
    historico = []
    ctl = atl = 0

    for i in range(60, -1, -1):
        data = (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        tss = tss_diario.get(data, 0)
        ctl = ctl + (tss - ctl) / 42
        atl = atl + (tss - atl) / 7
        historico.append({
            'data': data, 'ctl': round(ctl, 1), 'atl': round(atl, 1),
            'tsb': round(ctl - atl, 1), 'tss': round(tss, 1), 'forecast': False
        })

    # Forecast 7d
    plano_tss = {0: 100, 1: 0, 2: 100, 3: 0, 4: 100, 5: 200, 6: 30}
    ctl_fc, atl_fc = ctl, atl
    for i in range(1, 8):
        d = hoje + timedelta(days=i)
        tss_plan = plano_tss.get(d.weekday(), 0)
        ctl_fc = ctl_fc + (tss_plan - ctl_fc) / 42
        atl_fc = atl_fc + (tss_plan - atl_fc) / 7
        historico.append({
            'data': d.strftime('%Y-%m-%d'),
            'ctl': round(ctl_fc, 1), 'atl': round(atl_fc, 1),
            'tsb': round(ctl_fc - atl_fc, 1), 'tss': tss_plan, 'forecast': True
        })

    return historico

# ─── Plano semanal por intensidade ─────────────────────────────────────────

def gerar_plano_semana(intensidade):
    """Retorna dict com plano completo Seg-Dom"""
    if intensidade == 'leve':
        return {
            0: {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70, 'tss_alvo': 60,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            1: {'nome': 'Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            2: {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70, 'tss_alvo': 60,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            3: {'nome': 'Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            4: {'nome': 'Z2 Light', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 60, 'tss_alvo': 50,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 baixa', 'dur': 40, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            5: {'nome': 'Longo Z2 Suave', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 150, 'tss_alvo': 130,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Main Z2', 'dur': 120, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            6: {'nome': 'Descanso', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0, 'tss_alvo': 0,
                'blocos': [{'nome': 'Descanso total', 'dur': 0, 'detalhes': 'Recuperação completa'}]},
        }
    elif intensidade == 'forte':
        return {
            0: {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70, 'tss_alvo': 75,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.65, 'pct_max': 0.78, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            1: {'nome': 'Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            2: {'nome': 'VO2max 5x3min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 75, 'tss_alvo': 100,
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
            3: {'nome': 'Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            4: {'nome': 'Threshold 3x15min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 90, 'tss_alvo': 110,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '3º 15min FTP', 'dur': 15, 'pct_min': 0.93, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            5: {'nome': 'Longo + Sweet Spot', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 180, 'tss_alvo': 200,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Z2', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.75, 'zona': 'Z2'},
                    {'nome': 'Sweet Spot 1', 'dur': 20, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2 Recovery', 'dur': 10, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Sweet Spot 2', 'dur': 20, 'pct_min': 0.83, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            6: {'nome': 'Recuperação', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0, 'tss_alvo': 0,
                'blocos': [{'nome': 'Descanso ou caminhada leve', 'dur': 30, 'detalhes': 'Conforme TSB'}]},
        }
    else:  # normal
        return {
            0: {'nome': 'Z2 Endurance', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 70, 'tss_alvo': 70,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Endurance Z2', 'dur': 50, 'pct_min': 0.60, 'pct_max': 0.75, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            1: {'nome': 'Academia - Superiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro', 'dur': 60, 'detalhes': '4 séries 8-12 reps'}]},
            2: {'nome': 'Threshold 2x15min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 80, 'tss_alvo': 90,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.45, 'pct_max': 0.65, 'zona': 'Z1-Z2'},
                    {'nome': '1º 15min FTP', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.95, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 8, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2º 15min FTP', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.95, 'zona': 'Z4'},
                    {'nome': 'Z2', 'dur': 17, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]},
            3: {'nome': 'Academia - Inferiores', 'tipo': 'academia', 'horario': '—', 'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento, leg press, stiff'}]},
            4: {'nome': 'Sweet Spot 3x10min', 'tipo': 'ciclismo', 'horario': '05:30', 'dur_total': 80, 'tss_alvo': 85,
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
            5: {'nome': 'Longo Z2', 'tipo': 'ciclismo', 'horario': '07:00', 'dur_total': 180, 'tss_alvo': 175,
                'blocos': [
                    {'nome': 'Warmup', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1-Z2'},
                    {'nome': 'Endurance Z2', 'dur': 150, 'pct_min': 0.65, 'pct_max': 0.78, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
                ]},
            6: {'nome': 'Recuperação Ativa', 'tipo': 'recuperacao', 'horario': '—', 'dur_total': 0, 'tss_alvo': 0,
                'blocos': [{'nome': 'Descanso ou caminhada', 'dur': 30, 'detalhes': 'Conforme TSB'}]},
        }

# ─── Análise da Semana Atual ───────────────────────────────────────────────

def analisar_semana_atual(treinos, intensidade_planejada):
    """
    Para cada dia Seg-Dom da semana atual, retorna:
    - O treino planejado
    - O treino realizado (se houver)
    - Status: realizado/parcial/perdido/futuro
    """
    hoje = datetime.now()
    seg_atual = hoje - timedelta(days=hoje.weekday())
    seg_atual = seg_atual.replace(hour=0, minute=0, second=0, microsecond=0)

    plano = gerar_plano_semana(intensidade_planejada)

    # Mapear realizados
    realizados_por_dia = defaultdict(list)
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            if dt >= seg_atual and dt < seg_atual + timedelta(days=7):
                realizados_por_dia[dt.weekday()].append(t)
        except: continue

    resultado = []
    tss_realizado_total = 0
    tss_alvo_total = 0
    treinos_planejados_cic = 0
    treinos_perdidos = 0
    treinos_feitos = 0

    for wd in range(7):
        plan = plano[wd]
        dia_dt = seg_atual + timedelta(days=wd)
        realizados = realizados_por_dia.get(wd, [])
        tss_real_dia = sum(tss_treino(t) for t in realizados)

        tss_realizado_total += tss_real_dia
        tss_alvo_total += plan.get('tss_alvo', 0)

        if plan['tipo'] == 'ciclismo':
            treinos_planejados_cic += 1

        # Status
        is_passado = dia_dt.date() < hoje.date()
        is_hoje = dia_dt.date() == hoje.date()
        is_futuro = dia_dt.date() > hoje.date()

        if is_futuro:
            status = 'futuro'
            icone = '⏳'
            cor_status = '#6b7280'
        elif realizados:
            cats_real = [t.get('categoria') for t in realizados]
            if plan['tipo'] in cats_real or plan['tipo'] == 'recuperacao':
                status = 'realizado'
                icone = '✅'
                cor_status = '#4ade80'
                if plan['tipo'] == 'ciclismo': treinos_feitos += 1
            else:
                status = 'parcial'
                icone = '⚠️'
                cor_status = '#facc15'
        elif plan['tipo'] == 'recuperacao':
            status = 'realizado'
            icone = '✅'
            cor_status = '#4ade80'
        elif is_hoje:
            status = 'hoje'
            icone = '🎯'
            cor_status = '#3b82f6'
        else:
            status = 'perdido'
            icone = '❌'
            cor_status = '#f87171'
            if plan['tipo'] == 'ciclismo': treinos_perdidos += 1

        resultado.append({
            'weekday': wd,
            'data': dia_dt.strftime('%Y-%m-%d'),
            'plano': plan,
            'realizados': realizados,
            'tss_real': round(tss_real_dia, 1),
            'tss_alvo': plan.get('tss_alvo', 0),
            'status': status,
            'icone': icone,
            'cor_status': cor_status,
            'is_hoje': is_hoje,
            'is_passado': is_passado,
        })

    # Aderência (só conta dias passados ou hoje)
    dias_avaliados = sum(1 for r in resultado if not r['is_passado'] is False or r['is_hoje'])
    treinos_cic_avaliados = sum(1 for r in resultado
                                if (r['is_passado'] or r['is_hoje'])
                                and r['plano']['tipo'] == 'ciclismo')

    if treinos_cic_avaliados > 0:
        feitos_ate_agora = sum(1 for r in resultado
                              if (r['is_passado'] or r['is_hoje'])
                              and r['plano']['tipo'] == 'ciclismo'
                              and r['status'] == 'realizado')
        aderencia_pct = round((feitos_ate_agora / treinos_cic_avaliados) * 100)
    else:
        aderencia_pct = 100

    return {
        'dias': resultado,
        'tss_realizado': round(tss_realizado_total, 1),
        'tss_alvo': tss_alvo_total,
        'tss_pct': round((tss_realizado_total / tss_alvo_total) * 100) if tss_alvo_total > 0 else 0,
        'aderencia_pct': aderencia_pct,
        'treinos_perdidos': treinos_perdidos,
        'treinos_feitos': treinos_feitos,
        'treinos_planejados_cic': treinos_planejados_cic,
        'seg_atual': seg_atual.strftime('%Y-%m-%d')
    }

# ─── Decisão da Próxima Semana (HÍBRIDO TSB + Aderência) ──────────────────

def decidir_intensidade_proxima(tsb, aderencia_pct, treinos_perdidos):
    """
    Combinação inteligente TSB + Aderência:

    - Se perdeu 2+ treinos OU aderência < 60% → LEVE (recuperação obrigatória)
    - Se TSB < -25 (fadiga extrema) → LEVE
    - Se TSB > 10 E aderência > 85% → FORTE (forma + consistência)
    - Se TSB > 5 E aderência > 75% → FORTE
    - Padrão → NORMAL
    """
    razao = []

    # Forçar leve por aderência baixa
    if treinos_perdidos >= 2:
        return 'leve', f'⚠️ {treinos_perdidos} treinos perdidos esta semana — recuperação necessária', '#4ade80'

    if aderencia_pct < 60:
        return 'leve', f'⚠️ Aderência baixa ({aderencia_pct}%) — semana de retomada', '#4ade80'

    # Forçar leve por fadiga extrema
    if tsb < -25:
        return 'leve', f'🔴 TSB {tsb:.0f} — Fadiga crítica, recuperação obrigatória', '#4ade80'

    # Forte por boa forma + aderência
    if tsb > 10 and aderencia_pct >= 85:
        return 'forte', f'🟢 Forma ótima (TSB +{tsb:.0f}) + aderência alta ({aderencia_pct}%) — pode acelerar', '#f87171'

    if tsb > 5 and aderencia_pct >= 75:
        return 'forte', f'🟢 Forma boa (TSB +{tsb:.0f}) + consistente ({aderencia_pct}%) — semana de overreach', '#f87171'

    # Normal padrão
    return 'normal', f'⚖️ TSB {tsb:.0f} + Aderência {aderencia_pct}% — Construção equilibrada', '#facc15'

# ─── Suplementação ─────────────────────────────────────────────────────────

def calcular_suplementacao(dur_min):
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

# ─── Distribuição de Zonas ─────────────────────────────────────────────────

def calcular_distribuicao(treinos):
    quatro_sem = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')
    tempo_zona = defaultdict(float)

    for t in treinos.values():
        if t.get('categoria') != 'ciclismo': continue
        if t.get('data', '') < quatro_sem: continue
        dur = t.get('duracao_min', 0)
        laps = t.get('laps', [])
        if laps:
            for lap in laps:
                zona = lap.get('zona', '—')
                if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
                    tempo_zona[zona] += lap.get('dur_min', 0)
        else:
            zona = zona_treino(t)
            if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
                tempo_zona[zona] += dur

    total = sum(tempo_zona.values())
    if total == 0: return None

    pcts = {z: round((tempo_zona[z] / total) * 100, 1) for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']}
    baixa = pcts['Z1'] + pcts['Z2']
    media = pcts['Z3']
    alta = pcts['Z4'] + pcts['Z5']

    if baixa >= 75 and alta >= 10 and media <= 15:
        modelo, cor = '🎯 Polarizado 80/20', '#10b981'
        desc = 'Distribuição ideal: muito Z2 + intervalados Z4/Z5'
    elif media >= 30:
        modelo, cor = '⚠️ Piramidal (excesso Z3)', '#facc15'
        desc = 'Muito Z3 (sweet spot). Pode causar fadiga acumulada'
    elif baixa >= 90:
        modelo, cor = '📉 Sub-polarizado', '#9ca3af'
        desc = 'Falta intensidade. Adicione intervalados Z4/Z5'
    else:
        modelo, cor = '⚖️ Equilibrado', '#3b82f6'
        desc = 'Distribuição mista'

    return {'pcts': pcts, 'total_min': round(total), 'modelo': modelo, 'cor': cor,
            'descricao': desc, 'baixa': baixa, 'media': media, 'alta': alta}

# ─── Previsão FTP ──────────────────────────────────────────────────────────

def prever_ftp(treinos):
    cic = [t for t in treinos.values() if t.get('categoria') == 'ciclismo' and t.get('potencia_avg', 0) > 50]
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
    mx, my = sum(x) / n, sum(scores) / n
    num = sum((x[i] - mx) * (scores[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den == 0: return None, None, None

    slope = num / den
    ganho = slope * 0.3
    if ganho <= 0: return None, None, None
    return 220 - FTP, round((220 - FTP) / ganho), round(ganho, 1)

# ─── Helpers UI ────────────────────────────────────────────────────────────

def watts_pct(pmin, pmax):
    return f"{int(FTP * pmin)}-{int(FTP * pmax)}W"

def fc_zona_str(z):
    if z in ZONAS_FC:
        lo, hi = ZONAS_FC[z]
        return f"{lo}-{hi}bpm"
    return "—"

def cor_zona(z):
    return {'Z1': '#9ca3af', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}.get(z, '#888')

# ─── HTML BUILDERS ─────────────────────────────────────────────────────────

def build_bloco_treino(b):
    watts = watts_pct(b['pct_min'], b['pct_max'])
    pct_s = f"{int(b['pct_min']*100)}-{int(b['pct_max']*100)}%"
    fc_s = fc_zona_str(b['zona'])
    pavg = (b['pct_min'] + b['pct_max']) / 2

    if pavg < 0.55: cb = '#9ca3af'
    elif pavg < 0.75: cb = '#4ade80'
    elif pavg < 0.90: cb = '#facc15'
    elif pavg < 1.05: cb = '#fb923c'
    else: cb = '#f87171'

    h = f'<div style="display:grid;grid-template-columns:170px 60px 1fr 1fr 90px;gap:8px;font-size:11px;padding:6px 8px;margin-bottom:2px;border-left:2px solid {cb};background:#0f0f0f;border-radius:3px;align-items:center;">'
    h += f'<div style="color:#ddd;font-weight:500;">{b["nome"]}</div>'
    h += f'<div style="color:#999;">{b["dur"]}min</div>'
    h += f'<div style="color:{cb};font-weight:600;">{watts}</div>'
    h += f'<div style="color:#999;">{pct_s}</div>'
    h += f'<div style="color:#999;font-size:10px;">{b["zona"]} ({fc_s})</div>'
    h += '</div>'
    return h

def build_treino_realizado_inline(t, uid):
    """Card de treino realizado (compacto, expansível)"""
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

    h = f'<div class="treino-item" data-categoria="{cat}" style="background:#0a0a0a;border-radius:6px;margin-bottom:6px;border-left:3px solid {cor_cat};overflow:hidden;">'
    h += f'<div class="treino-header" onclick="toggleTreino(\'{uid}\')" style="padding:10px 12px;cursor:pointer;user-select:none;">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
    h += f'<div style="font-size:12px;color:#ddd;"><span style="font-size:14px;">{icon}</span> <strong>{t.get("nome", "Sem nome")}</strong> <span style="color:#666;font-weight:400;font-size:10px;margin-left:6px;">▼</span></div>'
    h += f'<div style="font-size:10px;color:#666;">Nota: {nota}/10 · TSS: {tss_t}</div>'
    h += f'</div>'
    h += f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;font-size:10px;color:#888;">'
    h += f'<div>Zona<br><span style="color:#ddd;font-weight:600;">{zona}</span></div>'
    h += f'<div>Dist<br><span style="color:#ddd;font-weight:600;">{t.get("distancia_km", 0)}km</span></div>'
    h += f'<div>Tempo<br><span style="color:#ddd;font-weight:600;">{int(t.get("duracao_min", 0))}min</span></div>'
    h += f'<div>Watts<br><span style="color:#ddd;font-weight:600;">{int(t.get("potencia_avg", 0))}W</span></div>'
    h += f'<div>FC<br><span style="color:#ddd;font-weight:600;">{int(t.get("fc_avg", 0))}bpm</span></div>'
    h += f'</div></div>'

    h += f'<div id="{uid}" class="treino-details" style="display:none;padding:12px;background:#050505;border-top:1px solid #1a1a1a;">'

    if cat == 'ciclismo':
        h += '<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">📊 Métricas</div>'
        h += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">'
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
            h += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;margin-bottom:4px;">{lbl}</div><div style="font-size:14px;font-weight:700;color:{c};">{val}</div></div>'
        h += '</div>'

        if laps_t and len(laps_t) > 1:
            h += f'<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">🔄 Voltas ({len(laps_t)})</div>'
            h += '<div style="background:#0a0a0a;border-radius:6px;overflow:hidden;">'
            h += '<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;background:#1a1a1a;font-size:10px;color:#666;text-transform:uppercase;">'
            h += '<div>#</div><div>Nome</div><div>Tempo</div><div>Dist</div><div>Watts</div><div>Máx</div><div>FC</div><div>Zona</div></div>'
            for lap in laps_t:
                zl = lap.get('zona', '—')
                cz = cor_zona(zl)
                ds = lap.get('dur_seg', 0)
                ts = f"{ds//3600}h{(ds%3600)//60:02d}m" if ds >= 3600 else f"{ds//60}m{ds%60:02d}s"
                h += f'<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;border-top:1px solid #1a1a1a;font-size:11px;align-items:center;">'
                h += f'<div style="color:#666;font-weight:600;">{lap.get("idx", "—")}</div>'
                h += f'<div style="color:#ddd;">{lap.get("nome", "")[:30]}</div>'
                h += f'<div style="color:#999;">{ts}</div>'
                h += f'<div style="color:#999;">{lap.get("dist_km", 0)}km</div>'
                h += f'<div style="color:#ddd;font-weight:600;">{lap.get("pot_avg", 0)}W</div>'
                h += f'<div style="color:#999;font-size:10px;">{lap.get("pot_max", 0)}W</div>'
                h += f'<div style="color:#ddd;">{lap.get("fc_avg", 0)}bpm</div>'
                h += f'<div style="color:{cz};font-weight:600;">{zl}</div>'
                h += '</div>'
            h += '</div>'
    else:
        h += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">'
        h += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">CATEGORIA</div><div style="font-size:14px;font-weight:700;">{cat.upper()}</div></div>'
        h += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">TIPO</div><div style="font-size:14px;font-weight:700;">{t.get("tipo", "—")}</div></div>'
        h += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;">FC MÁX</div><div style="font-size:14px;font-weight:700;color:#ef4444;">{int(t.get("fc_max", 0))}bpm</div></div>'
        h += '</div>'

    h += '</div></div>'
    return h

def build_dia_semana_atual(dia_info, idx):
    """Card de um dia da semana atual: planejado + realizado"""
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    plan = dia_info['plano']
    realizados = dia_info['realizados']
    status = dia_info['status']
    icone = dia_info['icone']
    cor_status = dia_info['cor_status']
    is_hoje = dia_info['is_hoje']

    cat = plan['tipo']
    icon_cat = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
    cor_cat = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')

    border_extra = 'box-shadow: 0 0 0 2px #3b82f6;' if is_hoje else ''

    h = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor_cat};{border_extra}">'

    # Header do dia
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">'
    h += f'<div style="display:flex;align-items:center;gap:8px;">'
    h += f'<span style="font-size:18px;">{icone}</span>'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon_cat} {dias_pt[dia_info["weekday"]]}'
    if is_hoje: h += ' <span style="color:#3b82f6;font-size:10px;margin-left:4px;">▶ HOJE</span>'
    h += f' <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div>'
    h += f'</div>'
    h += f'<div style="display:flex;gap:8px;align-items:center;">'
    h += f'<span style="font-size:10px;color:{cor_status};font-weight:600;padding:3px 8px;background:{cor_status}22;border-radius:4px;">{status.upper()}</span>'
    h += f'<span style="font-size:11px;color:#fbbf24;">{plan["nome"]}</span>'
    h += f'</div>'
    h += f'</div>'

    # TSS planejado vs realizado
    if plan.get('tss_alvo', 0) > 0 or dia_info['tss_real'] > 0:
        tss_real = dia_info['tss_real']
        tss_alvo = plan.get('tss_alvo', 0)
        pct = round((tss_real / tss_alvo) * 100) if tss_alvo > 0 else (100 if tss_real > 0 else 0)
        pct_bar = min(pct, 150)
        cor_tss = '#4ade80' if 80 <= pct <= 120 else ('#facc15' if 50 <= pct <= 140 else ('#f87171' if pct > 0 else '#6b7280'))

        h += f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;font-size:11px;">'
        h += f'<div style="color:#666;">TSS:</div>'
        h += f'<div style="color:#ddd;font-weight:600;">{int(tss_real)} / {tss_alvo}</div>'
        h += f'<div style="flex:1;background:#1a1a1a;height:6px;border-radius:3px;overflow:hidden;"><div style="background:{cor_tss};height:100%;width:{pct_bar}%;"></div></div>'
        h += f'<div style="color:{cor_tss};font-weight:700;">{pct}%</div>'
        h += f'</div>'

    # Treinos realizados (se houver)
    if realizados:
        h += '<div style="margin-top:10px;">'
        h += '<div style="font-size:10px;color:#4ade80;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">✅ Realizado</div>'
        for j, t in enumerate(realizados):
            uid = f"atual-{idx}-{j}"
            h += build_treino_realizado_inline(t, uid)
        h += '</div>'

    # Plano (mostra se ainda não realizou OU se é futuro)
    mostrar_plano = (status in ['futuro', 'hoje', 'perdido', 'parcial']) and cat == 'ciclismo'

    if mostrar_plano:
        h += '<div style="margin-top:10px;">'
        if status == 'realizado':
            h += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">📋 Plano original</div>'
        else:
            h += '<div style="font-size:10px;color:#fbbf24;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">📋 Plano</div>'

        h += '<div style="display:grid;grid-template-columns:170px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;">'
        h += '<div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'

        for b in plan['blocos']:
            h += build_bloco_treino(b)
        h += '</div>'

        # Suplementação se for hoje
        if is_hoje and cat == 'ciclismo':
            sups = calcular_suplementacao(plan['dur_total'])
            h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
            h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">🍌 Suplementação</div>'
            for e in sups:
                h += f'<div style="font-size:11px;color:#ddd;padding:4px 0;">{e}</div>'
            h += '</div>'

    elif cat == 'academia' and not realizados:
        for b in plan['blocos']:
            h += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;margin-top:6px;">'
            h += f'<strong>{b["nome"]}</strong> · {b["dur"]}min'
            if 'detalhes' in b: h += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
            h += '</div>'

    h += '</div>'
    return h

def build_dia_proxima_semana(wd, plan):
    """Card de um dia da próxima semana (só plano)"""
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    cat = plan['tipo']
    icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
    cor = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')

    h = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor};">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon} {dias_pt[wd]} <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div>'
    h += f'<div style="font-size:11px;color:#fbbf24;">{plan["nome"]} · {plan["dur_total"]}min · TSS {plan.get("tss_alvo", 0)}</div>'
    h += f'</div>'

    if cat == 'ciclismo':
        h += '<div style="display:grid;grid-template-columns:170px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;">'
        h += '<div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
        for b in plan['blocos']:
            h += build_bloco_treino(b)

        sups = calcular_suplementacao(plan['dur_total'])
        h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
        h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">🍌 Suplementação</div>'
        for e in sups:
            h += f'<div style="font-size:11px;color:#ddd;padding:4px 0;">{e}</div>'
        h += '</div>'
    else:
        for b in plan['blocos']:
            h += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;margin-top:6px;">'
            h += f'<strong>{b["nome"]}</strong> · {b["dur"]}min'
            if 'detalhes' in b: h += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
            h += '</div>'

    h += '</div>'
    return h

# ─── Build Dashboard ───────────────────────────────────────────────────────

def build_dashboard(treinos, wellness, fitness, estado):
    treinos_list = sorted(treinos.values(), key=lambda x: x.get('data', ''), reverse=True)
    cic = sum(1 for t in treinos_list if t.get('categoria') == 'ciclismo')
    acad = sum(1 for t in treinos_list if t.get('categoria') == 'academia')

    ftp_gap, sem_220, ganho_ftp = prever_ftp(treinos)
    wkg = round(FTP / PESO, 2)

    historico = calcular_wellness_historico(treinos)
    distrib = calcular_distribuicao(treinos)

    # VO2max
    vo2_fc = vo2max_fc(FC_MAX, FC_REPOUSO)
    vo2_pot, melhor_5min = vo2max_potencia(treinos)
    label_fc, cor_fc = classificar_vo2(vo2_fc)
    label_pot, cor_pot = classificar_vo2(vo2_pot)

    # Estado: intensidade da semana atual (default normal)
    intensidade_atual = estado.get('intensidade_atual', 'normal')

    # Análise semana atual
    analise = analisar_semana_atual(treinos, intensidade_atual)

    # Wellness atual
    ultimos_reais = [h for h in historico if not h.get('forecast')]
    ultimo = ultimos_reais[-1] if ultimos_reais else {'ctl': 36, 'atl': 54, 'tsb': -18, 'tss': 0}
    ctl, atl, tsb = ultimo['ctl'], ultimo['atl'], ultimo['tsb']

    if tsb < -30: cor_tsb = '#f87171'
    elif tsb < -10: cor_tsb = '#fbbf24'
    elif tsb < 5: cor_tsb = '#9ca3af'
    else: cor_tsb = '#4ade80'

    # Decisão Próxima Semana (HÍBRIDO)
    intens_prox, razao_prox, cor_prox = decidir_intensidade_proxima(
        tsb, analise['aderencia_pct'], analise['treinos_perdidos']
    )

    plano_proxima = gerar_plano_semana(intens_prox)

    # ─── Cards superiores ──────────────────────────────────────────────────
    cards_analise = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px;">'

    ctl_pct = min(round((ctl / META_CTL) * 100), 100)

    if ftp_gap and sem_220:
        cards_analise += f'''<div style="background:linear-gradient(135deg,#3b82f6,#1e40af);padding:16px;border-radius:10px;color:white;">
<div style="font-size:12px;opacity:0.9;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">📈 Previsão FTP</div>
<div style="font-size:24px;font-weight:700;margin-bottom:6px;">+{int(ftp_gap)}W</div>
<div style="font-size:11px;opacity:0.95;">FTP 220W em ~<strong>{sem_220} sem</strong> · +{ganho_ftp}W/sem</div>
</div>'''

    cards_analise += f'''<div style="background:linear-gradient(135deg,#ec4899,#be185d);padding:16px;border-radius:10px;color:white;">
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

    cards_vo2 = f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
<div style="background:#111;padding:16px;border-radius:10px;border:1px solid #222;">
<div style="font-size:12px;color:#666;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🫁 VO₂max (FC)</div>
<div style="font-size:28px;font-weight:700;color:{cor_fc};">{vo2_fc} <span style="font-size:14px;color:#666;">ml/kg/min</span></div>
<div style="font-size:11px;color:#888;margin-top:4px;">15 × ({FC_MAX}/{FC_REPOUSO})</div>
<div style="font-size:11px;color:{cor_fc};margin-top:6px;font-weight:600;">{label_fc}</div>
</div>
<div style="background:#111;padding:16px;border-radius:10px;border:1px solid #222;">
<div style="font-size:12px;color:#666;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">🫁 VO₂max (Potência 5min)</div>
<div style="font-size:28px;font-weight:700;color:{cor_pot};">{vo2_pot if vo2_pot > 0 else "—"} <span style="font-size:14px;color:#666;">ml/kg/min</span></div>
<div style="font-size:11px;color:#888;margin-top:4px;">16.6 + 8.87×{round(melhor_5min/PESO, 2) if melhor_5min > 0 else "—"} · Pico: {melhor_5min}W</div>
<div style="font-size:11px;color:{cor_pot};margin-top:6px;font-weight:600;">{label_pot if vo2_pot > 0 else "Dados insuficientes"}</div>
</div>
</div>'''

    # ─── ABA 1: Semana Atual ───────────────────────────────────────────────

    seg_dt = datetime.strptime(analise['seg_atual'], '%Y-%m-%d')
    dom_dt = seg_dt + timedelta(days=6)

    cor_ader = '#4ade80' if analise['aderencia_pct'] >= 80 else ('#facc15' if analise['aderencia_pct'] >= 60 else '#f87171')
    cor_tss_sem = '#4ade80' if 80 <= analise['tss_pct'] <= 120 else ('#facc15' if 60 <= analise['tss_pct'] <= 140 else ('#f87171' if analise['tss_pct'] > 0 else '#6b7280'))

    pct_bar_tss = min(analise['tss_pct'], 150)

    aba_atual = f'<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aba_atual += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">'
    aba_atual += f'<div>'
    aba_atual += f'<h3 style="font-size:15px;color:#fff;margin-bottom:2px;">📅 Semana Atual</h3>'
    aba_atual += f'<div style="font-size:11px;color:#666;">{seg_dt.strftime("%d/%m")} — {dom_dt.strftime("%d/%m")} · Intensidade: <span style="color:#fbbf24;font-weight:600;">{intensidade_atual.upper()}</span></div>'
    aba_atual += f'</div>'
    aba_atual += f'<div style="display:flex;gap:14px;align-items:center;">'
    aba_atual += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Aderência</div><div style="font-size:22px;font-weight:700;color:{cor_ader};">{analise["aderencia_pct"]}%</div></div>'
    aba_atual += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Treinos</div><div style="font-size:22px;font-weight:700;color:#3b82f6;">{analise["treinos_feitos"]}/{analise["treinos_planejados_cic"]}</div></div>'
    aba_atual += f'</div>'
    aba_atual += f'</div>'

    # Barra TSS semanal
    aba_atual += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;margin-bottom:14px;">'
    aba_atual += f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:11px;">'
    aba_atual += f'<div style="color:#666;text-transform:uppercase;letter-spacing:1px;font-weight:600;">📊 TSS Semana</div>'
    aba_atual += f'<div><span style="color:{cor_tss_sem};font-weight:700;">{int(analise["tss_realizado"])}</span><span style="color:#666;"> / {analise["tss_alvo"]} ({analise["tss_pct"]}%)</span></div>'
    aba_atual += f'</div>'
    aba_atual += f'<div style="background:#1a1a1a;height:10px;border-radius:5px;overflow:hidden;"><div style="background:{cor_tss_sem};height:100%;width:{pct_bar_tss}%;transition:width 0.3s;"></div></div>'
    aba_atual += f'</div>'

    # Dias da semana
    for idx, dia in enumerate(analise['dias']):
        aba_atual += build_dia_semana_atual(dia, idx)

    aba_atual += '</div>'

    # ─── ABA 2: Próxima Semana ─────────────────────────────────────────────

    prox_seg_dt = seg_dt + timedelta(days=7)
    prox_dom_dt = prox_seg_dt + timedelta(days=6)

    tss_total_proxima = sum(p.get('tss_alvo', 0) for p in plano_proxima.values())

    aba_prox = f'<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aba_prox += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">'
    aba_prox += f'<div>'
    aba_prox += f'<h3 style="font-size:15px;color:#fff;margin-bottom:2px;">🎯 Próxima Semana</h3>'
    aba_prox += f'<div style="font-size:11px;color:#666;">{prox_seg_dt.strftime("%d/%m")} — {prox_dom_dt.strftime("%d/%m")}</div>'
    aba_prox += f'</div>'
    aba_prox += f'<div style="display:flex;gap:12px;align-items:center;">'
    aba_prox += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">TSS Total</div><div style="font-size:20px;font-weight:700;color:#3b82f6;">{tss_total_proxima}</div></div>'
    aba_prox += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Intensidade</div><div style="font-size:14px;font-weight:700;color:{cor_prox};padding:4px 10px;background:{cor_prox}22;border-radius:6px;">{intens_prox.upper()}</div></div>'
    aba_prox += f'</div>'
    aba_prox += f'</div>'

    # Razão da decisão
    aba_prox += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;margin-bottom:14px;border-left:3px solid {cor_prox};">'
    aba_prox += f'<div style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">🤖 Lógica de Decisão</div>'
    aba_prox += f'<div style="font-size:12px;color:#ddd;line-height:1.5;">{razao_prox}</div>'
    aba_prox += f'<div style="font-size:10px;color:#666;margin-top:8px;">Baseado em: TSB ({tsb:+.1f}) + Aderência ({analise["aderencia_pct"]}%) + Treinos perdidos ({analise["treinos_perdidos"]})</div>'
    aba_prox += f'</div>'

    # Botão confirmar (salva no estado.json via download)
    aba_prox += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;margin-bottom:14px;border:1px dashed #444;">'
    aba_prox += f'<div style="font-size:11px;color:#666;margin-bottom:8px;">💾 Estado atual: <strong style="color:#ddd;">{intensidade_atual.upper()}</strong> → Próxima sugerida: <strong style="color:{cor_prox};">{intens_prox.upper()}</strong></div>'
    aba_prox += f'<div style="font-size:10px;color:#888;line-height:1.5;">Quando a semana virar (próxima segunda), o estado será automaticamente atualizado. A intensidade pode mudar conforme você executa os treinos durante a semana.</div>'
    aba_prox += f'</div>'

    # Dias da próxima semana
    for wd in range(7):
        aba_prox += build_dia_proxima_semana(wd, plano_proxima[wd])

    aba_prox += '</div>'

    # ─── ABA 3: Histórico ──────────────────────────────────────────────────

    por_semana_hist = defaultdict(list)
    for t in treinos_list:
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            week = (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
            # Pula semana atual (já está na aba 1)
            if week == analise['seg_atual']: continue
            por_semana_hist[week].append(t)
        except: pass

    sem_ord = sorted(por_semana_hist.keys(), reverse=True)

    aba_hist = ''

    # Distribuição
    if distrib:
        aba_hist += '<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
        aba_hist += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        aba_hist += '<h3 style="font-size:14px;color:#fff;">🎯 Distribuição de Zonas (últimas 4 semanas)</h3>'
        aba_hist += f'<div style="font-size:12px;color:{distrib["cor"]};font-weight:600;">{distrib["modelo"]}</div>'
        aba_hist += '</div>'
        aba_hist += f'<div style="font-size:11px;color:#888;margin-bottom:14px;">{distrib["descricao"]}</div>'
        aba_hist += '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">'
        for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
            pct = distrib['pcts'][z]
            min_z = int((pct / 100) * distrib['total_min'])
            cz = cor_zona(z)
            aba_hist += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;">'
            aba_hist += f'<div style="font-size:11px;color:{cz};font-weight:600;margin-bottom:4px;">{z}</div>'
            aba_hist += f'<div style="font-size:18px;font-weight:700;color:#fff;">{pct}%</div>'
            aba_hist += f'<div style="font-size:9px;color:#666;margin-top:2px;">{min_z}min</div>'
            aba_hist += f'<div style="background:#1a1a1a;height:3px;border-radius:2px;margin-top:6px;"><div style="background:{cz};height:100%;width:{pct}%;border-radius:2px;"></div></div>'
            aba_hist += '</div>'
        aba_hist += '</div>'
        aba_hist += f'<div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:11px;">'
        aba_hist += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Baixa:</span> <strong style="color:#4ade80;">{distrib["baixa"]:.0f}%</strong></div>'
        aba_hist += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Média (Z3):</span> <strong style="color:#facc15;">{distrib["media"]:.0f}%</strong></div>'
        aba_hist += f'<div style="background:#0a0a0a;padding:8px;border-radius:6px;text-align:center;"><span style="color:#666;">Alta:</span> <strong style="color:#f87171;">{distrib["alta"]:.0f}%</strong></div>'
        aba_hist += '</div>'
        aba_hist += '</div>'

    # Filtros
    aba_hist += '<div class="filtros">'
    aba_hist += '<span class="label-title">Filtrar:</span>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="ciclismo" checked> 🚴 Ciclismo</label>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="academia" checked> 🏋️ Academia</label>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="outros" checked> 🏃 Outros</label>'
    aba_hist += '</div>'

    # Semanas históricas
    for week in sem_ord[:8]:
        t_sem = por_semana_hist[week]
        dt_seg = datetime.strptime(week, '%Y-%m-%d')
        dt_dom = dt_seg + timedelta(days=6)
        label = f"{dt_seg.strftime('%d/%m')} — {dt_dom.strftime('%d/%m')}"

        tss_total = sum(tss_treino(t) for t in t_sem)
        if 380 <= tss_total <= 460:
            tss_cor, tss_label = '#4ade80', '✅ Ideal'
        elif tss_total < 250:
            tss_cor, tss_label = '#9ca3af', '📉 Baixa'
        elif tss_total < 380:
            tss_cor, tss_label = '#facc15', '⚖️ Moderada'
        elif tss_total <= 550:
            tss_cor, tss_label = '#fb923c', '🔥 Alta'
        else:
            tss_cor, tss_label = '#f87171', '⚠️ Excesso'

        aba_hist += f'<div style="background:#111;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #222;">'
        aba_hist += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">'
        aba_hist += f'<div style="font-size:13px;font-weight:600;color:#ddd;">{label}<span style="color:#666;font-weight:400;margin-left:10px;">{len(t_sem)} treinos</span></div>'
        aba_hist += f'<div style="display:flex;gap:10px;align-items:center;">'
        aba_hist += f'<div style="font-size:11px;color:#666;">TSS:</div>'
        aba_hist += f'<div style="font-size:18px;font-weight:700;color:{tss_cor};">{int(tss_total)}</div>'
        aba_hist += f'<div style="font-size:10px;color:{tss_cor};font-weight:600;padding:2px 8px;background:{tss_cor}22;border-radius:4px;">{tss_label}</div>'
        aba_hist += f'<div style="font-size:10px;color:#666;">/ Meta {TSS_META_SEMANA}</div>'
        aba_hist += f'</div></div>'

        for idx_t, t in enumerate(t_sem):
            uid = f"hist-{week}-{idx_t}"
            aba_hist += build_treino_realizado_inline(t, uid)

        aba_hist += '</div>'

    # ─── ABA 4: Condicionamento ────────────────────────────────────────────

    hist_json = json.dumps(historico)

    aba_cond = '<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aba_cond += f'<h3 style="font-size:14px;color:#fff;margin-bottom:6px;">📊 Condicionamento</h3>'
    aba_cond += f'<div style="font-size:11px;color:#666;margin-bottom:14px;">Último dia real: {ultimo["data"]} · Forecast 7 dias incluso</div>'

    aba_cond += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">'
    aba_cond += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">CTL (Fitness)</div><div style="font-size:22px;font-weight:700;color:#3b82f6;">{ultimo["ctl"]}</div></div>'
    aba_cond += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">ATL (Fadiga)</div><div style="font-size:22px;font-weight:700;color:#fb923c;">{ultimo["atl"]}</div></div>'
    aba_cond += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">TSB (Forma)</div><div style="font-size:22px;font-weight:700;color:{cor_tsb};">{ultimo["tsb"]}</div></div>'
    aba_cond += f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;text-align:center;border:1px solid #1a1a1a;"><div style="font-size:10px;color:#666;text-transform:uppercase;margin-bottom:6px;">TSS Hoje</div><div style="font-size:22px;font-weight:700;color:#10b981;">{int(ultimo["tss"])}</div></div>'
    aba_cond += '</div>'

    aba_cond += '''<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;">
<div style="font-size:11px;color:#666;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;">📈 Métricas (toggle)</div>
<div id="metric-toggles" style="display:flex;flex-wrap:wrap;gap:8px;">
<button class="metric-btn active" data-metric="ctl" data-color="#3b82f6">CTL</button>
<button class="metric-btn active" data-metric="atl" data-color="#fb923c">ATL</button>
<button class="metric-btn active" data-metric="tsb" data-color="#4ade80">TSB</button>
<button class="metric-btn" data-metric="tss" data-color="#a855f7">TSS</button>
</div>
</div>'''
    aba_cond += '<div style="background:#0a0a0a;padding:14px;border-radius:8px;"><canvas id="wellnessChart" style="width:100%;height:400px;"></canvas></div>'
    aba_cond += '</div>'

    # ─── HTML completo ─────────────────────────────────────────────────────

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🚴 Strava Coach v10.0</title>
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
.tabs {{ display: flex; gap: 6px; margin-bottom: 16px; border-bottom: 1px solid #222; flex-wrap: wrap; }}
.tab {{ background: none; border: none; color: #888; padding: 10px 16px; font-size: 12px; font-weight: 600; cursor: pointer; border-radius: 8px 8px 0 0; }}
.tab.active {{ background: #1a1a1a; color: #fff; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.filtros {{ display: flex; gap: 12px; margin-bottom: 16px; padding: 12px; background: #111; border-radius: 10px; align-items: center; flex-wrap: wrap; }}
.filtros label {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #ddd; cursor: pointer; }}
.filtros input[type="checkbox"] {{ cursor: pointer; width: 16px; height: 16px; }}
.filtros .label-title {{ font-size: 11px; color: #666; text-transform: uppercase; margin-right: 8px; }}
.treino-item.hidden {{ display: none; }}
.treino-header:hover {{ background: #0f0f0f; }}
.metric-btn {{ background: #1a1a1a; border: 1px solid #2a2a2a; color: #888; padding: 6px 12px; font-size: 11px; border-radius: 6px; cursor: pointer; }}
.metric-btn.active {{ background: #2a2a2a; color: #fff; border-color: #444; }}
@media (max-width: 768px) {{
  .fitness-bar {{ grid-template-columns: repeat(2, 1fr); }}
  body {{ padding: 10px; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
<h1>🚴 Strava Coach v10.0</h1>
<p>Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>

<div class="fitness-bar">
<div class="fc-card"><div class="label">CTL</div><div class="value" style="color:#3b82f6;">{ctl}</div></div>
<div class="fc-card"><div class="label">ATL</div><div class="value" style="color:#fb923c;">{atl}</div></div>
<div class="fc-card"><div class="label">TSB</div><div class="value" style="color:{cor_tsb};">{tsb}</div></div>
<div class="fc-card"><div class="label">FTP</div><div class="value">{FTP}W</div><div class="sub">{wkg} W/kg</div></div>
<div class="fc-card"><div class="label">Peso</div><div class="value">{PESO}</div><div class="sub">kg</div></div>
</div>

{cards_analise}
{cards_vo2}

<div class="tabs">
<button class="tab active" data-tab="atual">📅 Semana Atual</button>
<button class="tab" data-tab="proxima">🎯 Próxima Semana</button>
<button class="tab" data-tab="historico">📊 Histórico</button>
<button class="tab" data-tab="condicionamento">📈 Condicionamento</button>
</div>

<div id="atual" class="tab-content active">{aba_atual}</div>
<div id="proxima" class="tab-content">{aba_prox}</div>
<div id="historico" class="tab-content">{aba_hist}</div>
<div id="condicionamento" class="tab-content">{aba_cond}</div>

</div>

<script>
const wellnessData = {hist_json};

document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'condicionamento') renderChart();
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
    const forecastStart = wellnessData.findIndex(d => d.forecast);

    document.querySelectorAll('.metric-btn').forEach(btn => {{
        if (btn.classList.contains('active')) {{
            const metric = btn.dataset.metric;
            const color = btn.dataset.color;
            const label = btn.textContent;
            const dataReal = wellnessData.map((d, i) => i < forecastStart || forecastStart === -1 ? d[metric] : null);
            const dataForecast = wellnessData.map((d, i) => i >= forecastStart && forecastStart !== -1 ? d[metric] : null);

            datasets.push({{
                label: label, data: dataReal, borderColor: color, backgroundColor: color + '20',
                borderWidth: 2, tension: 0.3, pointRadius: 0
            }});
            if (forecastStart !== -1) {{
                datasets.push({{
                    label: label + ' (FC)', data: dataForecast, borderColor: color, backgroundColor: color + '10',
                    borderWidth: 2, borderDash: [5, 5], tension: 0.3, pointRadius: 3, pointStyle: 'rectRot'
                }});
            }}
        }}
    }});

    chartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            interaction: {{ mode: 'index', intersect: false }},
            plugins: {{
                legend: {{ labels: {{ color: '#ddd', font: {{ size: 11 }}, filter: (item) => !item.text.includes('FC') }} }},
                tooltip: {{ backgroundColor: '#000', borderColor: '#444', borderWidth: 1 }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '#666', maxRotation: 0, autoSkipPadding: 20 }}, grid: {{ color: '#1a1a1a' }} }},
                y: {{ ticks: {{ color: '#666' }}, grid: {{ color: '#1a1a1a' }} }}
            }}
        }}
    }});
}}

document.querySelectorAll('.metric-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        btn.classList.toggle('active');
        if (document.getElementById('condicionamento').classList.contains('active')) renderChart();
    }});
}});
</script>

</body>
</html>'''

    return html

# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    print("🎨 Dashboard Generator v10.0\n")
    treinos, wellness, fitness, estado = load_data()
    print(f"✅ {len(treinos)} treinos carregados")

    # Auto-update do estado: se passou pra próxima semana, atualiza intensidade
    hoje = datetime.now()
    seg_atual_str = (hoje - timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')

    if estado.get('semana_referencia') != seg_atual_str:
        # Mudou de semana — calcula nova intensidade baseado na semana anterior
        print(f"📅 Nova semana detectada ({seg_atual_str})")

        # Pega TSB e analise da semana que acabou
        historico = calcular_wellness_historico(treinos)
        ultimo = [h for h in historico if not h.get('forecast')][-1]
        tsb_atual = ultimo['tsb']

        intens_anterior = estado.get('intensidade_atual', 'normal')
        analise_anterior = analisar_semana_atual(treinos, intens_anterior)

        nova_intens, _, _ = decidir_intensidade_proxima(
            tsb_atual, analise_anterior['aderencia_pct'], analise_anterior['treinos_perdidos']
        )

        estado = {
            'semana_referencia': seg_atual_str,
            'intensidade_atual': nova_intens,
            'ultima_atualizacao': hoje.strftime('%Y-%m-%d %H:%M')
        }
        save_estado(estado)
        print(f"✅ Estado atualizado: intensidade = {nova_intens}")
    else:
        estado['ultima_atualizacao'] = hoje.strftime('%Y-%m-%d %H:%M')
        save_estado(estado)

    html = build_dashboard(treinos, wellness, fitness, estado)
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ dashboard.html gerado ({len(html):,} bytes)")
    print(f"📊 Intensidade da semana: {estado.get('intensidade_atual', 'normal').upper()}")

if __name__ == '__main__':
    main()
