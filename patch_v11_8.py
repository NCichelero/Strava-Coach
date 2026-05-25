"""
patch_v11_8.py
Aplica as mudanças do v11.8 no dashboard_generator.py existente.
Execute UMA vez: python patch_v11_8.py
"""

import os
import shutil

TARGET = 'dashboard_generator.py'

if not os.path.exists(TARGET):
    print(f"❌ Arquivo '{TARGET}' não encontrado. Execute na pasta do projeto.")
    exit(1)

# Backup
shutil.copy(TARGET, TARGET + '.bak_v11_7')
print(f"✅ Backup criado: {TARGET}.bak_v11_7")

with open(TARGET, 'r', encoding='utf-8') as f:
    src = f.read()

changes = 0

# ── PATCH 1: import build_card_tss_bloco ─────────────────────────────────────
OLD1 = "from dashboard_cards_lite import build_aba_analytics"
NEW1 = "from dashboard_cards_lite import build_aba_analytics, build_card_tss_bloco"
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    changes += 1
    print("✅ Patch 1: import build_card_tss_bloco")
else:
    print("⚠️  Patch 1 não aplicado (já existe ou import diferente)")

# ── PATCH 2: build_aba_analytics com novos parâmetros ────────────────────────
OLD2 = "    aba_analytics = build_aba_analytics(analytics_data)"
NEW2 = """    aba_analytics = build_aba_analytics(
        analytics_data,
        distrib=distrib,
        ctl=ctl,
        atl=atl,
        tss_meta_bloco=TSS_META_SEMANA,
        alvo_str=bloco_info['distribuicao']
    )"""
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    changes += 1
    print("✅ Patch 2: build_aba_analytics com parâmetros v11.8")
else:
    print("⚠️  Patch 2 não aplicado (linha não encontrada)")

# ── PATCH 3: gerar card_tss_bloco antes do HTML ───────────────────────────────
OLD3 = "    atl_anterior = historico[-8]['atl'] if len(historico) > 7 else atl"
NEW3 = """    atl_anterior = historico[-8]['atl'] if len(historico) > 7 else atl
    card_tss_bloco = build_card_tss_bloco(analise['tss_realizado'], TSS_META_SEMANA)"""
if OLD3 in src and 'card_tss_bloco' not in src:
    src = src.replace(OLD3, NEW3, 1)
    changes += 1
    print("✅ Patch 3: variável card_tss_bloco gerada")
else:
    print("⚠️  Patch 3 não aplicado (já existe ou linha não encontrada)")

# ── PATCH 4: inserir card_tss_bloco no HTML entre card_hoje e card_readiness ──
OLD4 = "{card_hoje}\n{card_readiness}"
NEW4 = "{card_hoje}\n{card_tss_bloco}\n{card_readiness}"
if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    changes += 1
    print("✅ Patch 4: card_tss_bloco inserido no HTML")
else:
    # Tenta variante com espaços/tabs diferentes
    OLD4B = "{card_hoje}\n{card_readiness}"
    if OLD4B in src and '{card_tss_bloco}' not in src:
        src = src.replace(OLD4B, '{card_hoje}\n{card_tss_bloco}\n{card_readiness}', 1)
        changes += 1
        print("✅ Patch 4 (alt): card_tss_bloco inserido no HTML")
    else:
        print("⚠️  Patch 4 não aplicado (bloco HTML não encontrado ou já existe)")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n{'✅ Patch completo' if changes == 4 else f'⚠️  {changes}/4 patches aplicados'} em '{TARGET}'")
if changes < 4:
    print("   Se algum patch falhou, verifique manualmente as linhas acima.")
    print("   Restaure com: copy dashboard_generator.py.bak_v11_7 dashboard_generator.py")
