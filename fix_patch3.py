"""
fix_patch3.py — corrige o Patch 3 que falhou no patch_v11_8.py
Execute: python fix_patch3.py
"""
import re

TARGET = 'dashboard_generator.py'

with open(TARGET, 'r', encoding='utf-8') as f:
    src = f.read()

if 'card_tss_bloco = build_card_tss_bloco' in src:
    print("✅ Patch 3 já está aplicado, nada a fazer.")
    exit(0)

# Procura a linha dos alerts_html que sempre existe antes do HTML
OLD = "    alerts_html = build_alerts(tsb, atl, ctl, atl_anterior)"
NEW = """    alerts_html = build_alerts(tsb, atl, ctl, atl_anterior)
    card_tss_bloco = build_card_tss_bloco(analise['tss_realizado'], TSS_META_SEMANA)"""

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(src)
    print("✅ Patch 3 aplicado com sucesso.")
else:
    # Fallback: procura a linha do card_hoje
    OLD2 = "    hoje_sups = calcular_suplementacao("
    NEW2 = """    card_tss_bloco = build_card_tss_bloco(analise['tss_realizado'], TSS_META_SEMANA)
    hoje_sups = calcular_suplementacao("""
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        with open(TARGET, 'w', encoding='utf-8') as f:
            f.write(src)
        print("✅ Patch 3 aplicado (fallback).")
    else:
        print("❌ Não encontrou ponto de inserção. Cole manualmente antes do bloco HTML:")
        print("    card_tss_bloco = build_card_tss_bloco(analise['tss_realizado'], TSS_META_SEMANA)")
