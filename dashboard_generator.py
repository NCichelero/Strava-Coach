"""
🎨 DASHBOARD GENERATOR v11.7
- Timezone São Paulo (UTC-3) fixo
- Histórico inclui semana atual também
- Periodização em blocos (BASE → THRESHOLD → VO2MAX → INTEGRAÇÃO)
- Treinos específicos com nomes técnicos
- Microciclos 3+1 (3 build + 1 recovery)
- v11.7: Analytics avançado (Power Curve, Decoupling, Forecast, Teste FTP)
"""

import json
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import statistics

# v11.7: Analytics
from analytics import gerar_analytics_completo
from dashboard_cards_lite import build_aba_analytics

# ─── Configuração ──────────────────────────────────────────────────────────

FTP = 210
PESO = 75.6
FC_MAX = 190
FC_REPOUSO = 39
META_CTL = 45
TSS_META_SEMANA = 420

# Timezone São Paulo (UTC-3)
TZ_BRT = timezone(timedelta(hours=-3))

def agora():
    """Retorna datetime atual no horário de Brasília"""
    return datetime.now(TZ_BRT).replace(tzinfo=None)

ZONAS_FC = {
    'Z1': (115, 129),
    'Z2': (129, 145),
    'Z3': (145, 161),
    'Z4': (161, 176),
    'Z5': (176, 200),
}

# ─── PERIODIZAÇÃO EM BLOCOS ────────────────────────────────────────────────
# Macrociclo: 16 semanas (4 blocos de 4 semanas: 3 build + 1 recovery)

BLOCOS = {
    'base': {
        'nome': 'BASE AERÓBICA',
        'descricao': 'Construir capacidade aeróbica e eficiência metabólica',
        'foco': 'Sweet Spot + Endurance Z2 longo',
        'icone': '🏗️',
        'cor': '#3b82f6',
        'duracao_sem': 4,
        'distribuicao': '85% Z1-Z2 | 15% Z3 | 0% Z4-Z5',
        'objetivo': 'Aumentar CTL para 38-40 | Eficiência aeróbica'
    },
    'threshold': {
        'nome': 'THRESHOLD',
        'descricao': 'Empurrar o limiar funcional para cima',
        'foco': 'Intervalos no FTP + Over-Unders',
        'icone': '🎯',
        'cor': '#fbbf24',
        'duracao_sem': 4,
        'distribuicao': '80% Z1-Z2 | 5% Z3 | 15% Z4',
        'objetivo': 'Subir FTP +5W | Melhorar TTE'
    },
    'vo2max': {
        'nome': 'VO2MAX',
        'descricao': 'Levantar teto aeróbico para puxar o FTP',
        'foco': 'Intervalos curtos de alta intensidade',
        'icone': '🚀',
        'cor': '#f87171',
        'duracao_sem': 4,
        'distribuicao': '75% Z1-Z2 | 5% Z3 | 5% Z4 | 15% Z5',
        'objetivo': 'Aumentar VO2max + Pico 5min'
    },
    'integracao': {
        'nome': 'INTEGRAÇÃO',
        'descricao': 'Consolidar ganhos e testar novo FTP',
        'foco': 'Sweet Spot longo + simulações',
        'icone': '✨',
        'cor': '#10b981',
        'duracao_sem': 4,
        'distribuicao': '80% Z1-Z2 | 10% Z3 | 10% Z4',
        'objetivo': 'Estabilizar novo FTP | Re-testar'
    },
}

# Ordem dos blocos no macrociclo
ORDEM_BLOCOS = ['base', 'threshold', 'vo2max', 'integracao']

# ─── BIBLIOTECA DE TREINOS POR BLOCO ───────────────────────────────────────

def treinos_quarta_por_bloco(bloco, semana_no_bloco):
    """Treino-chave da quarta (mais técnico/intenso)"""
    if bloco == 'base':
        # Sweet Spot progressivo
        if semana_no_bloco == 1:
            return {
                'nome': '🍯 Sweet Spot 2x15min',
                'dur_total': 70, 'tss_alvo': 75,
                'blocos': [
                    {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS Bloco 1', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação ativa', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS Bloco 2', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2 + Cooldown', 'dur': 20, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2-Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '🍯 Sweet Spot 2x20min',
                'dur_total': 80, 'tss_alvo': 90,
                'blocos': [
                    {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS Bloco 1 (20min)', 'dur': 20, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação ativa', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS Bloco 2 (20min)', 'dur': 20, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Z2 + Cooldown', 'dur': 20, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2-Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🍯 Sweet Spot 3x15min',
                'dur_total': 90, 'tss_alvo': 105,
                'blocos': [
                    {'nome': 'Warm-up progressivo', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS Bloco 1', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS Bloco 2', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS Bloco 3', 'dur': 15, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Cooldown', 'dur': 20, 'pct_min': 0.45, 'pct_max': 0.60, 'zona': 'Z1'},
                ]}
        else:  # recovery
            return {
                'nome': '☘️ Z2 Recovery',
                'dur_total': 60, 'tss_alvo': 45,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}

    elif bloco == 'threshold':
        if semana_no_bloco == 1:
            return {
                'nome': '🎯 Threshold 2x15min @ 95% FTP',
                'dur_total': 80, 'tss_alvo': 95,
                'blocos': [
                    {'nome': 'Warm-up + 3 sprints curtos', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'Threshold 1', 'dur': 15, 'pct_min': 0.93, 'pct_max': 0.97, 'zona': 'Z4'},
                    {'nome': 'Recuperação completa', 'dur': 8, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1-Z2'},
                    {'nome': 'Threshold 2', 'dur': 15, 'pct_min': 0.93, 'pct_max': 0.97, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 17, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '🎯 Threshold 3x12min @ 98% FTP',
                'dur_total': 85, 'tss_alvo': 105,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'Threshold 1', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 6, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Threshold 2', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 6, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Threshold 3', 'dur': 12, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 22, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🎯 Threshold 2x20min @ 95-100% FTP',
                'dur_total': 90, 'tss_alvo': 115,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'Threshold 1 (20min)', 'dur': 20, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 8, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'Threshold 2 (20min)', 'dur': 20, 'pct_min': 0.95, 'pct_max': 1.00, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 27, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Recovery',
                'dur_total': 60, 'tss_alvo': 45,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}

    elif bloco == 'vo2max':
        if semana_no_bloco == 1:
            return {
                'nome': '🚀 VO2max 5x3min @ 115% FTP',
                'dur_total': 75, 'tss_alvo': 100,
                'blocos': [
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
            return {
                'nome': '🚀 30/30 Billat (8x4min)',
                'dur_total': 80, 'tss_alvo': 105,
                'blocos': [
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
            return {
                'nome': '🚀 VO2max 6x3min @ 118% FTP',
                'dur_total': 85, 'tss_alvo': 115,
                'blocos': [
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
            return {
                'nome': '☘️ Z2 Recovery (pós-VO2)',
                'dur_total': 60, 'tss_alvo': 45,
                'blocos': [
                    {'nome': 'Warm-up muito leve', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                    {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.58, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.45, 'zona': 'Z1'},
                ]}

    else:  # integracao
        if semana_no_bloco == 1:
            return {
                'nome': '🎯 Over-Under 4x6min',
                'dur_total': 80, 'tss_alvo': 105,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'OU #1 (3min @ 90%, 3min @ 105%)', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #2', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #3', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #4', 'dur': 6, 'pct_min': 0.88, 'pct_max': 1.07, 'zona': 'Z3-Z4'},
                    {'nome': 'Cooldown', 'dur': 29, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '🎯 Sweet Spot 2x25min',
                'dur_total': 95, 'tss_alvo': 115,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS longo 1 (25min)', 'dur': 25, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recuperação ativa', 'dur': 8, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'SS longo 2 (25min)', 'dur': 25, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Cooldown', 'dur': 22, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🧪 TESTE FTP - 20min All-out',
                'dur_total': 75, 'tss_alvo': 100,
                'blocos': [
                    {'nome': 'Warm-up amplo', 'dur': 25, 'pct_min': 0.50, 'pct_max': 0.80, 'zona': 'Z1-Z3'},
                    {'nome': '5min @ 90% FTP', 'dur': 5, 'pct_min': 0.88, 'pct_max': 0.92, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 10, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '⚡ 20min MAX', 'dur': 20, 'pct_min': 1.00, 'pct_max': 1.10, 'zona': 'Z4-Z5'},
                    {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Recovery + Re-test',
                'dur_total': 60, 'tss_alvo': 45,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 leve', 'dur': 40, 'pct_min': 0.58, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}


def treinos_sexta_por_bloco(bloco, semana_no_bloco):
    """Treino-chave da sexta (complementar à quarta)"""
    if bloco == 'base':
        if semana_no_bloco == 1:
            return {
                'nome': '🍯 Sweet Spot 3x10min',
                'dur_total': 75, 'tss_alvo': 80,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS #1', 'dur': 10, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #2', 'dur': 10, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #3', 'dur': 10, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Z2 + Cooldown', 'dur': 20, 'pct_min': 0.55, 'pct_max': 0.65, 'zona': 'Z2-Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '🍯 Sweet Spot 3x12min',
                'dur_total': 80, 'tss_alvo': 90,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS #1', 'dur': 12, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #2', 'dur': 12, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #3', 'dur': 12, 'pct_min': 0.86, 'pct_max': 0.91, 'zona': 'Z3'},
                    {'nome': 'Cooldown', 'dur': 19, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🍯 Sweet Spot 4x10min',
                'dur_total': 85, 'tss_alvo': 100,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 12, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'SS #1', 'dur': 10, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #2', 'dur': 10, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #3', 'dur': 10, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.50, 'pct_max': 0.60, 'zona': 'Z1'},
                    {'nome': 'SS #4', 'dur': 10, 'pct_min': 0.88, 'pct_max': 0.93, 'zona': 'Z3'},
                    {'nome': 'Cooldown', 'dur': 21, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Endurance',
                'dur_total': 60, 'tss_alvo': 50,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2 Endurance', 'dur': 40, 'pct_min': 0.62, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}

    elif bloco == 'threshold':
        if semana_no_bloco == 1:
            return {
                'nome': '⚙️ Over-Under 3x8min',
                'dur_total': 80, 'tss_alvo': 95,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'OU #1 (4×1min @ 105%, 1min @ 95%)', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #2', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #3', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 31, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '⚙️ Criss-Cross 3x10min',
                'dur_total': 85, 'tss_alvo': 100,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'CC #1 (1min @ 108%, 1min @ 92%)', 'dur': 10, 'pct_min': 0.90, 'pct_max': 1.10, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'CC #2', 'dur': 10, 'pct_min': 0.90, 'pct_max': 1.10, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'CC #3', 'dur': 10, 'pct_min': 0.90, 'pct_max': 1.10, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 30, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '⚙️ Over-Under 4x8min',
                'dur_total': 90, 'tss_alvo': 110,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 12, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'OU #1', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #2', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #3', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Recup', 'dur': 4, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'OU #4', 'dur': 8, 'pct_min': 0.93, 'pct_max': 1.07, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 34, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Endurance',
                'dur_total': 60, 'tss_alvo': 50,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2', 'dur': 40, 'pct_min': 0.62, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}

    elif bloco == 'vo2max':
        if semana_no_bloco == 1:
            return {
                'nome': '🚀 30/15 Rønnestad (3x13)',
                'dur_total': 80, 'tss_alvo': 100,
                'blocos': [
                    {'nome': 'Warm-up + sprints', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                    {'nome': '13× (30s @ 115%, 15s @ 60%)', 'dur': 10, 'pct_min': 0.60, 'pct_max': 1.18, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '13× (30/15)', 'dur': 10, 'pct_min': 0.60, 'pct_max': 1.18, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '13× (30/15)', 'dur': 10, 'pct_min': 0.60, 'pct_max': 1.18, 'zona': 'Z5'},
                    {'nome': 'Cooldown', 'dur': 27, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '🚀 VO2max 4x4min @ 110% FTP',
                'dur_total': 80, 'tss_alvo': 105,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                    {'nome': 'VO2max #1', 'dur': 4, 'pct_min': 1.08, 'pct_max': 1.13, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'VO2max #2', 'dur': 4, 'pct_min': 1.08, 'pct_max': 1.13, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'VO2max #3', 'dur': 4, 'pct_min': 1.08, 'pct_max': 1.13, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 4, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'VO2max #4', 'dur': 4, 'pct_min': 1.08, 'pct_max': 1.13, 'zona': 'Z5'},
                    {'nome': 'Cooldown', 'dur': 37, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🚀 Bossi Mix 3x10min',
                'dur_total': 85, 'tss_alvo': 110,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.75, 'zona': 'Z1-Z2'},
                    {'nome': 'Bossi #1 (alterna 30s @ 120% / 30s @ 77%)', 'dur': 10, 'pct_min': 0.75, 'pct_max': 1.22, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Bossi #2', 'dur': 10, 'pct_min': 0.75, 'pct_max': 1.22, 'zona': 'Z5'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Bossi #3', 'dur': 10, 'pct_min': 0.75, 'pct_max': 1.22, 'zona': 'Z5'},
                    {'nome': 'Cooldown', 'dur': 30, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Recovery',
                'dur_total': 60, 'tss_alvo': 45,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                    {'nome': 'Z2 leve', 'dur': 40, 'pct_min': 0.58, 'pct_max': 0.65, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.45, 'zona': 'Z1'},
                ]}

    else:  # integracao
        if semana_no_bloco == 1:
            return {
                'nome': '⚙️ Threshold 3x10min @ FTP',
                'dur_total': 75, 'tss_alvo': 90,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': 'Threshold #1', 'dur': 10, 'pct_min': 0.97, 'pct_max': 1.02, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Threshold #2', 'dur': 10, 'pct_min': 0.97, 'pct_max': 1.02, 'zona': 'Z4'},
                    {'nome': 'Recuperação', 'dur': 5, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Threshold #3', 'dur': 10, 'pct_min': 0.97, 'pct_max': 1.02, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 20, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 2:
            return {
                'nome': '⚡ Race Sim 30min @ FTP',
                'dur_total': 75, 'tss_alvo': 95,
                'blocos': [
                    {'nome': 'Warm-up + ativação', 'dur': 20, 'pct_min': 0.50, 'pct_max': 0.80, 'zona': 'Z1-Z3'},
                    {'nome': '⚡ 30min sustentado @ FTP', 'dur': 30, 'pct_min': 0.98, 'pct_max': 1.03, 'zona': 'Z4'},
                    {'nome': 'Cooldown', 'dur': 25, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        elif semana_no_bloco == 3:
            return {
                'nome': '🧪 Pré-teste tune-up',
                'dur_total': 60, 'tss_alvo': 55,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.50, 'pct_max': 0.70, 'zona': 'Z1-Z2'},
                    {'nome': '5min @ 85% (ativação)', 'dur': 5, 'pct_min': 0.83, 'pct_max': 0.88, 'zona': 'Z3'},
                    {'nome': 'Recuperação', 'dur': 10, 'pct_min': 0.45, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': '2× 1min @ 110%', 'dur': 5, 'pct_min': 0.50, 'pct_max': 1.10, 'zona': 'Z5'},
                    {'nome': 'Cooldown', 'dur': 25, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                ]}
        else:
            return {
                'nome': '☘️ Z2 Endurance',
                'dur_total': 60, 'tss_alvo': 50,
                'blocos': [
                    {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                    {'nome': 'Z2', 'dur': 40, 'pct_min': 0.62, 'pct_max': 0.70, 'zona': 'Z2'},
                    {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
                ]}


def treino_segunda_recovery(semana_no_bloco):
    """Segunda — Z2 puro (recovery ativo)"""
    if semana_no_bloco == 4:  # recovery week
        return {
            'nome': '☘️ Z2 Spin Leve',
            'dur_total': 50, 'tss_alvo': 35,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 baixa', 'dur': 30, 'pct_min': 0.55, 'pct_max': 0.62, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}
    return {
        'nome': '☘️ Z2 Endurance Aeróbico',
        'dur_total': 70, 'tss_alvo': 55,
        'blocos': [
            {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
            {'nome': 'Z2 Endurance', 'dur': 50, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
            {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
        ]}


def treino_sabado_longo(bloco, semana_no_bloco):
    """Sábado — Longo (com ou sem trabalho de intensidade dependendo do bloco)"""
    if semana_no_bloco == 4:  # recovery
        return {
            'nome': '☘️ Endurance Z2 (recovery week)',
            'dur_total': 90, 'tss_alvo': 75,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 10, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 70, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 10, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}

    if bloco == 'base':
        # Longo Z2 puro com toque de SS
        return {
            'nome': '🏞️ Long Ride Z2 + Sweet Spot',
            'dur_total': 180, 'tss_alvo': 175,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 75, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
                {'nome': 'SS embedido (15min)', 'dur': 15, 'pct_min': 0.85, 'pct_max': 0.90, 'zona': 'Z3'},
                {'nome': 'Z2 Endurance', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.72, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
    elif bloco == 'threshold':
        return {
            'nome': '🏞️ Long Ride + 2x Tempo',
            'dur_total': 180, 'tss_alvo': 190,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.60, 'zona': 'Z1'},
                {'nome': 'Z2', 'dur': 60, 'pct_min': 0.65, 'pct_max': 0.75, 'zona': 'Z2'},
                {'nome': 'Tempo #1 (15min)', 'dur': 15, 'pct_min': 0.80, 'pct_max': 0.88, 'zona': 'Z3'},
                {'nome': 'Z2 Recovery', 'dur': 15, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                {'nome': 'Tempo #2 (15min)', 'dur': 15, 'pct_min': 0.80, 'pct_max': 0.88, 'zona': 'Z3'},
                {'nome': 'Z2', 'dur': 45, 'pct_min': 0.60, 'pct_max': 0.70, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.55, 'zona': 'Z1'},
            ]}
    elif bloco == 'vo2max':
        # No bloco VO2max o longo é puro Z2 (recovery do meio da semana)
        return {
            'nome': '🏞️ Long Z2 (recovery dos VO2)',
            'dur_total': 180, 'tss_alvo': 160,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance fundo', 'dur': 150, 'pct_min': 0.62, 'pct_max': 0.70, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}
    else:  # integracao
        return {
            'nome': '🏞️ Race Simulation',
            'dur_total': 180, 'tss_alvo': 200,
            'blocos': [
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
    """Domingo — Adaptativo baseado em TSB e bloco"""
    if semana_no_bloco == 4 or tsb < -20:
        return {
            'nome': '😴 Descanso ou Caminhada',
            'tipo': 'recuperacao', 'horario': '—',
            'dur_total': 0, 'tss_alvo': 0,
            'blocos': [{'nome': 'Descanso total ou caminhada leve 30min', 'dur': 0, 'detalhes': 'Recuperação obrigatória'}]
        }

    if bloco in ('base', 'integracao'):
        return {
            'nome': '🌅 Endurance Z2 Suave',
            'tipo': 'ciclismo', 'horario': '07:00',
            'dur_total': 120, 'tss_alvo': 100,
            'blocos': [
                {'nome': 'Warm-up', 'dur': 15, 'pct_min': 0.40, 'pct_max': 0.55, 'zona': 'Z1'},
                {'nome': 'Z2 Endurance', 'dur': 90, 'pct_min': 0.60, 'pct_max': 0.68, 'zona': 'Z2'},
                {'nome': 'Cooldown', 'dur': 15, 'pct_min': 0.35, 'pct_max': 0.50, 'zona': 'Z1'},
            ]}
    return {
        'nome': '😴 Recovery Day',
        'tipo': 'recuperacao', 'horario': '—',
        'dur_total': 0, 'tss_alvo': 0,
        'blocos': [{'nome': 'Descanso ou caminhada leve', 'dur': 30, 'detalhes': 'Sem bike — recuperar para próximo bloco'}]
    }


def gerar_plano_semana_bloco(bloco, semana_no_bloco, tsb=0):
    """
    Gera plano semanal completo baseado no bloco e semana no bloco.
    semana_no_bloco: 1, 2, 3 = build / 4 = recovery
    """
    plano = {}

    # Segunda — Z2 (sempre tranquilo)
    seg = treino_segunda_recovery(semana_no_bloco)
    seg['tipo'] = 'ciclismo'
    seg['horario'] = '05:30'
    plano[0] = seg

    # Terça — Academia
    plano[1] = {
        'nome': '🏋️ Academia - Superiores',
        'tipo': 'academia', 'horario': '—',
        'dur_total': 60, 'tss_alvo': 0,
        'blocos': [{'nome': 'Peito + Tríceps + Ombro + Core', 'dur': 60, 'detalhes': '4 séries 8-12 reps · Foco em hipertrofia'}]
    }

    # Quarta — Treino-chave 1
    quarta = treinos_quarta_por_bloco(bloco, semana_no_bloco)
    quarta['tipo'] = 'ciclismo'
    quarta['horario'] = '05:30'
    plano[2] = quarta

    # Quinta — Academia
    plano[3] = {
        'nome': '🏋️ Academia - Inferiores',
        'tipo': 'academia', 'horario': '—',
        'dur_total': 60, 'tss_alvo': 0,
        'blocos': [{'nome': 'Pernas + Glúteo + Core', 'dur': 60, 'detalhes': 'Agachamento + Leg press + Stiff + Panturrilha'}]
    }

    # Sexta — Treino-chave 2
    sexta = treinos_sexta_por_bloco(bloco, semana_no_bloco)
    sexta['tipo'] = 'ciclismo'
    sexta['horario'] = '05:30'
    plano[4] = sexta

    # Sábado — Longo
    sab = treino_sabado_longo(bloco, semana_no_bloco)
    sab['tipo'] = 'ciclismo'
    sab['horario'] = '07:00'
    plano[5] = sab

    # Domingo — Adaptativo
    plano[6] = treino_domingo(bloco, semana_no_bloco, tsb)

    return plano


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
    
    # v11.7: Gerar analytics
    print("📊 Gerando analytics...")
    analytics_data = gerar_analytics_completo()
    
    return treinos, wellness, fitness, estado, analytics_data

def save_estado(estado):
    os.makedirs('data', exist_ok=True)
    with open('data/estado.json', 'w', encoding='utf-8') as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

# ─── Zonas + métricas ──────────────────────────────────────────────────────

def zona_por_fc(fc):
    if fc <= 0: return '—'
    if fc < 129: return 'Z1'
    if fc < 145: return 'Z2'
    if fc < 161: return 'Z3'
    if fc < 176: return 'Z4'
    return 'Z5'

def zona_treino(t):
    if t.get('categoria') != 'ciclismo': return '—'
    fc = t.get('fc_avg', 0)
    pot = t.get('potencia_avg', 0)
    if fc > 50: return zona_por_fc(fc)
    if pot > 50:
        pct = pot / FTP
        if pct < 0.55: return 'Z1'
        elif pct < 0.75: return 'Z2'
        elif pct < 0.90: return 'Z3'
        elif pct < 1.05: return 'Z4'
        else: return 'Z5'
    return '—'

def vo2max_fc():
    if FC_REPOUSO <= 0: return 0
    return round(15 * (FC_MAX / FC_REPOUSO), 1)

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
        if pot_avg > 50 and fc_avg > 0: ne = min(10, (pot_avg / fc_avg) * 8)
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
    if pot_norm > 50: return round(dur * (pot_norm / FTP) ** 2 * 100 / 60, 1)
    elif fc_avg > 0: return round(dur * (fc_avg / FC_MAX) ** 2 * 100 / 60, 1)
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
    tss_diario = defaultdict(float)
    for t in treinos.values():
        data = t.get('data', '')
        if not data: continue
        tss_diario[data] += tss_treino(t)
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
    plano_tss = {0: 70, 1: 0, 2: 100, 3: 0, 4: 95, 5: 180, 6: 100}
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

# ─── Análise Semana Atual ──────────────────────────────────────────────────

def analisar_semana_passada(treinos, plano):
    """Igual analisar_semana_atual mas para a semana anterior"""
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

    treinos_planejados_cic = 0
    treinos_perdidos = 0
    treinos_feitos = 0

    for wd in range(7):
        plan = plano[wd]
        realizados = realizados_por_dia.get(wd, [])
        if plan['tipo'] == 'ciclismo':
            treinos_planejados_cic += 1
            if realizados:
                cats_real = [t.get('categoria') for t in realizados]
                if plan['tipo'] in cats_real:
                    treinos_feitos += 1
                else:
                    treinos_perdidos += 1
            else:
                treinos_perdidos += 1

    aderencia_pct = round((treinos_feitos / max(treinos_planejados_cic, 1)) * 100)
    return {'aderencia_pct': aderencia_pct, 'treinos_perdidos': treinos_perdidos}


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

        is_passado = dia_dt.date() < hoje.date()
        is_hoje = dia_dt.date() == hoje.date()
        is_futuro = dia_dt.date() > hoje.date()

        if is_futuro:
            status, icone, cor = 'futuro', '⏳', '#6b7280'
        elif realizados:
            cats_real = [t.get('categoria') for t in realizados]
            if plan['tipo'] in cats_real or plan['tipo'] == 'recuperacao':
                status, icone, cor = 'realizado', '✅', '#4ade80'
                if plan['tipo'] == 'ciclismo': treinos_feitos += 1
            else:
                status, icone, cor = 'parcial', '⚠️', '#facc15'
        elif plan['tipo'] == 'recuperacao':
            status, icone, cor = 'realizado', '✅', '#4ade80'
        elif is_hoje:
            status, icone, cor = 'hoje', '🎯', '#3b82f6'
        else:
            status, icone, cor = 'perdido', '❌', '#f87171'
            if plan['tipo'] == 'ciclismo': treinos_perdidos += 1

        resultado.append({
            'weekday': wd, 'data': dia_dt.strftime('%Y-%m-%d'),
            'plano': plan, 'realizados': realizados,
            'tss_real': round(tss_real_dia, 1), 'tss_alvo': plan.get('tss_alvo', 0),
            'status': status, 'icone': icone, 'cor_status': cor,
            'is_hoje': is_hoje, 'is_passado': is_passado,
        })

    treinos_cic_avaliados = sum(1 for r in resultado
                                if (r['is_passado'] or r['is_hoje']) and r['plano']['tipo'] == 'ciclismo')
    if treinos_cic_avaliados > 0:
        feitos = sum(1 for r in resultado
                    if (r['is_passado'] or r['is_hoje'])
                    and r['plano']['tipo'] == 'ciclismo' and r['status'] == 'realizado')
        aderencia_pct = round((feitos / treinos_cic_avaliados) * 100)
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

# ─── Decisão Próxima Semana ────────────────────────────────────────────────

def proxima_semana_periodizacao(estado, tsb, aderencia_pct, treinos_perdidos):
    """
    Decide bloco e semana_no_bloco da próxima semana.
    Mantém periodização mas adapta se aderência ruim.
    """
    bloco_atual = estado.get('bloco_atual', 'base')
    semana_atual = estado.get('semana_no_bloco', 1)

    razoes = []
    forcou_recovery = False

    # Determina próxima semana naturalmente
    if semana_atual < 4:
        prox_semana = semana_atual + 1
        prox_bloco = bloco_atual
    else:
        # Termina o bloco — passa pro próximo
        idx = ORDEM_BLOCOS.index(bloco_atual)
        prox_bloco = ORDEM_BLOCOS[(idx + 1) % len(ORDEM_BLOCOS)]
        prox_semana = 1
        razoes.append(f'🎉 Bloco {BLOCOS[bloco_atual]["nome"]} finalizado → iniciando {BLOCOS[prox_bloco]["nome"]}')

    # Ajustes adaptativos (sobrescreve se necessário)
    if treinos_perdidos >= 2:
        prox_semana = 4  # força recovery
        forcou_recovery = True
        razoes.append(f'⚠️ {treinos_perdidos} treinos perdidos → semana 4 (recovery)')

    if tsb < -25:
        prox_semana = 4
        forcou_recovery = True
        razoes.append(f'🔴 TSB {tsb:.0f} crítico → recovery obrigatório')

    if aderencia_pct < 60:
        prox_semana = 4
        forcou_recovery = True
        razoes.append(f'⚠️ Aderência baixa ({aderencia_pct}%) → recovery')

    if not razoes:
        if prox_semana == 4:
            razoes.append(f'✅ Semana de recovery planejada (final do bloco {BLOCOS[prox_bloco]["nome"]})')
        else:
            razoes.append(f'📈 Progredindo no bloco {BLOCOS[prox_bloco]["nome"]} (semana {prox_semana}/4)')

    return prox_bloco, prox_semana, razoes, forcou_recovery


# ─── Suplementação ─────────────────────────────────────────────────────────

def calcular_suplementacao(dur_min):
    """Retorna apenas carboidrato, água e sódio necessários"""
    if dur_min < 60:
        return {
            'carbo_g': 0,
            'agua_ml': 400,
            'sodio_mg': 200
        }
    elif dur_min < 90:
        return {
            'carbo_g': 50,  # Pré: ~50g
            'agua_ml': 600,  # Durante: 500ml
            'sodio_mg': 300
        }
    elif dur_min < 150:
        return {
            'carbo_g': 100,  # Pré: 50g + Durante: 30g + 30g
            'agua_ml': 1200,  # 500ml + 500ml + 200ml
            'sodio_mg': 500
        }
    else:  # >= 150min
        carbo = 50 + (60 * ((dur_min - 90) // 30))  # Dinâmico por duração
        agua = 600 + (500 * ((dur_min - 90) // 30))
        sodio = 600 if dur_min < 180 else 800
        return {
            'carbo_g': carbo,
            'agua_ml': agua,
            'sodio_mg': sodio
        }

# ─── Distribuição zonas ────────────────────────────────────────────────────

def calcular_distribuicao(treinos):
    quatro_sem = (agora() - timedelta(days=28)).strftime('%Y-%m-%d')
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
        modelo, cor, desc = '🎯 Polarizado 80/20', '#10b981', 'Distribuição ideal: muito Z2 + intervalados Z4/Z5'
    elif media >= 30:
        modelo, cor, desc = '⚠️ Piramidal (excesso Z3)', '#facc15', 'Muito Z3. Pode causar fadiga acumulada'
    elif baixa >= 90:
        modelo, cor, desc = '📉 Sub-polarizado', '#9ca3af', 'Falta intensidade. Adicione intervalados Z4/Z5'
    else:
        modelo, cor, desc = '⚖️ Equilibrado', '#3b82f6', 'Distribuição mista'
    return {'pcts': pcts, 'total_min': round(total), 'modelo': modelo, 'cor': cor,
            'descricao': desc, 'baixa': baixa, 'media': media, 'alta': alta}

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
    n = len(scores); x = list(range(n))
    mx, my = sum(x) / n, sum(scores) / n
    num = sum((x[i] - mx) * (scores[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den == 0: return None, None, None
    slope = num / den
    ganho = slope * 0.3
    if ganho <= 0: return None, None, None
    return 220 - FTP, round((220 - FTP) / ganho), round(ganho, 1)

# ─── Helpers UI ────────────────────────────────────────────────────────────

def watts_pct(pmin, pmax): return f"{int(FTP * pmin)}-{int(FTP * pmax)}W"
def fc_zona_str(z):
    if z in ZONAS_FC:
        lo, hi = ZONAS_FC[z]
        return f"{lo}-{hi}bpm"
    return "—"
def cor_zona(z):
    return {'Z1': '#9ca3af', 'Z2': '#4ade80', 'Z3': '#facc15', 'Z4': '#fb923c', 'Z5': '#f87171'}.get(z, '#888')

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
    nota = calcular_nota(t)
    zona = zona_treino(t)
    tss_t = tss_treino(t)
    if_v = if_treino(t)
    vi_v = vi_treino(t)
    laps_t = t.get('laps', [])
    pico5 = t.get('pico_5min', 0)

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
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">'
    h += f'<div style="display:flex;align-items:center;gap:8px;">'
    h += f'<span style="font-size:18px;">{icone}</span>'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon_cat} {dias_pt[dia_info["weekday"]]}'
    if is_hoje: h += ' <span style="color:#3b82f6;font-size:10px;margin-left:4px;">▶ HOJE</span>'
    h += f' <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div>'
    h += f'</div>'
    h += f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">'
    h += f'<span style="font-size:10px;color:{cor_status};font-weight:600;padding:3px 8px;background:{cor_status}22;border-radius:4px;">{status.upper()}</span>'
    h += f'<span style="font-size:11px;color:#fbbf24;">{plan["nome"]}</span>'
    h += f'</div>'
    h += f'</div>'

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

    if realizados:
        h += '<div style="margin-top:10px;">'
        h += '<div style="font-size:10px;color:#4ade80;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">✅ Realizado</div>'
        for j, t in enumerate(realizados):
            uid = f"atual-{idx}-{j}"
            h += build_treino_realizado_inline(t, uid)
        h += '</div>'

    mostrar_plano = (status in ['futuro', 'hoje', 'perdido', 'parcial']) and cat == 'ciclismo'
    if mostrar_plano:
        h += '<div style="margin-top:10px;">'
        if status == 'realizado':
            h += '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">📋 Plano original</div>'
        else:
            h += '<div style="font-size:10px;color:#fbbf24;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600;">📋 Plano</div>'
        h += '<div style="display:grid;grid-template-columns:200px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;">'
        h += '<div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
        for b in plan['blocos']:
            h += build_bloco_treino(b)
        h += '</div>'
        if is_hoje and cat == 'ciclismo':
            sups = calcular_suplementacao(plan['dur_total'])
            h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
            h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">⚡ Nutrição Necessária</div>'
            h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:11px;">'
            h += f'<div><div style="color:#888;font-size:9px;">CARBOIDRATO</div><div style="color:#facc15;font-weight:700;font-size:14px;">{sups["carbo_g"]}g</div></div>'
            h += f'<div><div style="color:#888;font-size:9px;">ÁGUA</div><div style="color:#3b82f6;font-weight:700;font-size:14px;">{sups["agua_ml"]}ml</div></div>'
            h += f'<div><div style="color:#888;font-size:9px;">SÓDIO</div><div style="color:#ec4899;font-weight:700;font-size:14px;">{sups["sodio_mg"]}mg</div></div>'
            h += '</div>'
            h += '</div>'
    elif cat == 'academia' and not realizados:
        for b in plan['blocos']:
            h += f'<div style="font-size:11px;color:#ddd;padding:8px;background:#1a1a1a;border-radius:4px;margin-top:6px;">'
            h += f'<strong>{b["nome"]}</strong> · {b["dur"]}min'
            if 'detalhes' in b: h += f'<br><span style="color:#888;font-size:10px;">{b["detalhes"]}</span>'
            h += '</div>'
    h += '</div>'
    return h

def build_dia_proxima(wd, plan):
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    cat = plan['tipo']
    icon = '🚴' if cat == 'ciclismo' else ('🏋️' if cat == 'academia' else '😴')
    cor = '#3b82f6' if cat == 'ciclismo' else ('#a855f7' if cat == 'academia' else '#6b7280')
    h = f'<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:10px;border-left:3px solid {cor};">'
    h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px;">'
    h += f'<div style="font-size:13px;color:#ddd;font-weight:600;">{icon} {dias_pt[wd]} <span style="color:#888;font-weight:400;margin-left:6px;font-size:11px;">{plan["horario"]}</span></div>'
    h += f'<div style="font-size:11px;color:#fbbf24;">{plan["nome"]} · {plan["dur_total"]}min · TSS {plan.get("tss_alvo", 0)}</div>'
    h += f'</div>'
    if cat == 'ciclismo':
        h += '<div style="display:grid;grid-template-columns:200px 60px 1fr 1fr 90px;gap:8px;font-size:10px;color:#666;padding:4px 8px;background:#1a1a1a;border-radius:4px;margin-bottom:4px;">'
        h += '<div>BLOCO</div><div>TEMPO</div><div>POTÊNCIA</div><div>% FTP</div><div>ZONA FC</div></div>'
        for b in plan['blocos']:
            h += build_bloco_treino(b)
        sups = calcular_suplementacao(plan['dur_total'])
        h += '<div style="margin-top:12px;padding:10px;background:#1a1a1a;border-radius:6px;border-left:3px solid #fbbf24;">'
        h += '<div style="font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">⚡ Nutrição Necessária</div>'
        h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:11px;">'
        h += f'<div><div style="color:#888;font-size:9px;">CARBOIDRATO</div><div style="color:#facc15;font-weight:700;font-size:14px;">{sups["carbo_g"]}g</div></div>'
        h += f'<div><div style="color:#888;font-size:9px;">ÁGUA</div><div style="color:#3b82f6;font-weight:700;font-size:14px;">{sups["agua_ml"]}ml</div></div>'
        h += f'<div><div style="color:#888;font-size:9px;">SÓDIO</div><div style="color:#ec4899;font-weight:700;font-size:14px;">{sups["sodio_mg"]}mg</div></div>'
        h += '</div>'
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




# ─── Build Card Comparação Periódica ─────────────────────────────────────

def build_card_comparacao(analise, historico, treinos={}):
    """Compara esta semana vs semana passada vs média 4 semanas"""
    from datetime import datetime, timedelta
    
    hoje = datetime.now()
    seg_atual = hoje - timedelta(days=hoje.weekday())
    
    def semana_stats(seg_ref):
        dom_ref = seg_ref + timedelta(days=6)
        tss = dist = mins = 0
        for t in treinos.values():
            try:
                dt = datetime.strptime(t.get('data', ''), '%Y-%m-%d')
                if seg_ref.date() <= dt.date() <= dom_ref.date():
                    tss  += t.get('tss', 0)
                    dist += t.get('dist', 0)
                    mins += t.get('tempo', 0)
            except:
                pass
        return round(tss, 1), round(dist, 1), round(mins / 60, 1)
    
    tss_a, dist_a, h_a = semana_stats(seg_atual)
    tss_p, dist_p, h_p = semana_stats(seg_atual - timedelta(days=7))
    
    medias = [semana_stats(seg_atual - timedelta(days=7*i)) for i in range(1, 5)]
    tss_m  = round(sum(m[0] for m in medias) / 4, 1)
    dist_m = round(sum(m[1] for m in medias) / 4, 1)
    h_m    = round(sum(m[2] for m in medias) / 4, 1)
    
    def cor(a, b):
        if not b: return '#888'
        return '#4ade80' if a >= b else '#f87171'
    
    def pct(a, b):
        if not b: return '+0%'
        return f'{((a-b)/b*100):+.0f}%'
    
    h  = '<div style="background:#0a0a0a;padding:14px;border-radius:8px;margin-bottom:14px;border-left:3px solid #3b82f6;">'
    h += '<div style="font-size:12px;color:#3b82f6;font-weight:600;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px;">📊 Comparação Periódica</div>'
    h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;">'
    
    for label, atual, passada, media, un in [
        ('TSS',       tss_a, tss_p, tss_m, ''),
        ('DISTÂNCIA', dist_a, dist_p, dist_m, 'km'),
        ('HORAS',     h_a, h_p, h_m, 'h'),
    ]:
        h += f'<div style="background:#1a1a1a;padding:8px;border-radius:6px;">'
        h += f'<div style="color:#888;margin-bottom:4px;">{label}</div>'
        h += f'<div style="font-weight:700;color:#fff;font-size:13px;">{atual}{un}</div>'
        h += f'<div style="font-size:9px;color:{cor(atual,passada)};margin-top:2px;">vs semana: {pct(atual,passada)}</div>'
        h += f'<div style="font-size:9px;color:#888;margin-top:1px;">Média 4sem: {media}{un}</div>'
        h += '</div>'
    
    h += '</div></div>'
    return h


def build_card_hoje(analise, sups_dict, plano_proxima=None):
    """Card rápido: treino de hoje + próximo (pode estar na próxima semana)"""
    hoje = None
    proximo = None
    
    # Verificar se analise tem 'dias'
    if 'dias' not in analise or not analise['dias']:
        return '<div style="background:linear-gradient(135deg,#3b82f6,#1e40af);padding:16px;border-radius:10px;margin-bottom:14px;color:white;"><div style="font-size:12px;opacity:0.8;">⏰ Sem dados</div></div>'
    
    dias = analise['dias']
    encontrou_hoje = False
    
    # Procurar hoje
    for i, dia in enumerate(dias):
        if dia.get('is_hoje'):
            hoje = dia
            encontrou_hoje = True
            # Próximo é o dia logo depois
            if i + 1 < len(dias):
                proximo = dias[i + 1]
            break
    
    # Se não encontrou próximo na semana atual, pegar da próxima semana
    if not proximo and plano_proxima and encontrou_hoje:
        # próximo é o primeiro dia da próxima semana
        for wd, plano in plano_proxima.items():
            if plano.get('nome'):  # Verificar que tem plano válido
                proximo = {'plano': plano}
                break
    
    h = '<div style="background:linear-gradient(135deg,#3b82f6,#1e40af);padding:16px;border-radius:10px;margin-bottom:14px;color:white;">'
    h += '<div style="font-size:12px;opacity:0.8;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">⏰ Hoje</div>'
    
    if hoje:
        plan = hoje.get('plano', {})
        h += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        h += f'<div><div style="font-size:14px;font-weight:700;">{plan.get("nome", "Treino")}</div>'
        h += f'<div style="font-size:11px;opacity:0.8;">{plan.get("horario", "--")} · {plan.get("dur_total", 0)}min</div></div>'
        h += f'<div style="text-align:right;font-size:11px;"><strong>TSS</strong> {plan.get("tss_alvo", 0)}</div>'
        h += f'</div>'
        
        if plan.get('tipo') == 'ciclismo' and sups_dict:
            h += f'<div style="background:rgba(255,255,255,0.1);padding:8px;border-radius:6px;margin-bottom:8px;font-size:10px;">'
            h += f'<strong>Nutrição:</strong> {sups_dict.get("carbo_g", 0)}g carbo · {sups_dict.get("agua_ml", 0)}ml água · {sups_dict.get("sodio_mg", 0)}mg sódio'
            h += f'</div>'
    else:
        h += '<div style="font-size:12px;color:#ddd;">Nenhum treino hoje</div>'
    
    # PRÓXIMO TREINO
    if proximo:
        plan_prox = proximo.get('plano', {})
        h += f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.2);font-size:11px;">'
        h += f'<div style="opacity:0.8;margin-bottom:4px;">👉 Próximo:</div>'
        h += f'<div style="font-weight:700;">{plan_prox.get("nome", "Treino")} ({plan_prox.get("horario", "--")})</div>'
        h += f'<div style="opacity:0.7;font-size:10px;margin-top:2px;">TSS {plan_prox.get("tss_alvo", 0)} · {plan_prox.get("dur_total", 0)}min</div>'
        h += f'</div>'
    
    h += '</div>'
    return h

# ─── Build Alerts ────────────────────────────────────────────────────────────

def build_alerts(tsb, atl, ctl, atl_anterior=None):
    """Retorna cards de alerta baseado em escala Intervals.icu"""
    alerts = []
    
    # Escala Intervals.icu:
    # +20 e acima: Adaptando (amarelo)
    # +6 até +20: Descansando (verde claro)
    # -10 até +5: Mantendo (verde)
    # -30 até -11: Evoluindo (azul)
    # -31 e abaixo: Alto Risco (vermelho)
    
    if tsb <= -31:
        alerts.append(('🚨 ALTO RISCO', 'TSB muito baixo. Recuperação urgente.', '#f87171'))
    elif -30 <= tsb <= -11:
        # Zona de evolução - informativo apenas
        pass
    elif -10 <= tsb <= 5:
        # Zona de manutenção - normal
        pass
    elif 6 <= tsb <= 20:
        # Zona de descanso - informativo
        pass
    elif tsb >= 21:
        alerts.append(('⚡ ADAPTANDO', 'TSB elevado. Corpo se adaptando à carga.', '#fbbf24'))
    
    if atl_anterior and atl > atl_anterior * 1.15:
        alerts.append(('📈 ATL CRESCENDO', 'Fadiga acumulada aumentando. Monitore.', '#fb923c'))
    
    if not alerts:
        return ''
    
    h = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin-bottom:14px;">'
    
    for icon_status, msg, cor in alerts:
        h += f'<div style="background:{cor}22;padding:12px;border-radius:8px;border-left:3px solid {cor};">'
        h += f'<div style="color:{cor};font-weight:700;font-size:12px;margin-bottom:4px;">{icon_status}</div>'
        h += f'<div style="color:#ddd;font-size:11px;">{msg}</div>'
        h += f'</div>'
    
    h += '</div>'
    return h

# ─── Build Gráficos ────────────────────────────────────────────────────────────

def build_grafico_ctl_atl_tsb(historico):
    """Gera chart.js para CTL/ATL/TSB últimos 30 dias"""
    if not historico or len(historico) < 7:
        return ''
    
    # Pegar últimos 30 dias (ou menos se não tiver)
    dados = historico[-30:]
    
    labels = [f"D{i}" for i in range(len(dados))]
    ctl_vals = [d.get('ctl', 0) for d in dados]
    atl_vals = [d.get('atl', 0) for d in dados]
    tsb_vals = [d.get('tsb', 0) for d in dados]
    
    js = f'''
    <div style="background:#0a0a0a;padding:12px;border-radius:8px;margin-bottom:12px;">
    <canvas id="chart_ctl_atl" height="80"></canvas>
    <script>
    new Chart(document.getElementById('chart_ctl_atl'), {{
        type: 'line',
        data: {{
            labels: {labels},
            datasets: [
                {{label: 'CTL', data: {ctl_vals}, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', tension: 0.3}},
                {{label: 'ATL', data: {atl_vals}, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', tension: 0.3}},
                {{label: 'TSB', data: {tsb_vals}, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3}}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{legend: {{display: true, position: 'top'}}}},
            scales: {{y: {{beginAtZero: false, grid: {{color: '#333'}}}}, x: {{grid: {{color: '#333'}}}}}}
        }}
    }});
    </script>
    </div>
    '''
    return js

def build_grafico_power_curve(analytics_data):
    """Gera chart.js para Power Curve"""
    if 'power_curve' not in analytics_data:
        return ''
    
    pc = analytics_data['power_curve']
    labels = ['5s', '1min', '5min', '20min', '60min']
    valores = [
        pc.get('pico_5s', 0),
        pc.get('pico_1min', 0),
        pc.get('pico_5min', 0),
        pc.get('pico_20min', 0),
        pc.get('pico_60min', 0)
    ]
    
    js = f'''
    <div style="background:#0a0a0a;padding:12px;border-radius:8px;margin-bottom:12px;">
    <canvas id="chart_power_curve" height="60"></canvas>
    <script>
    new Chart(document.getElementById('chart_power_curve'), {{
        type: 'bar',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Watts',
                data: {valores},
                backgroundColor: ['#fbbf24', '#f97316', '#ef4444', '#ec4899', '#a855f7'],
                borderRadius: 6
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'x',
            plugins: {{legend: {{display: false}}}},
            scales: {{y: {{beginAtZero: true, grid: {{color: '#333'}}}}, x: {{grid: {{color: '#333'}}}}}}
        }}
    }});
    </script>
    </div>
    '''
    return js

def build_grafico_distribuicao_zonas(distrib):
    """Gera chart.js pie para distribuição de zonas"""
    if not distrib:
        return ''
    
    labels = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
    valores = [
        distrib.get('z1_pct', 0),
        distrib.get('z2_pct', 0),
        distrib.get('z3_pct', 0),
        distrib.get('z4_pct', 0),
        distrib.get('z5_pct', 0)
    ]
    
    js = f'''
    <div style="background:#0a0a0a;padding:12px;border-radius:8px;margin-bottom:12px;max-width:300px;">
    <canvas id="chart_zonas" height="80"></canvas>
    <script>
    new Chart(document.getElementById('chart_zonas'), {{
        type: 'doughnut',
        data: {{
            labels: {labels},
            datasets: [{{
                data: {valores},
                backgroundColor: ['#6b7280', '#10b981', '#f59e0b', '#ef4444', '#a21caf']
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{legend: {{position: 'right'}}}}
        }}
    }});
    </script>
    </div>
    '''
    return js

def build_dashboard(treinos, wellness, fitness, estado, analytics_data={}):
    treinos_list = sorted(treinos.values(), key=lambda x: x.get('data', ''), reverse=True)
    ftp_gap, sem_220, ganho_ftp = prever_ftp(treinos)
    wkg = round(FTP / PESO, 2)
    historico = calcular_wellness_historico(treinos)
    distrib = calcular_distribuicao(treinos)
    vo2_fc = vo2max_fc()
    vo2_pot, melhor_5min = vo2max_potencia(treinos)
    label_fc, cor_fc = classificar_vo2(vo2_fc)
    label_pot, cor_pot = classificar_vo2(vo2_pot)

    # Bloco atual + semana
    bloco_atual = estado.get('bloco_atual', 'base')
    semana_no_bloco = estado.get('semana_no_bloco', 1)
    bloco_info = BLOCOS[bloco_atual]

    plano_atual = gerar_plano_semana_bloco(bloco_atual, semana_no_bloco)
    analise = analisar_semana_atual(treinos, plano_atual)

    ultimos_reais = [h for h in historico if not h.get('forecast')]
    ultimo = ultimos_reais[-1] if ultimos_reais else {'ctl': 36, 'atl': 54, 'tsb': -18, 'tss': 0}
    ctl, atl, tsb = ultimo['ctl'], ultimo['atl'], ultimo['tsb']

    # Escala TSB Intervals.icu
    if tsb <= -31:
        cor_tsb = '#f87171'  # Alto Risco (vermelho)
    elif -30 <= tsb <= -11:
        cor_tsb = '#3b82f6'  # Evoluindo (azul)
    elif -10 <= tsb <= 5:
        cor_tsb = '#4ade80'  # Mantendo (verde)
    elif 6 <= tsb <= 20:
        cor_tsb = '#86efac'  # Descansando (verde claro)
    else:  # tsb >= 21
        cor_tsb = '#fbbf24'  # Adaptando (amarelo)

    # Próxima semana (com periodização)
    prox_bloco, prox_semana, razoes_prox, forcou_rec = proxima_semana_periodizacao(
        estado, tsb, analise['aderencia_pct'], analise['treinos_perdidos']
    )
    plano_proxima = gerar_plano_semana_bloco(prox_bloco, prox_semana, tsb)
    bloco_prox_info = BLOCOS[prox_bloco]

    # ─── Cards superiores ──────────────────────────────────────────────────
    cards_analise = f'<div style="display:grid;grid-template-columns:{"1fr 1fr 1fr" if ftp_gap and sem_220 else "1fr 1fr"};gap:12px;margin-bottom:14px;">'
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

    # ─── Header de periodização ───────────────────────────────────────────
    fase_label = 'BUILD' if semana_no_bloco < 4 else 'RECOVERY'
    fase_cor = '#fbbf24' if fase_label == 'BUILD' else '#10b981'

    header_period = f'<div style="background:linear-gradient(135deg, {bloco_info["cor"]}22, transparent);padding:16px;border-radius:10px;margin-bottom:14px;border:1px solid {bloco_info["cor"]}44;">'
    header_period += f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">'
    header_period += f'<div>'
    header_period += f'<div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:2px;font-weight:600;margin-bottom:4px;">📚 Bloco atual de treinamento</div>'
    header_period += f'<div style="font-size:22px;font-weight:700;color:{bloco_info["cor"]};">{bloco_info["icone"]} {bloco_info["nome"]}</div>'
    header_period += f'<div style="font-size:12px;color:#aaa;margin-top:4px;">{bloco_info["descricao"]}</div>'
    header_period += f'</div>'
    header_period += f'<div style="text-align:right;">'
    header_period += f'<div style="font-size:10px;color:#666;text-transform:uppercase;">Semana</div>'
    header_period += f'<div style="font-size:28px;font-weight:700;color:{fase_cor};">{semana_no_bloco}<span style="font-size:14px;color:#666;">/4</span></div>'
    header_period += f'<div style="font-size:10px;color:{fase_cor};font-weight:600;">{fase_label}</div>'
    header_period += f'</div>'
    header_period += f'</div>'
    header_period += f'<div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:11px;">'
    header_period += f'<div><span style="color:#666;">Foco:</span> <span style="color:#ddd;">{bloco_info["foco"]}</span></div>'
    header_period += f'<div><span style="color:#666;">Distribuição alvo:</span> <span style="color:#ddd;">{bloco_info["distribuicao"]}</span></div>'
    header_period += f'</div>'
    header_period += f'</div>'

    # ─── Aba 1: Semana Atual ──────────────────────────────────────────────
    seg_dt = datetime.strptime(analise['seg_atual'], '%Y-%m-%d')
    dom_dt = seg_dt + timedelta(days=6)
    cor_ader = '#4ade80' if analise['aderencia_pct'] >= 80 else ('#facc15' if analise['aderencia_pct'] >= 60 else '#f87171')
    cor_tss_sem = '#4ade80' if 80 <= analise['tss_pct'] <= 120 else ('#facc15' if 60 <= analise['tss_pct'] <= 140 else ('#f87171' if analise['tss_pct'] > 0 else '#6b7280'))
    pct_bar_tss = min(analise['tss_pct'], 150)

    aba_atual = f'<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aba_atual += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">'
    aba_atual += f'<div>'
    aba_atual += f'<h3 style="font-size:15px;color:#fff;margin-bottom:2px;">📅 Semana Atual</h3>'
    aba_atual += f'<div style="font-size:11px;color:#666;">{seg_dt.strftime("%d/%m")} — {dom_dt.strftime("%d/%m")}</div>'
    aba_atual += f'</div>'
    aba_atual += f'<div style="display:flex;gap:14px;align-items:center;">'
    aba_atual += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Aderência</div><div style="font-size:22px;font-weight:700;color:{cor_ader};">{analise["aderencia_pct"]}%</div></div>'
    aba_atual += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Treinos</div><div style="font-size:22px;font-weight:700;color:#3b82f6;">{analise["treinos_feitos"]}/{analise["treinos_planejados_cic"]}</div></div>'
    aba_atual += f'</div></div>'
    aba_atual += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;margin-bottom:14px;">'
    aba_atual += f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:11px;">'
    aba_atual += f'<div style="color:#666;text-transform:uppercase;letter-spacing:1px;font-weight:600;">📊 TSS Semana</div>'
    aba_atual += f'<div><span style="color:{cor_tss_sem};font-weight:700;">{int(analise["tss_realizado"])}</span><span style="color:#666;"> / {analise["tss_alvo"]} ({analise["tss_pct"]}%)</span></div>'
    aba_atual += f'</div>'
    aba_atual += f'<div style="background:#1a1a1a;height:10px;border-radius:5px;overflow:hidden;"><div style="background:{cor_tss_sem};height:100%;width:{pct_bar_tss}%;"></div></div>'
    aba_atual += f'</div>'
    for idx, dia in enumerate(analise['dias']):
        aba_atual += build_dia_semana_atual(dia, idx)
    aba_atual += '</div>'

    # ─── Aba 2: Próxima Semana ────────────────────────────────────────────
    prox_seg_dt = seg_dt + timedelta(days=7)
    prox_dom_dt = prox_seg_dt + timedelta(days=6)
    tss_total_prox = sum(p.get('tss_alvo', 0) for p in plano_proxima.values())
    fase_prox = 'BUILD' if prox_semana < 4 else 'RECOVERY'
    fase_prox_cor = '#fbbf24' if fase_prox == 'BUILD' else '#10b981'

    aba_prox = f'<div style="background:#111;border-radius:10px;padding:16px;margin-bottom:14px;">'
    aba_prox += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">'
    aba_prox += f'<div>'
    aba_prox += f'<h3 style="font-size:15px;color:#fff;margin-bottom:2px;">🎯 Próxima Semana</h3>'
    aba_prox += f'<div style="font-size:11px;color:#666;">{prox_seg_dt.strftime("%d/%m")} — {prox_dom_dt.strftime("%d/%m")}</div>'
    aba_prox += f'</div>'
    aba_prox += f'<div style="display:flex;gap:12px;align-items:center;">'
    aba_prox += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">TSS</div><div style="font-size:20px;font-weight:700;color:#3b82f6;">{tss_total_prox}</div></div>'
    aba_prox += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Bloco</div><div style="font-size:14px;font-weight:700;color:{bloco_prox_info["cor"]};padding:4px 10px;background:{bloco_prox_info["cor"]}22;border-radius:6px;">{bloco_prox_info["icone"]} {bloco_prox_info["nome"]}</div></div>'
    aba_prox += f'<div style="text-align:center;"><div style="font-size:9px;color:#666;text-transform:uppercase;">Semana</div><div style="font-size:14px;font-weight:700;color:{fase_prox_cor};">{prox_semana}/4 ({fase_prox})</div></div>'
    aba_prox += f'</div></div>'

    # Razões da decisão
    aba_prox += f'<div style="background:#0a0a0a;padding:12px;border-radius:6px;margin-bottom:14px;border-left:3px solid {bloco_prox_info["cor"]};">'
    aba_prox += f'<div style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600;">🤖 Lógica de Periodização</div>'
    for r in razoes_prox:
        aba_prox += f'<div style="font-size:12px;color:#ddd;line-height:1.5;margin-bottom:4px;">{r}</div>'
    aba_prox += f'<div style="font-size:10px;color:#666;margin-top:8px;border-top:1px solid #1a1a1a;padding-top:8px;">Estado: TSB {tsb:+.1f} · Aderência {analise["aderencia_pct"]}% · Perdidos {analise["treinos_perdidos"]} · Objetivo: {bloco_prox_info["objetivo"]}</div>'
    aba_prox += f'</div>'

    for wd in range(7):
        aba_prox += build_dia_proxima(wd, plano_proxima[wd])
    aba_prox += '</div>'

    # ─── Aba 3: Histórico (INCLUI semana atual) ───────────────────────────
    por_semana_hist = defaultdict(list)
    for t in treinos_list:
        data = t.get('data', '')
        if not data: continue
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            week = (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
            por_semana_hist[week].append(t)
        except: pass
    sem_ord = sorted(por_semana_hist.keys(), reverse=True)

    aba_hist = ''
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
        aba_hist += '</div></div>'

    aba_hist += '<div class="filtros">'
    aba_hist += '<span class="label-title">Filtrar:</span>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="ciclismo" checked> 🚴 Ciclismo</label>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="academia" checked> 🏋️ Academia</label>'
    aba_hist += '<label><input type="checkbox" class="filter-cat" data-cat="outros" checked> 🏃 Outros</label>'
    aba_hist += '</div>'

    for week in sem_ord[:10]:
        t_sem = por_semana_hist[week]
        dt_seg = datetime.strptime(week, '%Y-%m-%d')
        dt_dom = dt_seg + timedelta(days=6)
        label = f"{dt_seg.strftime('%d/%m')} — {dt_dom.strftime('%d/%m')}"
        is_atual = week == analise['seg_atual']
        atual_b = ' <span style="color:#facc15;font-weight:600;font-size:10px;margin-left:8px;">▶ ATUAL</span>' if is_atual else ''
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

        border = 'border:1px solid #facc15;' if is_atual else 'border:1px solid #222;'
        aba_hist += f'<div style="background:#111;border-radius:10px;padding:14px;margin-bottom:10px;{border}">'
        aba_hist += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">'
        aba_hist += f'<div style="font-size:13px;font-weight:600;color:#ddd;">{label}<span style="color:#666;font-weight:400;margin-left:10px;">{len(t_sem)} treinos</span>{atual_b}</div>'
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

    # ─── Aba 4: Condicionamento ───────────────────────────────────────────
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

    # v11.7: Aba Analytics
    aba_analytics = build_aba_analytics(analytics_data)
    
    # v11.7: Gráficos e comparação
    card_comparacao = build_card_comparacao(analise, historico, treinos)
    grafico_ctl_atl = build_grafico_ctl_atl_tsb(historico)
    grafico_power = build_grafico_power_curve(analytics_data)
    grafico_zonas = build_grafico_distribuicao_zonas(distrib)

    # v11.7: Cards hoje + alerts
    hoje_sups = calcular_suplementacao(analise['dias'][-1]['plano']['dur_total'] if analise['dias'] else 0)
    card_hoje = build_card_hoje(analise, hoje_sups, plano_proxima)
    
    atl_anterior = historico[-8]['atl'] if len(historico) > 7 else atl
    alerts_html = build_alerts(tsb, atl, ctl, atl_anterior)

    # ─── HTML completo ─────────────────────────────────────────────────────
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🚴 Strava Coach v11.7</title>
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
<h1>🚴 Strava Coach v11.7</h1>
<p>Atualizado em {agora().strftime('%d/%m/%Y %H:%M')} (BRT)</p>
</div>

<div class="fitness-bar">
<div class="fc-card"><div class="label">CTL</div><div class="value" style="color:#3b82f6;">{ctl}</div></div>
<div class="fc-card"><div class="label">ATL</div><div class="value" style="color:#fb923c;">{atl}</div></div>
<div class="fc-card"><div class="label">TSB</div><div class="value" style="color:{cor_tsb};">{tsb}</div></div>
<div class="fc-card"><div class="label">FTP</div><div class="value">{FTP}W</div><div class="sub">{wkg} W/kg</div></div>
<div class="fc-card"><div class="label">Peso</div><div class="value">{PESO}</div><div class="sub">kg</div></div>
</div>

{cards_analise}
{alerts_html}
{card_hoje}
{card_comparacao}
{cards_vo2}
{header_period}

<div class="tabs">
<button class="tab active" data-tab="atual">📅 Semana Atual</button>
<button class="tab" data-tab="proxima">🎯 Próxima Semana</button>
<button class="tab" data-tab="historico">📊 Histórico</button>
<button class="tab" data-tab="condicionamento">📈 Condicionamento</button>
<button class="tab" data-tab="analytics">📊 Analytics</button>
</div>

<div id="atual" class="tab-content active">{aba_atual}</div>
<div id="proxima" class="tab-content">{aba_prox}</div>
<div id="historico" class="tab-content">{aba_hist}</div>
<div id="condicionamento" class="tab-content">{grafico_ctl_atl}{aba_cond}</div>
<div id="analytics" class="tab-content">{aba_analytics}</div>

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
            datasets.push({{ label: label, data: dataReal, borderColor: color, backgroundColor: color + '20',
                borderWidth: 2, tension: 0.3, pointRadius: 0 }});
            if (forecastStart !== -1) {{
                datasets.push({{ label: label + ' (FC)', data: dataForecast, borderColor: color, backgroundColor: color + '10',
                    borderWidth: 2, borderDash: [5, 5], tension: 0.3, pointRadius: 3, pointStyle: 'rectRot' }});
            }}
        }}
    }});
    chartInstance = new Chart(ctx, {{
        type: 'line', data: {{ labels: labels, datasets: datasets }},
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
    print("🎨 Dashboard Generator v11.7 (Periodização + Analytics)\n")
    treinos, wellness, fitness, estado, analytics_data = load_data()
    print(f"✅ {len(treinos)} treinos carregados")

    hoje = agora()
    seg_atual_str = (hoje - timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')

    # Estado inicial se vazio
    if not estado or 'bloco_atual' not in estado:
        estado = {
            'semana_referencia': seg_atual_str,
            'bloco_atual': 'base',
            'semana_no_bloco': 1,
            'ultima_atualizacao': hoje.strftime('%Y-%m-%d %H:%M BRT')
        }
        print(f"📚 Iniciando: Bloco BASE, semana 1/4")
        save_estado(estado)
    elif estado.get('semana_referencia') != seg_atual_str:
        # Nova semana — avança periodização com base na semana que TERMINOU
        print(f"📅 Nova semana detectada ({seg_atual_str})")
        historico = calcular_wellness_historico(treinos)
        ultimo = [h for h in historico if not h.get('forecast')][-1]
        tsb_atual = ultimo['tsb']
        plano_anterior = gerar_plano_semana_bloco(estado['bloco_atual'], estado['semana_no_bloco'])
        # CORREÇÃO: analisar semana passada (não a atual que está começando)
        analise_anterior = analisar_semana_passada(treinos, plano_anterior)
        novo_bloco, nova_semana, _, _ = proxima_semana_periodizacao(
            estado, tsb_atual, analise_anterior['aderencia_pct'], analise_anterior['treinos_perdidos']
        )
        estado = {
            'semana_referencia': seg_atual_str,
            'bloco_atual': novo_bloco,
            'semana_no_bloco': nova_semana,
            'ultima_atualizacao': hoje.strftime('%Y-%m-%d %H:%M BRT')
        }
        save_estado(estado)
        print(f"📚 Bloco: {novo_bloco} | Semana: {nova_semana}/4")
    else:
        estado['ultima_atualizacao'] = hoje.strftime('%Y-%m-%d %H:%M BRT')
        save_estado(estado)

    print(f"📚 Bloco atual: {BLOCOS[estado['bloco_atual']]['nome']} ({estado['semana_no_bloco']}/4)")

    html = build_dashboard(treinos, wellness, fitness, estado, analytics_data)
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ dashboard.html gerado ({len(html):,} bytes)")

if __name__ == '__main__':
    main()
