"""
patch_config.py — v11.8.1
Aplica suporte a config.json no dashboard_generator.py:
  - TSS_META_SEMANA dinâmico (vem do config)
  - dias_off_planejados: aparecem como 🗓️ OFF em vez de ❌ Perdido
  - Academia no lugar de ciclismo → status 'parcial' (amarelo)

Execute: python patch_config.py
"""

import shutil
import os

TARGET = 'dashboard_generator.py'

if not os.path.exists(TARGET):
    print(f"❌ '{TARGET}' não encontrado.")
    exit(1)

if not os.path.exists('config.json'):
    print("❌ 'config.json' não encontrado. Copie o arquivo junto com este script.")
    exit(1)

shutil.copy(TARGET, TARGET + '.bak_v11_8')
print(f"✅ Backup: {TARGET}.bak_v11_8")

with open(TARGET, 'r', encoding='utf-8') as f:
    src = f.read()

patches_ok = 0

# ── PATCH 1: carregar config.json logo após os imports ───────────────────────
OLD1 = "# v11.7: Analytics\nfrom analytics import gerar_analytics_completo\nfrom dashboard_cards_lite import build_aba_analytics, build_card_tss_bloco"
NEW1 = """# v11.7: Analytics
from analytics import gerar_analytics_completo
from dashboard_cards_lite import build_aba_analytics, build_card_tss_bloco

# v11.8.1: Config dinâmico
def carregar_config():
    import json
    path = 'config.json'
    defaults = {'tss_meta_semana': 350, 'dias_off_planejados': []}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        defaults.update({k: v for k, v in cfg.items() if not k.startswith('_')})
    return defaults

CONFIG = carregar_config()"""

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    patches_ok += 1
    print("✅ Patch 1: carregar_config()")
else:
    print("⚠️  Patch 1 não aplicado — import line não encontrada")

# ── PATCH 2: TSS_META_SEMANA dinâmico ────────────────────────────────────────
OLD2 = "TSS_META_SEMANA = 420"
NEW2 = "TSS_META_SEMANA = CONFIG.get('tss_meta_semana', 350)"
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    patches_ok += 1
    print("✅ Patch 2: TSS_META_SEMANA dinâmico")
else:
    # Já pode ter sido alterado para 350 manualmente
    OLD2B = "TSS_META_SEMANA = 350"
    if OLD2B in src:
        src = src.replace(OLD2B, NEW2, 1)
        patches_ok += 1
        print("✅ Patch 2 (alt): TSS_META_SEMANA dinâmico")
    else:
        print("⚠️  Patch 2 não aplicado")

# ── PATCH 3: dias_off_planejados em analisar_semana_atual ────────────────────
# Substitui o bloco que determina status/icone/cor por dia
OLD3 = """        if is_futuro:
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
            if plan['tipo'] == 'ciclismo': treinos_perdidos += 1"""

NEW3 = """        dias_off = CONFIG.get('dias_off_planejados', [])
        is_off = dia_dt.strftime('%Y-%m-%d') in dias_off

        if is_futuro:
            if is_off:
                status, icone, cor = 'off', '🗓️', '#6b7280'
            else:
                status, icone, cor = 'futuro', '⏳', '#6b7280'
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
            if plan['tipo'] == 'ciclismo': treinos_perdidos += 1"""

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    patches_ok += 1
    print("✅ Patch 3: dias_off_planejados + academia=parcial")
else:
    print("⚠️  Patch 3 não aplicado — bloco de status não encontrado (verifique indentação)")

# ── PATCH 4: label 'off' no build_dia_semana_atual ───────────────────────────
# Garante que status 'off' mostre o plano (não trata como perdido)
OLD4 = "    mostrar_plano = (status in ['futuro', 'hoje', 'perdido', 'parcial']) and cat == 'ciclismo'"
NEW4 = "    mostrar_plano = (status in ['futuro', 'hoje', 'perdido', 'parcial', 'off']) and cat == 'ciclismo'"
if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    patches_ok += 1
    print("✅ Patch 4: status 'off' mostra plano no card")
else:
    print("⚠️  Patch 4 não aplicado")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n{'✅ Todos os patches aplicados!' if patches_ok == 4 else f'⚠️  {patches_ok}/4 aplicados'}")
print("\nPróximos passos:")
print("  1. Edite config.json para ajustar datas e TSS")
print("  2. python dashboard_generator.py")
print("  3. git add -A && git commit -m 'v11.8.1: config.json + dias_off' && git push")
