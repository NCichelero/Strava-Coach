"""
intervals_sync.py — Sincroniza dados do Intervals.icu antes de gerar o dashboard
Execute: python intervals_sync.py
"""

import json
import os
import sys
from datetime import datetime

# Garante que o diretório data/ existe
os.makedirs("data", exist_ok=True)

try:
    from intervals_api import buscar_tudo, wellness_hoje, calcular_readiness_real, resumo_rpe_recente
except ImportError:
    print("❌ intervals_api.py não encontrado na pasta atual")
    sys.exit(1)

def sincronizar():
    print("🔄 Sincronizando Intervals.icu...")
    dados = buscar_tudo()

    wellness = dados.get("wellness", [])
    atividades = dados.get("atividades", [])
    fitness = dados.get("fitness")

    print(f"  ✅ Wellness: {len(wellness)} dias")
    print(f"  ✅ Atividades: {len(atividades)}")
    if fitness:
        print(f"  ✅ Fitness: CTL {fitness['ctl']} | ATL {fitness['atl']} | TSB {fitness['tsb']:+.1f}")

    # Salva wellness separado para o dashboard usar
    with open("data/wellness.json", "w", encoding="utf-8") as f:
        json.dump(wellness, f, ensure_ascii=False, indent=2)

    # Salva fitness do Intervals (sobrescreve cálculo local)
    if fitness:
        with open("data/fitness_intervals.json", "w", encoding="utf-8") as f:
            json.dump(fitness, f, ensure_ascii=False, indent=2)

    # Resumo RPE
    rpe = resumo_rpe_recente(atividades)
    if rpe:
        print(f"  ✅ RPE médio (14d): {rpe['rpe_medio']} — {rpe['interpretacao']}")

    # Wellness hoje
    w = wellness_hoje(dados)
    if w:
        hrv = w.get("hrv") or w.get("hrv_score")
        sono = w.get("sono_horas")
        fc = w.get("fc_repouso")
        print(f"\n📊 Wellness hoje ({w['data']}):")
        if hrv:   print(f"  HRV: {hrv:.0f}")
        if sono:  print(f"  Sono: {sono:.1f}h")
        if fc:    print(f"  FC repouso: {fc}bpm")

    print("\n✅ Sincronização concluída")
    return dados


if __name__ == "__main__":
    sincronizar()
