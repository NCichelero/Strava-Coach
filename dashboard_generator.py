"""
🎨 DASHBOARD GENERATOR v12
- Tabs no topo
- Aba Hoje como default
- Layout limpo: sem cards duplicados, sem métricas inúteis
- Previsão FTP removida (cálculo quebrado)
- VO2max FC removida (fórmula imprecisa)
- Comparação Periódica movida para Condicionamento
- config.json para TSS meta e dias OFF
"""

import json
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import statistics

from analytics import gerar_analytics_completo
from dashboard_cards_lite import build_aba_analytics, build_card_tss_bloco

# ─── Config dinâmico ───────────────────────────────────────────────────────

def carregar_config():
    path = 'config.json'
    defaults = {'tss_meta_semana': 350, 'dias_off_planejados': []}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        defaults.update({k: v for k, v in cfg.items() if not k.startswith('_')})
    return defaults

CONFIG = carregar_config()

# ─── Configuração base ─────────────────────────────────────────────────────

FTP = 210
PESO = 75.6
FC_MAX = 190
FC_REPOUSO = 39
META_CTL = 45
TSS_META_SEMANA = CONFIG.get('tss_meta_semana', 350)

TZ_BRT = timezone(timedelta(hours=-3))

def agora():
    return datetime.now(TZ_BRT).replace(tzinfo=None)

ZONAS_FC = {
    'Z1': (115, 129), 'Z2': (129, 145),
    'Z3': (145, 161), 'Z4': (161, 176), 'Z5': (176, 200),
}

# ─── PERIODIZAÇÃO ──────────────────────────────────────────────────────────

BLOCOS = {
    'base': {
        'nome': 'BASE AERÓBICA', 'descricao': 'Construir capacidade aeróbica e eficiência metabólica',
        'foco': 'Sweet Spot + Endurance Z2 longo', 'icone': '🏗️', 'cor': '#3b82f6',
        'duracao_sem': 4, 'distribuicao': '85% Z1-Z2 | 15% Z3 | 0% Z4-Z5',
        'objetivo': 'Aumentar CTL para 38-40 | Eficiência aeróbica'
    },
    'threshold': {
        'nome': 'THRESHOLD', 'descricao': 'Empurrar o limiar funcional para cima',
        'foco': 'Intervalos no FTP + Over-Unders', 'icone': '🎯', 'cor': '#fbbf24',
        'duracao_sem': 4, 'distribuicao': '80% Z1-Z2 | 5% Z3 | 15% Z4',
        'objetivo': 'Subir FTP +5W | Melhorar TTE'
    },
    'vo2max': {
        'nome': 'VO2MAX', 'descricao': 'Levantar teto aeróbico para puxar o FTP',
        'foco': 'Intervalos curtos de alta intensidade', 'icone': '🚀', 'cor': '#f87171',
        'duracao_sem': 4, 'distribuicao': '75% Z1-Z2 | 5% Z3 | 5% Z4 | 15% Z5',
        'objetivo': 'Aumentar VO2max + Pico 5min'
    },
    'integracao': {
        'nome': 'INTEGRAÇÃO', 'descricao': 'Consolidar ganhos e testar novo FTP',
        'foco': 'Sweet Spot longo + simulações', 'icone': '✨', 'cor': '#10b981',
        'duracao_sem': 4, 'distribuicao': '80% Z1-Z2 | 10% Z3 | 10% Z4',
        'objetivo': 'Estabilizar novo FTP | Re-testar'
    },
}

ORDEM_BLOCOS = ['base', 'threshold', 'vo2max', 'integracao']

# ─── BIBLIOTECA DE TREINOS ──────────────────────────────────────────────────

def treinos_quarta_por_bloco(bloco, semana_no_bloco):
    if bloco == 'base':
        if semana_no_bloco == 1:
            return {'nome': '🍯 Sweet Spot 2x15min', 'dur_total': 70, 'tss_alvo': 75, 'blocos': [
                {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'SS Bloco 1', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Recuperação ativa', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'SS Bloco 2', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Z2 + Cooldown', 'dur': 20, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2-Z1'},
            ]}
        elif semana_no_bloco == 2:
            return {'nome': '🍯 Sweet Spot 2x20min', 'dur_total': 80, 'tss_alvo': 90, 'blocos': [
                {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'SS Bloco 1 (20min)', 'dur': 20, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Recuperação ativa', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'SS Bloco 2 (20min)', 'dur': 20, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Z2 + Cooldown', 'dur': 20, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2-Z1'},
            ]}
        elif semana_no_bloco == 3:
            return {'nome': '🍯 Sweet Spot 3x15min', 'dur_total': 90, 'tss_alvo': 105, 'blocos': [
                {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'SS Bloco 1', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'SS Bloco 2', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'SS Bloco 3', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Cooldown', 'dur': 20, 'pct_min': 0.45, 'pct_max': 0.60, 'zona': 'Z1'},
            ]}
        else:
            return {'nome': '☘️ Z2 Recovery', 'dur_total': 60, 'tss_alvo': 45, 'blocos': [
                {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}
    elif bloco == 'threshold':
        if semana_no_bloco == 1:
            return {'nome': '🎯 Threshold 2x15min @ 95% FTP', 'dur_total': 80, 'tss_alvo': 95, 'blocos': [
                {'nome': 'Warm-up + 3 sprints curtos', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'Threshold 1', 'dur': 15, 'pct_min': 0.93, 'pct_max': 0.97, 'zona': 'Z4'},
                {'nome': 'Recuperação completa', 'dur': 8, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1-Z2'},
                {'nome': 'Threshold 2', 'dur': 15, 'pct_min': 0.93, 'pct_max': 0.97, 'zona': 'Z4'},
                {'nome': 'Cooldown', 'dur': 17, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        elif semana_no_bloco == 2:
            return {'nome': '🎯 Threshold 3x12min @ 98% FTP', 'dur_total': 85, 'tss_alvo': 105, 'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'Threshold 1', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                {'nome': 'Recuperação', 'dur': 6, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'Threshold 2', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                {'nome': 'Recuperação', 'dur': 6, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'Threshold 3', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                {'nome': 'Cooldown', 'dur': 22, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        elif semana_no_bloco == 3:
            return {'nome': '🎯 Threshold 2x20min @ 95-100% FTP', 'dur_total': 90, 'tss_alvo': 115, 'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'Threshold 1 (20min)', 'dur': 20, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                {'nome': 'Recuperação', 'dur': 8, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'Threshold 2 (20min)', 'dur': 20, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                {'nome': 'Cooldown', 'dur': 27, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        else:
            return {'nome': '☘️ Z2 Recovery', 'dur_total': 60, 'tss_alvo': 45, 'blocos': [
                {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}
    elif bloco == 'vo2max':
        if semana_no_bloco == 1:
            return {'nome': '🚀 VO2max 5x3min @ 115% FTP', 'dur_total': 75, 'tss_alvo': 100, 'blocos': [
                {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                {'nome': 'VO2max #1', 'dur': 3, 'pct_min': 1.13, 'pct_max': 1.18, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #2', 'dur': 3, 'pct_min': 1.13, 'pct_max': 1.18, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #3', 'dur': 3, 'pct_min': 1.13, 'pct_max': 1.18, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #4', 'dur': 3, 'pct_min': 1.13, 'pct_max': 1.18, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #5', 'dur': 3, 'pct_min': 1.13, 'pct_max': 1.18, 'zona': 'Z5'},
                {'nome': 'Cooldown', 'dur': 13, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        elif semana_no_bloco == 2:
            return {'nome': '🚀 30/30 Billat (8x4min)', 'dur_total': 80, 'tss_alvo': 105, 'blocos': [
                {'nome': 'Warm-up + 3 sprints', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                {'nome': '4min de 30/30 (1)', 'dur': 4, 'pct_min': 0.95, 'pct_max': 1.20, 'zona': 'Z4-Z5'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': '4min de 30/30 (2)', 'dur': 4, 'pct_min': 0.95, 'pct_max': 1.20, 'zona': 'Z4-Z5'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': '4min de 30/30 (3)', 'dur': 4, 'pct_min': 0.95, 'pct_max': 1.20, 'zona': 'Z4-Z5'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': '4min de 30/30 (4)', 'dur': 4, 'pct_min': 0.95, 'pct_max': 1.20, 'zona': 'Z4-Z5'},
                {'nome': 'Cooldown', 'dur': 33, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1-Z2'},
            ]}
        elif semana_no_bloco == 3:
            return {'nome': '🚀 VO2max 6x3min @ 118% FTP', 'dur_total': 85, 'tss_alvo': 115, 'blocos': [
                {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                {'nome': 'VO2max #1', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #2', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #3', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #4', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #5', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Recuperação', 'dur': 3, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'VO2max #6', 'dur': 3, 'pct_min': 1.15, 'pct_max': 1.20, 'zona': 'Z5'},
                {'nome': 'Cooldown', 'dur': 18, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        else:
            return {'nome': '☘️ Z2 Recovery (pós-VO2)', 'dur_total': 60, 'tss_alvo': 45, 'blocos': [
                {'nome': 'Warm-up muito leve', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.58, 'pct_max': 0.65, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.45, 'zona': 'Z1'},
            ]}
    else:  # integracao
        if semana_no_bloco == 1:
            return {'nome': '🎯 Over-Under 4x6min', 'dur_total': 80, 'tss_alvo': 105, 'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'OU #1', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'OU #2', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'OU #3', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'OU #4', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                {'nome': 'Cooldown', 'dur': 29, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        elif semana_no_bloco == 2:
            return {'nome': '🎯 Sweet Spot 2x25min', 'dur_total': 95, 'tss_alvo': 115, 'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                {'nome': 'SS longo 1 (25min)', 'dur': 25, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Recuperação ativa', 'dur': 8, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2'},
                {'nome': 'SS longo 2 (25min)', 'dur': 25, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                {'nome': 'Cooldown', 'dur': 22, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        elif semana_no_bloco == 3:
            return {'nome': '🧪 TESTE FTP - 20min All-out', 'dur_total': 75, 'tss_alvo': 100, 'blocos': [
                {'nome': 'Warm-up amplo', 'dur': 25, 'pct_min': 0.50, 'pct_max': 0.80, 'zona': 'Z1-Z3'},
                {'nome': '5min @ 90% FTP', 'dur': 5, 'pct_min': 0.88, 'pct_max': 0.92, 'zona': 'Z3'},
                {'nome': 'Recuperação', 'dur': 10, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': '⚡ 20min MAX', 'dur': 20, 'pct_min': 1.00, 'pct_max': 1.10, 'zona': 'Z4-Z5'},
                {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
        else:
            return {'nome': '☘️ Z2 Recovery + Re-test', 'dur_total': 60, 'tss_alvo': 45, 'blocos': [
                {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 leve', 'dur': 40, 'pct_min': 0.58, 'pct_max': 0.65, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}


def treinos_sexta_por_bloco(bloco, semana_no_bloco):
    if bloco == 'base':
        configs = {
            1: ('🍯 Sweet Spot 3x10min', 75, 80, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'), ('SS #1', 10, 0.86, 0.91, 'Z3'),
                ('Recuperação', 5, 0.50, 0.60, 'Z1'), ('SS #2', 10, 0.86, 0.91, 'Z3'),
                ('Recuperação', 5, 0.50, 0.60, 'Z1'), ('SS #3', 10, 0.86, 0.91, 'Z3'),
                ('Z2 + Cooldown', 20, 0.55, 0.65, 'Z2-Z1')]),
            2: ('🍯 Sweet Spot 3x12min', 80, 90, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'), ('SS #1', 12, 0.86, 0.91, 'Z3'),
                ('Recuperação', 5, 0.50, 0.60, 'Z1'), ('SS #2', 12, 0.86, 0.91, 'Z3'),
                ('Recuperação', 5, 0.50, 0.60, 'Z1'), ('SS #3', 12, 0.86, 0.91, 'Z3'),
                ('Cooldown', 19, 0.40, 0.55, 'Z1')]),
            3: ('🍯 Sweet Spot 4x10min', 85, 100, [
                ('Warm-up', 12, 0.50, 0.70, 'Z1-Z2'), ('SS #1', 10, 0.88, 0.93, 'Z3'),
                ('Recup', 4, 0.50, 0.60, 'Z1'), ('SS #2', 10, 0.88, 0.93, 'Z3'),
                ('Recup', 4, 0.50, 0.60, 'Z1'), ('SS #3', 10, 0.88, 0.93, 'Z3'),
                ('Recup', 4, 0.50, 0.60, 'Z1'), ('SS #4', 10, 0.88, 0.93, 'Z3'),
                ('Cooldown', 21, 0.40, 0.55, 'Z1')]),
            4: ('☘️ Z2 Endurance', 60, 50, [
                ('Warm-up', 10, 0.40, 0.55, 'Z1'), ('Z2 Endurance', 40, 0.62, 0.70, 'Z2'),
                ('Cooldown', 10, 0.35, 0.50, 'Z1')]),
        }
    elif bloco == 'threshold':
        configs = {
            1: ('⚙️ Over-Under 3x8min', 80, 95, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'), ('OU #1', 8, 0.93, 1.07, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('OU #2', 8, 0.93, 1.07, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('OU #3', 8, 0.93, 1.07, 'Z4'),
                ('Cooldown', 31, 0.40, 0.55, 'Z1')]),
            2: ('⚙️ Criss-Cross 3x10min', 85, 100, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'), ('CC #1', 10, 0.90, 1.10, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('CC #2', 10, 0.90, 1.10, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('CC #3', 10, 0.90, 1.10, 'Z4'),
                ('Cooldown', 30, 0.40, 0.55, 'Z1')]),
            3: ('⚙️ Over-Under 4x8min', 90, 110, [
                ('Warm-up', 12, 0.50, 0.70, 'Z1-Z2'), ('OU #1', 8, 0.93, 1.07, 'Z4'),
                ('Recup', 4, 0.45, 0.55, 'Z1'), ('OU #2', 8, 0.93, 1.07, 'Z4'),
                ('Recup', 4, 0.45, 0.55, 'Z1'), ('OU #3', 8, 0.93, 1.07, 'Z4'),
                ('Recup', 4, 0.45, 0.55, 'Z1'), ('OU #4', 8, 0.93, 1.07, 'Z4'),
                ('Cooldown', 34, 0.40, 0.55, 'Z1')]),
            4: ('☘️ Z2 Endurance', 60, 50, [
                ('Warm-up', 10, 0.40, 0.55, 'Z1'), ('Z2', 40, 0.62, 0.70, 'Z2'),
                ('Cooldown', 10, 0.35, 0.50, 'Z1')]),
        }
    elif bloco == 'vo2max':
        configs = {
            1: ('🚀 30/15 Rønnestad (3x13)', 80, 100, [
                ('Warm-up + sprints', 15, 0.50, 0.75, 'Z1-Z2'),
                ('13× (30s @ 115%, 15s @ 60%)', 10, 0.60, 1.18, 'Z5'),
                ('Recuperação', 4, 0.40, 0.55, 'Z1'),
                ('13× (30/15)', 10, 0.60, 1.18, 'Z5'),
                ('Recuperação', 4, 0.40, 0.55, 'Z1'),
                ('13× (30/15)', 10, 0.60, 1.18, 'Z5'),
                ('Cooldown', 27, 0.40, 0.55, 'Z1')]),
            2: ('🚀 VO2max 4x4min @ 110% FTP', 80, 105, [
                ('Warm-up', 15, 0.50, 0.75, 'Z1-Z2'), ('VO2max #1', 4, 1.08, 1.13, 'Z5'),
                ('Recuperação', 4, 0.40, 0.55, 'Z1'), ('VO2max #2', 4, 1.08, 1.13, 'Z5'),
                ('Recuperação', 4, 0.40, 0.55, 'Z1'), ('VO2max #3', 4, 1.08, 1.13, 'Z5'),
                ('Recuperação', 4, 0.40, 0.55, 'Z1'), ('VO2max #4', 4, 1.08, 1.13, 'Z5'),
                ('Cooldown', 37, 0.40, 0.55, 'Z1')]),
            3: ('🚀 Bossi Mix 3x10min', 85, 110, [
                ('Warm-up', 15, 0.50, 0.75, 'Z1-Z2'),
                ('Bossi #1', 10, 0.75, 1.22, 'Z5'), ('Recuperação', 5, 0.45, 0.55, 'Z1'),
                ('Bossi #2', 10, 0.75, 1.22, 'Z5'), ('Recuperação', 5, 0.45, 0.55, 'Z1'),
                ('Bossi #3', 10, 0.75, 1.22, 'Z5'), ('Cooldown', 30, 0.40, 0.55, 'Z1')]),
            4: ('☘️ Z2 Recovery', 60, 45, [
                ('Warm-up', 10, 0.35, 0.50, 'Z1'), ('Z2 leve', 40, 0.58, 0.65, 'Z2'),
                ('Cooldown', 10, 0.35, 0.45, 'Z1')]),
        }
    else:  # integracao
        configs = {
            1: ('⚙️ Threshold 3x10min @ FTP', 75, 90, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'), ('Threshold #1', 10, 0.97, 1.02, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('Threshold #2', 10, 0.97, 1.02, 'Z4'),
                ('Recuperação', 5, 0.45, 0.55, 'Z1'), ('Threshold #3', 10, 0.97, 1.02, 'Z4'),
                ('Cooldown', 20, 0.40, 0.55, 'Z1')]),
            2: ('⚡ Race Sim 30min @ FTP', 75, 95, [
                ('Warm-up + ativação', 20, 0.50, 0.80, 'Z1-Z3'),
                ('⚡ 30min sustentado @ FTP', 30, 0.98, 1.03, 'Z4'),
                ('Cooldown', 25, 0.40, 0.55, 'Z1')]),
            3: ('🧪 Pré-teste tune-up', 60, 55, [
                ('Warm-up', 15, 0.50, 0.70, 'Z1-Z2'),
                ('5min @ 85%', 5, 0.83, 0.88, 'Z3'),
                ('Recuperação', 10, 0.45, 0.55, 'Z1'),
                ('2× 1min @ 110%', 5, 0.50, 1.10, 'Z5'),
                ('Cooldown', 25, 0.40, 0.55, 'Z1')]),
            4: ('☘️ Z2 Endurance', 60, 50, [
                ('Warm-up', 10, 0.40, 0.55, 'Z1'), ('Z2', 40, 0.62, 0.70, 'Z2'),
                ('Cooldown', 10, 0.35, 0.50, 'Z1')]),
        }
    nome, dur, tss, bls = configs[semana_no_bloco]
    return {'nome': nome, 'dur_total': dur, 'tss_alvo': tss,
            'blocos': [{'nome': b[0], 'dur': b[1], 'pct_min': b[2], 'pct_max': b[3], 'zona': b[4]} for b in bls]}


def treino_segunda_recovery(semana_no_bloco):
    if semana_no_bloco == 4:
        return {'nome': '☘️ Z2 Spin Leve', 'dur_total': 50, 'tss_alvo': 35, 'blocos': [
            {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            {'nome': 'Z2 baixa', 'dur': 30, 'pct_min': 0.55, 'pct_max': 0.62, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
        ]}
    return {'nome': '☘️ Z2 Endurance Aeróbico', 'dur_total': 70, 'tss_alvo': 55, 'blocos': [
        {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
        {'nome': 'Z2 Endurance', 'dur': 50, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
        {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
    ]}


def treino_sabado_longo(bloco, semana_no_bloco):
    if semana_no_bloco == 4:
        return {'nome': '☘️ Endurance Z2 (recovery week)', 'dur_total': 90, 'tss_alvo': 75, 'blocos': [
            {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            {'nome': 'Z2 Endurance', 'dur': 70, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
        ]}
    if bloco == 'base':
        return {'nome': '🏞️ Long Ride Z2 + Sweet Spot', 'dur_total': 180, 'tss_alvo': 175, 'blocos': [
            {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
            {'nome': 'Z2 Endurance', 'dur': 75, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
            {'nome': 'SS embedido (15min)', 'dur': 15, 'pct_min': 0.85, 'pct_max': 0.90, 'zona': 'Z3'},
            {'nome': 'Z2 Endurance', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
        ]}
    elif bloco == 'threshold':
        return {'nome': '🏞️ Long Ride + 2x Tempo', 'dur_total': 180, 'tss_alvo': 190, 'blocos': [
            {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
            {'nome': 'Z2', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.75, 'zona': 'Z2'},
            {'nome': 'Tempo #1 (15min)', 'dur': 15, 'pct_min': 0.80, 'pct_max': 0.88, 'zona': 'Z3'},
            {'nome': 'Z2 Recovery', 'dur': 15, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
            {'nome': 'Tempo #2 (15min)', 'dur': 15, 'pct_min': 0.80, 'pct_max': 0.88, 'zona': 'Z3'},
            {'nome': 'Z2', 'dur': 45, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
        ]}
    elif bloco == 'vo2max':
        return {'nome': '🏞️ Long Z2 (recovery dos VO2)', 'dur_total': 180, 'tss_alvo': 160, 'blocos': [
            {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            {'nome': 'Z2 Endurance fundo', 'dur': 150, 'pct_min': 0.62, 'pct_max': 0.70, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
        ]}
    else:
        return {'nome': '🏞️ Race Simulation', 'dur_total': 180, 'tss_alvo': 200, 'blocos': [
            {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
            {'nome': 'Z2', 'dur': 45, 'pct_min': 0.65, 'pct_max': 0.75, 'zona': 'Z2'},
            {'nome': 'SS Block #1', 'dur': 20, 'pct_min': 0.85, 'pct_max': 0.92, 'zona': 'Z3'},
            {'nome': 'Z2', 'dur': 15, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
            {'nome': '5× Surge (1min @ 110%)', 'dur': 10, 'pct_min': 0.60, 'pct_max': 1.10, 'zona': 'Z2-Z5'},
            {'nome': 'Z2', 'dur': 15, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
            {'nome': 'SS Block #2', 'dur': 15, 'pct_min': 0.85, 'pct_max': 0.92, 'zona': 'Z3'},
            {'nome': 'Z2', 'dur': 30, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
        ]}


def treino_domingo(bloco, semana_no_bloco, tsb=0):
    if semana_no_bloco == 4 or tsb < -20:
        return {'nome': '😴 Descanso ou Caminhada', 'tipo': 'recuperacao', 'horario': '—',
                'dur_total': 0, 'tss_alvo': 0,
                'blocos': [{'nome': 'Descanso total ou caminhada leve 30min', 'dur': 0, 'detalhes': 'Recuperação obrigatória'}]}
    if bloco in ('base', 'integracao'):
        return {'nome': '🌅 Endurance Z2 Suave', 'tipo': 'ciclismo', 'horario': '07:00',
                'dur_total': 75, 'tss_alvo': 60,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 Endurance', 'dur': 55, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}
    return {'nome': '😴 Recovery Day', 'tipo': 'recuperacao', 'horario': '—',
            'dur_total': 0, 'tss_alvo': 0,
            'blocos': [{'nome': 'Descanso ou caminhada leve', 'dur': 30, 'detalhes': 'Sem bike — recuperar para próximo bloco'}]}


def gerar_plano_semana_bloco(bloco, semana_no_bloco, tsb=0):
    plano = {}
    seg = treino_segunda_recovery(semana_no_bloco)
    seg['tipo'] = 'ciclismo'; seg['horario'] = '05:30'
    plano[0] = seg
    plano[1] = {'nome': '🏋️ Academia - Superiores', 'tipo': 'academia', 'horario': '—',
                'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Peito + Tríceps + Ombro + Core', 'dur': 60, 'detalhes': '4 séries 8-12 reps · Foco em hipertrofia'}]}
    quarta = treinos_quarta_por_bloco(bloco, semana_no_bloco)
    quarta['tipo'] = 'ciclismo'; quarta['horario'] = '05:30'
    plano[2] = quarta
    plano[3] = {'nome': '🏋️ Academia - Inferiores', 'tipo': 'academia', 'horario': '—',
                'dur_total': 60, 'tss_alvo': 0,
                'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento + Leg press + Stiff + Panturrilha'}]}
    sexta = treinos_sexta_por_bloco(bloco, semana_no_bloco)
    sexta['tipo'] = 'ciclismo'; sexta['horario'] = '05:30'
    plano[4] = sexta
    sab = treino_sabado_longo(bloco, semana_no_bloco)
    sab['tipo'] = 'ciclismo'; sab['horario'] = '07:00'
    plano[5] = sab
    plano[6] = treino_domingo(bloco, semana_no_bloco, tsb)
    return plano

# ─── Loaders ───────────────────────────────────────────────────────────────

def load_data():
    treinos, wellness, fitness, estado = {}, [], {'ctl': 36, 'atl': 54, 'tsb': -18}, {}
    for nome, var in [('treinos.json', None), ('wellness.json', None), ('fitness.json', None), ('estado.json', None)]:
        path = f'data/{nome}'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if nome == 'treinos.json': treinos = data
            elif nome == 'wellness.json': wellness = data
            elif nome == 'fitness.json': fitness = data
            elif nome == 'estado.json': estado = data
    print("📊 Gerando analytics...")
    analytics_data = gerar_analytics_completo()
    return treinos, wellness, fitness, estado, analytics_data

def save_estado(estado):
    os.makedirs('data', exist_ok=True)
    with open('data/estado.json', 'w', encoding='utf-8') as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

# ─── Métricas ──────────────────────────────────────────────────────────────

def zona_por_fc(fc):
    if fc <= 0: return '—'
    if fc < 129: return 'Z1'
    if fc < 145: return 'Z2'
    if fc < 161: return 'Z3'
    if fc < 176: return 'Z4'
    return 'Z5'

def zona_treino(t):
    if t.get('categoria') != 'ciclismo': return '—'
    fc = t.get('fc_avg', 0); pot = t.get('potencia_avg', 0)
    if fc > 50: return zona_por_fc(fc)
    if pot > 50:
        pct = pot / FTP
        if pct < 0.55: return 'Z1'
        elif pct < 0.75: return 'Z2'
        elif pct < 0.90: return 'Z3'
        elif pct < 1.05: return 'Z4'
        else: return 'Z5'
    return '—'

def vo2max_potencia(treinos):
    duas_sem = (agora() - timedelta(days=14)).strftime('%Y-%m-%d')
    picos = [t.get('pico_5min', 0) for t in treinos.values()
             if t.get('data', '') >= duas_sem and t.get('pico_5min', 0) > 0]
    if not picos: return 0, 0
    melhor = max(picos)
    return round(16.6 + (8.87 * (melhor / PESO)), 1), melhor

def classificar_vo2(vo2):
    if vo2 >= 55: return 'Excelente', '#10b981'
    elif vo2 >= 47: return 'Muito Bom', '#3b82f6'
    elif vo2 >= 41: return 'Bom', '#facc15'
    elif vo2 >= 33: return 'Regular', '#f97316'
    elif vo2 > 0: return 'Baixo', '#ef4444'
    return '—', '#888'

def calcular_nota(t):
    cat = t.get('categoria', 'outros')
    if cat == 'ciclismo':
        dur = t.get('duracao_min', 0); pot_avg = t.get('potencia_avg', 0)
        fc_avg = t.get('fc_avg', 0); pot_norm = t.get('potencia_norm', 0) or pot_avg
        nd = 3 if dur < 20 else (7 if dur < 45 else (9 if dur < 90 else (10 if dur < 180 else 9.5)))
        if pot_avg > 50:
            pct = pot_avg / FTP
            ni = 5 if pct < 0.55 else (7.5 if pct < 0.75 else (8.5 if pct < 0.90 else (9.5 if pct < 1.05 else 10)))
        elif fc_avg > 0:
            pct = fc_avg / FC_MAX
            ni = 5 if pct < 0.68 else (7.5 if pct < 0.76 else (8.5 if pct < 0.84 else (9.5 if pct < 0.92 else 10)))
        else: ni = 6
        ne = min(10, (pot_avg / fc_avg) * 8) if pot_avg > 50 and fc_avg > 0 else 6
        if pot_norm > 50 and pot_avg > 50:
            vi = pot_norm / pot_avg
            nv = 10 if vi < 1.05 else (8 if vi < 1.15 else (6 if vi < 1.25 else 4))
        else: nv = 6
        return round((nd * 0.30) + (ni * 0.35) + (ne * 0.20) + (nv * 0.15), 1)
    elif cat == 'academia':
        dur = t.get('duracao_min', 0)
        return 5.5 if dur < 30 else (6.5 if dur < 45 else (8.0 if dur < 75 else 8.5))
    return 6.0

def tss_treino(t):
    dur = t.get('duracao_min', 0)
    pot_norm = t.get('potencia_norm', 0) or t.get('potencia_avg', 0)
    fc_avg = t.get('fc_avg', 0)
    if pot_norm > 50: return round(dur * (pot_norm / FTP) ** 2 * 100 / 60, 1)
    elif fc_avg > 0: return round(dur * (fc_avg / FC_MAX) ** 2 * 100 / 60, 1)
    return 0

def if_treino(t):
    np = t.get('potencia_norm', 0) or t.get('potencia_avg', 0)
    return round(np / FTP, 2) if np > 50 else 0

def vi_treino(t):
    np = t.get('potencia_norm', 0); ap = t.get('potencia_avg', 0)
    return round(np / ap, 2) if (np > 50 and ap > 50) else 0

def calcular_wellness_historico(treinos):
    tss_diario = defaultdict(float)
    for t in treinos.values():
        data = t.get('data', '')
        if data: tss_diario[data] += tss_treino(t)
    hoje = agora().date()
    historico = []
    ctl = atl = 0
    for i in range(60, -1, -1):
        data = (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        tss = tss_diario.get(data, 0)
        ctl = ctl + (tss - ctl) / 42
        atl = atl + (tss - atl) / 7
        historico.append({'data': data, 'ctl': round(ctl, 1), 'atl': round(atl, 1),
                          'tsb': round(ctl - atl, 1), 'tss': round(tss, 1), 'forecast': False})
    plano_tss = {0: 70, 1: 0, 2: 100, 3: 0, 4: 95, 5: 180, 6: 60}
    ctl_fc, atl_fc = ctl, atl
    for i in range(1, 8):
        d = hoje + timedelta(days=i)
        tss_plan = plano_tss.get(d.weekday(), 0)
        ctl_fc = ctl_fc + (tss_plan - ctl_fc) / 42
        atl_fc = atl_fc + (tss_plan - atl_fc) / 7
        historico.append({'data': d.strftime('%Y-%m-%d'), 'ctl': round(ctl_fc, 1),
                          'atl': round(atl_fc, 1), 'tsb': round(ctl_fc - atl_fc, 1),
                          'tss': tss_plan, 'forecast': True})
    return historico

def analisar_semana_passada(treinos, plano):
    hoje = agora()
    seg_passada = hoje - timedelta(days=hoje.weekday() + 7)
    seg_passada = seg_passada.replace(hour=0, minute=0, second=0, microsecond=0)
    realizados_por_dia = defaultdict(list)
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            if dt >= seg_passada and dt < seg_passada + timedelta(days=7):
                realizados_por_dia[dt.weekday()].append(t)
        except: continue
    treinos_planejados_cic = treinos_perdidos = treinos_feitos = 0
    for wd in range(7):
        plan = plano[wd]; realizados = realizados_por_dia.get(wd, [])
        if plan['tipo'] == 'ciclismo':
            treinos_planejados_cic += 1
            if realizados:
                if plan['tipo'] in [t.get('categoria') for t in realizados]: treinos_feitos += 1
                else: treinos_perdidos += 1
            else: treinos_perdidos += 1
    return {'aderencia_pct': round((treinos_feitos / max(treinos_planejados_cic, 1)) * 100),
            'treinos_perdidos': treinos_perdidos}

def analisar_semana_atual(treinos, plano):
    hoje = agora()
    seg_atual = hoje - timedelta(days=hoje.weekday())
    seg_atual = seg_atual.replace(hour=0, minute=0, second=0, microsecond=0)
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
    tss_realizado_total = tss_alvo_total = treinos_planejados_cic = treinos_perdidos = treinos_feitos = 0
    for wd in range(7):
        plan = plano[wd]; dia_dt = seg_atual + timedelta(days=wd)
        realizados = realizados_por_dia.get(wd, [])
        tss_real_dia = sum(tss_treino(t) for t in realizados)
        tss_realizado_total += tss_real_dia
        tss_alvo_total += plan.get('tss_alvo', 0)
        if plan['tipo'] == 'ciclismo': treinos_planejados_cic += 1
        is_passado = dia_dt.date() < hoje.date()
        is_hoje = dia_dt.date() == hoje.date()
        is_futuro = dia_dt.date() > hoje.date()
        dias_off = CONFIG.get('dias_off_planejados', [])
        is_off = dia_dt.strftime('%Y-%m-%d') in dias_off
        if is_futuro:
            status, icone, cor = ('off', '🗓️', '#6b7280') if is_off else ('futuro', '⏳', '#6b7280')
        elif is_off and not realizados:
            status, icone, cor = 'off', '🗓️', '#6b7280'
        elif realizados:
            cats_real = [t.get('categoria') for t in realizados]
            if plan['tipo'] in cats_real or plan['tipo'] == 'recuperacao':
                status, icone, cor = 'realizado', '✅', '#4ade80'
                if plan['tipo'] == 'ciclismo': treinos_feitos += 1
            elif plan['tipo'] == 'ciclismo' and 'academia' in cats_real:
                status, icone, cor = 'parcial', '⚠️', '#facc15'
            else:
                status, icone, cor = 'parcial', '⚠️', '#facc15'
        elif plan['tipo'] == 'recuperacao':
            status, icone, cor = 'realizado', '✅', '#4ade80'
        elif is_hoje:
            status, icone, cor = 'hoje', '🎯', '#3b82f6'
        elif is_off:
            status, icone, cor = 'off', '🗓️', '#6b7280'
        else:
            status, icone, cor = 'perdido', '❌', '#f87171'
            if plan['tipo'] == 'ciclismo': treinos_perdidos += 1
        resultado.append({'weekday': wd, 'data': dia_dt.strftime('%Y-%m-%d'), 'plano': plan,
                          'realizados': realizados, 'tss_real': round(tss_real_dia, 1),
                          'tss_alvo': plan.get('tss_alvo', 0), 'status': status, 'icone': icone,
                          'cor_status': cor, 'is_hoje': is_hoje, 'is_passado': is_passado})
    avaliados = sum(1 for r in resultado if (r['is_passado'] or r['is_hoje']) and r['plano']['tipo'] == 'ciclismo')
    if avaliados > 0:
        feitos = sum(1 for r in resultado if (r['is_passado'] or r['is_hoje'])
                    and r['plano']['tipo'] == 'ciclismo' and r['status'] == 'realizado')
        aderencia_pct = round((feitos / avaliados) * 100)
    else:
        aderencia_pct = 100
    return {'dias': resultado, 'tss_realizado': round(tss_realizado_total, 1),
            'tss_alvo': tss_alvo_total,
            'tss_pct': round((tss_realizado_total / tss_alvo_total) * 100) if tss_alvo_total > 0 else 0,
            'aderencia_pct': aderencia_pct, 'treinos_perdidos': treinos_perdidos,
            'treinos_feitos': treinos_feitos, 'treinos_planejados_cic': treinos_planejados_cic,
            'seg_atual': seg_atual.strftime('%Y-%m-%d')}

def proxima_semana_periodizacao(estado, tsb, aderencia_pct, treinos_perdidos):
    bloco_atual = estado.get('bloco_atual', 'base')
    semana_atual = estado.get('semana_no_bloco', 1)
    razoes = []; forcou_recovery = False
    if semana_atual < 4:
        prox_semana = semana_atual + 1; prox_bloco = bloco_atual
    else:
        idx = ORDEM_BLOCOS.index(bloco_atual)
        prox_bloco = ORDEM_BLOCOS[(idx + 1) % len(ORDEM_BLOCOS)]
        prox_semana = 1
        razoes.append(f'🎉 Bloco {BLOCOS[bloco_atual]["nome"]} finalizado → iniciando {BLOCOS[prox_bloco]["nome"]}')
    if treinos_perdidos >= 2:
        prox_semana = 4; forcou_recovery = True
        razoes.append(f'⚠️ {treinos_perdidos} treinos perdidos → semana 4 (recovery)')
    if tsb < -25:
        prox_semana = 4; forcou_recovery = True
        razoes.append(f'🔴 TSB {tsb:.0f} crítico → recovery obrigatório')
    if aderencia_pct < 60:
        prox_semana = 4; forcou_recovery = True
        razoes.append(f'⚠️ Aderência baixa ({aderencia_pct}%) → recovery')
    if not razoes:
        if prox_semana == 4:
            razoes.append(f'✅ Semana de recovery planejada')
        else:
            razoes.append(f'📈 Progredindo no bloco {BLOCOS[prox_bloco]["nome"]} (semana {prox_semana}/4)')
    return prox_bloco, prox_semana, razoes, forcou_recovery

def calcular_suplementacao(dur_min):
    if dur_min < 60: return {'carbo_g': 0, 'agua_ml': 400, 'sodio_mg': 200}
    elif dur_min < 90: return {'carbo_g': 50, 'agua_ml': 600, 'sodio_mg': 300}
    elif dur_min < 150: return {'carbo_g': 100, 'agua_ml': 1200, 'sodio_mg': 500}
    else:
        carbo = 50 + (60 * ((dur_min - 90) // 30))
        agua = 600 + (500 * ((dur_min - 90) // 30))
        sodio = 600 if dur_min < 180 else 800
        return {'carbo_g': carbo, 'agua_ml': agua, 'sodio_mg': sodio}

def calcular_distribuicao(treinos):
    quatro_sem = (agora() - timedelta(days=28)).strftime('%Y-%m-%d')
    tempo_zona = defaultdict(float)
    for t in treinos.values():
        if t.get('categoria') != 'ciclismo' or t.get('data', '') < quatro_sem: continue
        dur = t.get('duracao_min', 0); laps = t.get('laps', [])
        if laps:
            for lap in laps:
                zona = lap.get('zona', '—')
                if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
                    tempo_zona[zona] += lap.get('dur_min', 0)
        else:
            zona = zona_treino(t)
            if zona in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']: tempo_zona[zona] += dur
    total = sum(tempo_zona.values())
    if total == 0: return None
    pcts = {z: round((tempo_zona[z] / total) * 100, 1) for z in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']}
    baixa = pcts['Z1'] + pcts['Z2']; media = pcts['Z3']; alta = pcts['Z4'] + pcts['Z5']
    if baixa >= 75 and alta >= 10 and media <= 15:
        modelo, cor, desc = '🎯 Polarizado 80/20', '#10b981', 'Distribuição ideal: muito Z2 + intervalados Z4/Z5'
    elif media >= 30:
        modelo, cor, desc = '⚠️ Piramidal (excesso Z3)', '#facc15', 'Muito Z3. Pode causar fadiga acumulada'
    elif baixa >= 90:
        modelo, cor, desc = '📉 Sub-polarizado', '#9ca3af', 'Falta intensidade. Adicione intervalados Z4/Z5'
    else:
        modelo, cor, desc = '⚖️ Equilibrado', '#3b82f6', 'Distribuição mista'
    return {'pcts': pcts, 'total_min': round(total), 'modelo': modelo, 'cor': cor,
            'descricao': desc, 'baixa': baixa, 'media': media, 'alta': alta}

# ─── UI Helpers ────────────────────────────────────────────────────────────

def watts_pct(pmin, pmax): return f"{int(FTP * pmin)}-{int(FTP * pmax)}W"
def fc_zona_str(z):
    if z in ZONAS_FC: lo, hi = ZONAS_FC[z]; return f"{lo}-{hi}bpm"
    return "—"
def cor_zona(z):
    return {'Z1': '#9ca3af', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}.get(z, '#888')

def build_bloco_treino(b):
    watts = watts_pct(b['pct_min'], b['pct_max']); pct_s = f"{int(b['pct_min']*100)}-{int(b['pct_max']*100)}%"
    fc_s = fc_zona_str(b['zona']); pavg = (b['pct_min'] + b['pct_max']) / 2
    if pavg < 0.55: cb = '#9ca3af'
    elif pavg < 0.75: cb = '#4ade80'
    elif pavg < 0.90: cb = '#facc15'
    elif pavg < 1.05: cb = '#fb923c'
    else: cb = '#f87171'
    h = f'<div style="display:grid;grid-template-columns:200px 60px 1fr 1fr 90px;gap:8px;font-size:11px;padding:6px 8px;margin-bottom:2px;border-left:2px solid {cb};background:#0f0f0f;border-radius:3px;align-items:center;">'
    h += f'<div style="color:#ddd;font-weight:500;">{b["nome"]}</div>'
    h += f'<div style="color:#999;">{b["dur"]}min</div>'
    h += f'<div style="color:{cb};font-weight:600;">{watts}</div>'
    h += f'<div style="color:#999;">{pct_s}</div>'
    h += f'<div style="color:#999;font-size:10px;">{b["zona"]} ({fc_s})</div>'
    h += '</div>'
    return h

def build_treino_realizado_inline(t, uid):
    cat = t.get('categoria', 'outros')
    icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '🏃')
    cor_cat = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
    nota = calcular_nota(t); zona = zona_treino(t); tss_t = tss_treino(t)
    if_v = if_treino(t); vi_v = vi_treino(t); laps_t = t.get('laps', []); pico5 = t.get('pico_5min', 0)
    h = f'<div class="treino-item" data-categoria="{cat}" style="background:#0a0a0a;border-radius:6px;margin-bottom:6px;border-left:3px solid {cor_cat};overflow:hidden;">'
    h += f'<div class="treino-header" onclick="toggleTreino(\'{uid}\')" style="padding:10px 12px;cursor:pointer;user-select:none;">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:6px;">'
    h += f'<div style="font-size:12px;color:#ddd;"><span style="font-size:14px;">{icon}</span> <strong>{t.get("nome", "Sem nome")}</strong> <span style="color:#666;font-weight:400;font-size:10px;margin-left:6px;">▼</span></div>'
    h += f'<div style="font-size:10px;color:#666;">{t.get("data", "")} · Nota: {nota}/10 · TSS: {tss_t}</div>'
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
        metricas = [('TSS', f'{tss_t}', '#3b82f6'), ('IF', f'{if_v}', '#a855f7'),
                    ('VI', f'{vi_v}' if vi_v > 0 else '—', '#ec4899'),
                    ('NP', f'{int(t.get("potencia_norm", 0))}W' if t.get('potencia_norm', 0) > 0 else '—', '#f59e0b'),
                    ('Pot. Máx', f'{int(t.get("potencia_max", 0))}W' if t.get('potencia_max', 0) > 0 else '—', '#ef4444'),
                    ('Pico 5min', f'{pico5}W' if pico5 > 0 else '—', '#8b5cf6'),
                    ('FC Máx', f'{int(t.get("fc_max", 0))}bpm' if t.get('fc_max', 0) > 0 else '—', '#dc2626'),
                    ('Elevação', f'{int(t.get("elevacao", 0))}m', '#0ea5e9'),
                    ('Vel. Média', f'{t.get("velocidade_avg", 0)}km/h', '#06b6d4'),
                    ('Vel. Máx', f'{t.get("velocidade_max", 0)}km/h' if t.get('velocidade_max', 0) > 0 else '—', '#0891b2'),
                    ('Cadência', f'{int(t.get("cadence_avg", 0))}rpm' if t.get('cadence_avg', 0) > 0 else '—', '#8b5cf6'),
                    ('Calorias', f'{int(t.get("calorias", 0))}cal' if t.get('calorias', 0) > 0 else '—', '#f97316')]
        for lbl, val, c in metricas:
            h += f'<div style="background:#0a0a0a;padding:10px;border-radius:6px;text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;margin-bottom:4px;">{lbl}</div><div style="font-size:14px;font-weight:700;color:{c};">{val}</div></div>'
        h += '</div>'
        if laps_t and len(laps_t) > 1:
            h += f'<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">🔄 Voltas ({len(laps_t)})</div>'
            h += '<div style="background:#0a0a0a;border-radius:6px;overflow:hidden;">'
            h += '<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;background:#1a1a1a;font-size:10px;color:#666;text-transform:uppercase;"><div>#</div><div>Nome</div><div>Tempo</div><div>Dist</div><div>Watts</div><div>Máx</div><div>FC</div><div>Zona</div></div>'
            for lap in laps_t:
                zl = lap.get('zona', '—'); cz = cor_zona(zl); ds = lap.get('dur_seg', 0)
                ts = f"{ds//3600}h{(ds%3600)//60:02d}m" if ds >= 3600 else f"{ds//60}m{ds%60:02d}s"
                h += f'<div style="display:grid;grid-template-columns:40px 1fr 70px 70px 70px 70px 70px 60px;gap:8px;padding:8px 12px;border-top:1px solid #1a1a1a;font-size:11px;align-items:center;">'
                h += f'<div style="color:#666;font-weight:600;">{lap.get("idx", "—")}</div>'
                h += f'<div style="color:#ddd;">{lap.get("nome", "")[:30]}</div>'
                h += f'<div style="color:#999;">{ts}</div><div style="color:#999;">{lap.get("dist_km", 0)}km</div>'
                h += f'<div style="color:#ddd;font-weight:600;">{lap.get("pot_avg", 0)}W</div>'
                h += f'<div style="color:#999;font-size:10px;">{lap.get("pot_max", 0)}W</div>'
                h += f'<div style="color:#ddd;">{lap.get("fc_avg", 0)}bpm</div>'
                h += f'<div style="color:{cz};font-weight:600;">{zl}</div></div>'
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
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    plan = dia_info['plano']; realizados = dia_info['realizados']
    status = dia_info['status']; icone = dia_info['icone']; cor_status = dia_info['cor_status']
    is_hoje = dia_info['is_hoje']; cat = plan['tipo']
    icon_cat = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
    cor_cat = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
    border_extra = 'box-shadow: 0 0 0 2px #3b82f6;' if is_hoje else ''
    h = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor_cat};{border_extra}">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">'
    h += f'<div style="display:flex;align-items:center;gap:8px;"><span style="font-size:18px;">{icone}</span>'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon_cat} {dias_pt[dia_info["weekday"]]}'
    if is_hoje: h += ' <span style="color:#3b82f6;font-size:10px;margin-left:4px;">▶ HOJE</span>'
    h += f' <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div></div>'
    h += f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">'
    h += f'<span style="font-size:10px;color:{cor_status};font-weight:600;padding:3px 8px;background:{cor_status}22;border-radius:4px;">{status.upper()}</span>'
    h += f'<span style="font-size:11px;color:#fbbf24;">{plan["nome"]}</span></div></div>'
    if plan.get('tss_alvo', 0) > 0 or dia_info['tss_real'] > 0:
        tss_real = dia_info['tss_real']; tss_alvo = plan.get('tss_alvo', 0)
        pct = round((tss_real / tss_alvo) * 100) if tss_alvo > 0 else (100 if tss_real > 0 else 0)
        pct_bar = min(pct, 150)
        cor_tss = '#4ade80' if 80 <= pct <= 120 else ('#facc15' if 50 <= pct <= 140 else ('#f87171' if pct > 0 else '#6b7280'))
        h += f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;font-size:11px;">'
        h += f'<div style="color:#666;">TSS:</div><div style="color:#ddd;font-weight:600;">{int(tss_real)} / {tss_alvo}</div>'
        h += f'<div style="flex:1;background:#1a1a1a;height:6px;border-radius:3px;overflow:hidden;"><div style="background:{cor_tss};height:100%;width:{pct_bar}%;"></div></div>'
        h += f'<div style="color:{cor_tss};font-weight:700;">{pct}%</div></div>'
    if realizados:
        h += '<div style="margin-top:10px;"><div style="font-size:10px;color:#4ade80;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">✅ Realizado</div>'
        for j, t in enumerate(realizados): h += build_treino_realizado_inline(t, f"atual-{idx}-{j}")
        h += '</div>'
    mostrar_plano = (status in ['futuro', 'hoje', 'perdido', 'parcial', 'off']) and cat == 'ciclismo'
    if mostrar_plano:
        h += '<div style="margin-top:10px;">'
        h += '<div style="font-size:10px;color:#fbbf24;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">📋 Plano</div>'
        h += '<div style="display:grid;grid-template-columns:200px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;"><div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
        for b in plan['blocos']: h += build_bloco_treino(b)
        h += '</div>'
        if is_hoje and cat == 'ciclismo':
            sups = calcular_suplementacao(plan['dur_total'])
            h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
            h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">⚡ Nutrição</div>'
            h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:11px;">'
            h += f'<div><div style="color:#888;font-size:9px;">CARBOIDRATO</div><div style="color:#facc15;font-weight:700;font-size:14px;">{sups["carbo_g"]}g</div></div>'
            h += f'<div><div style="color:#888;font-size:9px;">ÁGUA</div><div style="color:#3b82f6;font-weight:700;font-size:14px;">{sups["agua_ml"]}ml</div></div>'
            h += f'<div><div style="color:#888;font-size:9px;">SÓDIO</div><div style="color:#ec4899;font-weight:700;font-size:14px;">{sups["sodio_mg"]}mg</div></div>'
            h += '</div></div>'
    elif cat == 'academia' and not realizados:
        for b in plan['blocos']:
            h += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;margin-top:6px;"><strong>{b["nome"]}</strong> · {b["dur"]}min'
            if 'detalhes' in b: h += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
            h += '</div>'
    h += '</div>'
    return h

def build_dia_proxima(wd, plan):
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    cat = plan['tipo']; icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
    cor = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
    h = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor};">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px;">'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon} {dias_pt[wd]} <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div>'
    h += f'<div style="font-size:11px;color:#fbbf24;">{plan["nome"]} · {plan["dur_total"]}min · TSS {plan.get("tss_alvo", 0)}</div></div>'
    if cat == 'ciclismo':
        h += '<div style="display:grid;grid-template-columns:200px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;"><div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
        for b in plan['blocos']: h += build_bloco_treino(b)
        sups = calcular_suplementacao(plan['dur_total'])
        h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
        h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;">⚡ Nutrição</div>'
        h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:11px;">'
        h += f'<div><div style="color:#888;font-size:9px;">CARBOIDRATO</div><div style="color:#facc15;font-weight:700;font-size:14px;">{sups["carbo_g"]}g</div></div>'
        h += f'<div><div style="color:#888;font-size:9px;">ÁGUA</div><div style="color:#3b82f6;font-weight:700;font-size:14px;">{sups["agua_ml"]}ml</div></div>'
        h += f'<div><div style="color:#888;font-size:9px;">SÓDIO</div><div style="color:#ec4899;font-weight:700;font-size:14px;">{sups["sodio_mg"]}mg</div></div>'
        h += '</div></div>'
    else:
        for b in plan['blocos']:
            h += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;margin-top:6px;"><strong>{b["nome"]}</strong> · {b["dur"]}min'
            if 'detalhes' in b: h += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
            h += '</div>'
    h += '</div>'
    return h

def build_readiness_score(tsb, atl, ctl, historico):
    score = 50
    if tsb >= 6: score += 25
    elif -10 <= tsb <= 5: score += 15
    elif -30 <= tsb <= -11: score += 5
    else: score -= 20
    if len(historico) >= 3:
        atl_3d = historico[-3].get('atl', atl)
        if atl < atl_3d: score += 15
        elif atl > atl_3d * 1.05: score -= 10
    score += 10 if ctl >= 50 else (5 if ctl >= 35 else -5)
    score = max(0, min(100, score))
    if score >= 80: label, cor, status = 'PRONTO', '#4ade80', 'Ótimo para treino intenso'
    elif score >= 60: label, cor, status = 'BOM', '#86efac', 'Bom para treino moderado'
    elif score >= 40: label, cor, status = 'REGULAR', '#fbbf24', 'Prefira treino leve'
    else: label, cor, status = 'BAIXO', '#f87171', 'Recuperação recomendada'
    h  = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;border-left:3px solid {cor};">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
    h += f'<div style="font-size:12px;color:{cor};font-weight:600;text-transform:uppercase;letter-spacing:1px;">Readiness Score</div>'
    h += f'<div style="font-size:24px;font-weight:700;color:{cor};">{score}<span style="font-size:12px;color:#666;">/100</span></div></div>'
    h += f'<div style="background:#1a1a1a;border-radius:4px;height:6px;margin-bottom:8px;"><div style="background:{cor};width:{score}%;height:6px;border-radius:4px;"></div></div>'
    h += f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:10px;color:#888;">'
    h += f'<div>TSB: <span style="color:#ddd;">{tsb:+.1f}</span></div>'
    h += f'<div>ATL: <span style="color:#ddd;">{atl:.1f}</span></div>'
    h += f'<div>CTL: <span style="color:#ddd;">{ctl:.1f}</span></div></div>'
    h += f'<div style="margin-top:6px;font-size:11px;color:{cor};">{status}</div></div>'
    return h

def build_card_comparacao(analise, historico, treinos={}):
    hoje = datetime.now(); seg_atual = hoje - timedelta(days=hoje.weekday())
    def semana_stats(seg_ref):
        dom_ref = seg_ref + timedelta(days=6); tss = dist = mins = 0
        for t in treinos.values():
            try:
                dt = datetime.strptime(t.get('data', ''), '%Y-%m-%d')
                if seg_ref.date() <= dt.date() <= dom_ref.date():
                    tss += tss_treino(t); dist += t.get('distancia_km', 0); mins += t.get('duracao_min', 0)
            except: pass
        return round(tss, 1), round(dist, 1), round(mins / 60, 1)
    tss_a, dist_a, h_a = semana_stats(seg_atual)
    tss_p, dist_p, h_p = semana_stats(seg_atual - timedelta(days=7))
    medias = [semana_stats(seg_atual - timedelta(days=7*i)) for i in range(1, 5)]
    tss_m = round(sum(m[0] for m in medias) / 4, 1); dist_m = round(sum(m[1] for m in medias) / 4, 1); h_m = round(sum(m[2] for m in medias) / 4, 1)
    def cor(a, b): return '#888' if not b else ('#4ade80' if a >= b else '#f87171')
    def pct(a, b): return '+0%' if not b else f'{((a-b)/b*100):+.0f}%'
    h  = '<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;border-left:3px solid #3b82f6;">'
    h += '<div style="font-size:12px;color:#3b82f6;font-weight:600;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;">📊 Comparação Periódica</div>'
    h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;">'
    for label, atual, passada, media, un in [('TSS', tss_a, tss_p, tss_m, ''), ('DISTÂNCIA', dist_a, dist_p, dist_m, 'km'), ('HORAS', h_a, h_p, h_m, 'h')]:
        h += f'<div style="background:#1a1a1a;padding:8px;border-radius:6px;"><div style="color:#888;margin-bottom:4px;">{label}</div>'
        h += f'<div style="font-weight:700;color:#fff;font-size:13px;">{atual}{un}</div>'
        h += f'<div style="font-size:9px;color:{cor(atual,passada)};margin-top:2px;">vs semana: {pct(atual,passada)}</div>'
        h += f'<div style="font-size:9px;color:#888;margin-top:1px;">Média 4sem: {media}{un}</div></div>'
    h += '</div></div>'
    return h

def build_grafico_ctl_atl_tsb(historico):
    if not historico or len(historico) < 7: return ''
    dados = historico[-30:]; labels = [f"D{i}" for i in range(len(dados))]
    ctl_vals = [d.get('ctl', 0) for d in dados]; atl_vals = [d.get('atl', 0) for d in dados]
    tsb_vals = [d.get('tsb', 0) for d in dados]
    return f'''<div style="background:#0a0a0a;padding:12px;border-radius:8px;margin-bottom:12px;">
<canvas id="chart_ctl_atl" height="80"></canvas>
<script>
new Chart(document.getElementById('chart_ctl_atl'), {{
    type: 'line',
    data: {{labels: {labels},datasets: [
        {{label:'CTL',data:{ctl_vals},borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,0.1)',tension:0.3}},
        {{label:'ATL',data:{atl_vals},borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,0.1)',tension:0.3}},
        {{label:'TSB',data:{tsb_vals},borderColor:'#10b981',backgroundColor:'rgba(16,185,129,0.1)',tension:0.3}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,plugins:{{legend:{{display:true,position:'top'}}}},
    scales:{{y:{{beginAtZero:false,grid:{{color:'#333'}}}},x:{{grid:{{color:'#333'}}}}}}}}
}});
</script></div>'''

# ─── BUILD DASHBOARD v12 ───────────────────────────────────────────────────

def build_dashboard(treinos, wellness, fitness, estado, analytics_data={}):
    treinos_list = sorted(treinos.values(), key=lambda x: x.get('data', ''), reverse=True)
    wkg = round(FTP / PESO, 2)
    historico = calcular_wellness_historico(treinos)
    distrib = calcular_distribuicao(treinos)
    vo2_pot, melhor_5min = vo2max_potencia(treinos)
    label_pot, cor_pot = classificar_vo2(vo2_pot)

    bloco_atual = estado.get('bloco_atual', 'base')
    semana_no_bloco = estado.get('semana_no_bloco', 1)
    bloco_info = BLOCOS[bloco_atual]

    plano_atual = gerar_plano_semana_bloco(bloco_atual, semana_no_bloco)
    analise = analisar_semana_atual(treinos, plano_atual)

    ultimos_reais = [h for h in historico if not h.get('forecast')]
    ultimo = ultimos_reais[-1] if ultimos_reais else {'ctl': 36, 'atl': 54, 'tsb': -18, 'tss': 0}
    ctl, atl, tsb = ultimo['ctl'], ultimo['atl'], ultimo['tsb']

    if tsb <= -31: cor_tsb, forma_label = '#f87171', 'Alto Risco'
    elif -30 <= tsb <= -11: cor_tsb, forma_label = '#3b82f6', 'Evoluindo'
    elif -10 <= tsb <= 5: cor_tsb, forma_label = '#4ade80', 'Mantendo'
    elif 6 <= tsb <= 20: cor_tsb, forma_label = '#86efac', 'Descansando'
    else: cor_tsb, forma_label = '#fbbf24', 'Adaptando'

    prox_bloco, prox_semana, razoes_prox, forcou_rec = proxima_semana_periodizacao(
        estado, tsb, analise['aderencia_pct'], analise['treinos_perdidos'])
    plano_proxima = gerar_plano_semana_bloco(prox_bloco, prox_semana, tsb)
    bloco_prox_info = BLOCOS[prox_bloco]

    fase_label = 'BUILD' if semana_no_bloco < 4 else 'RECOVERY'
    fase_cor = '#fbbf24' if fase_label == 'BUILD' else '#10b981'

    # ── Aba Hoje ────────────────────────────────────────────────────────────
    hoje_dia = next((d for d in analise['dias'] if d.get('is_hoje')), None)
    prox_dia = None
    if hoje_dia:
        idx_h = analise['dias'].index(hoje_dia)
        if idx_h + 1 < len(analise['dias']):
            prox_dia = analise['dias'][idx_h + 1]

    plan_h = hoje_dia['plano'] if hoje_dia else {}
    sups_hoje = calcular_suplementacao(plan_h.get('dur_total', 0))

    # Card Hoje
    card_hoje_html = f'<div style="back
