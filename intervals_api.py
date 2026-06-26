"""
intervals_api.py — Integração com Intervals.icu
Busca: wellness (HRV, sono, FC repouso), CTL/ATL/TSB, atividades, perceived exertion
"""

import requests
import json
import os
from datetime import datetime, timedelta

ATHLETE_ID = "i571333"
API_KEY = "6ysaprmt15s19ibgbfabo2stw"
BASE_URL = "https://intervals.icu/api/v1/athlete"
AUTH = ("API_KEY", API_KEY)
CACHE_FILE = "data/intervals_cache.json"
CACHE_TTL_HOURS = 3


def _get(endpoint, params=None):
    url = f"{BASE_URL}/{ATHLETE_ID}/{endpoint}"
    try:
        r = requests.get(url, auth=AUTH, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Intervals.icu API erro ({endpoint}): {e}")
        return None


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        ts = cache.get("_timestamp", "")
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600
            if age < CACHE_TTL_HOURS:
                return cache
    return {}


def _save_cache(data):
    os.makedirs("data", exist_ok=True)
    data["_timestamp"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def buscar_wellness(dias=14):
    """Busca dados de wellness dos últimos N dias (HRV, sono, FC repouso, fadiga)."""
    hoje = datetime.now()
    inicio = (hoje - timedelta(days=dias)).strftime("%Y-%m-%d")
    fim = hoje.strftime("%Y-%m-%d")

    data = _get("wellness", params={"oldest": inicio, "newest": fim})
    if not data:
        return []

    wellness = []
    for w in data:
        wellness.append({
            "data": w.get("id", ""),
            "hrv": w.get("hrv"),
            "hrv_score": w.get("hrvScore"),
            "fc_repouso": w.get("restingHR"),
            "sono_horas": round(w.get("sleepSecs", 0) / 3600, 1) if w.get("sleepSecs") else None,
            "sono_score": w.get("sleepScore"),
            "sono_qualidade": w.get("sleepQuality"),
            "fadiga": w.get("fatigue"),       # 1-7 (1=muito baixa, 7=muito alta)
            "forma": w.get("form"),            # 1-7
            "humor": w.get("mood"),
            "motivacao": w.get("motivation"),
            "ctl": w.get("ctl"),
            "atl": w.get("atl"),
            "tsb": w.get("tsb"),
            "comentarios": w.get("comments", ""),
        })

    return sorted(wellness, key=lambda x: x["data"], reverse=True)


def buscar_atividades(dias=60):
    """Busca atividades com perceived_exertion e métricas de carga."""
    hoje = datetime.now()
    inicio = (hoje - timedelta(days=dias)).strftime("%Y-%m-%d")

    data = _get("activities", params={
        "oldest": inicio,
        "fields": "id,name,start_date_local,type,moving_time,distance,icu_training_load,"
                  "icu_ctl_end,icu_atl_end,icu_tsb_end,perceived_exertion,average_heartrate,"
                  "weighted_average_watts,average_watts,max_heartrate,icu_rpe"
    })
    if not data:
        return []

    atividades = []
    for a in data:
        atividades.append({
            "id": a.get("id"),
            "nome": a.get("name", ""),
            "data": a.get("start_date_local", "")[:10],
            "tipo": a.get("type", ""),
            "duracao_min": round(a.get("moving_time", 0) / 60, 1),
            "distancia_km": round(a.get("distance", 0) / 1000, 1),
            "tss": a.get("icu_training_load"),
            "ctl_end": a.get("icu_ctl_end"),
            "atl_end": a.get("icu_atl_end"),
            "tsb_end": a.get("icu_tsb_end"),
            "rpe": a.get("perceived_exertion") or a.get("icu_rpe"),
            "fc_avg": a.get("average_heartrate"),
            "fc_max": a.get("max_heartrate"),
            "potencia_norm": a.get("weighted_average_watts"),
            "potencia_avg": a.get("average_watts"),
        })

    return sorted(atividades, key=lambda x: x["data"], reverse=True)


def buscar_fitness_atual():
    """Busca CTL/ATL/TSB atual direto do Intervals (mais preciso)."""
    data = _get("fitnesses", params={
        "oldest": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "newest": datetime.now().strftime("%Y-%m-%d"),
    })
    if not data:
        return None

    # Pega o mais recente
    for entry in reversed(data):
        ctl = entry.get("ctl") or entry.get("fitness")
        atl = entry.get("atl") or entry.get("fatigue")
        tsb = entry.get("tsb") or entry.get("form")
        if ctl:
            return {
                "ctl": round(ctl, 1),
                "atl": round(atl, 1) if atl else 0,
                "tsb": round(tsb, 1) if tsb else 0,
                "data": entry.get("id", ""),
            }
    return None


def buscar_tudo():
    """Busca todos os dados do Intervals.icu com cache."""
    cache = _load_cache()
    if cache.get("_timestamp"):
        print("  → Usando cache Intervals.icu")
        return cache

    print("  → Buscando dados do Intervals.icu...")
    wellness = buscar_wellness(dias=14)
    atividades = buscar_atividades(dias=60)
    fitness = buscar_fitness_atual()

    resultado = {
        "wellness": wellness,
        "atividades": atividades,
        "fitness": fitness,
    }
    _save_cache(resultado)
    return resultado


# ─── Funções de análise ───────────────────────────────────────────────────

def wellness_hoje(dados):
    """Retorna wellness de hoje ou ontem (o mais recente disponível)."""
    wellness = dados.get("wellness", [])
    if not wellness:
        return None
    hoje = datetime.now().strftime("%Y-%m-%d")
    ontem = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    for w in wellness:
        if w["data"] in (hoje, ontem):
            return w
    return wellness[0] if wellness else None


def calcular_readiness_real(dados, tsb):
    """
    Readiness combinando HRV + TSB + FC repouso + sono.
    Retorna score 0-100, label, cor, detalhes.
    """
    w = wellness_hoje(dados)
    score = 50
    fatores = []

    # TSB (peso 40%)
    if tsb >= 5:
        score += 20; fatores.append(f"TSB {tsb:+.0f} ✅ forma positiva")
    elif -15 <= tsb < 5:
        score += 10; fatores.append(f"TSB {tsb:+.0f} neutro")
    elif -25 <= tsb < -15:
        score -= 5; fatores.append(f"TSB {tsb:+.0f} ⚠️ carga alta")
    else:
        score -= 20; fatores.append(f"TSB {tsb:+.0f} 🔴 carga crítica")

    if w:
        # HRV (peso 30%)
        hrv = w.get("hrv") or w.get("hrv_score")
        if hrv:
            # HRV score do Intervals já é normalizado 0-100
            if hrv >= 70:
                score += 15; fatores.append(f"HRV {hrv:.0f} ✅ ótimo")
            elif hrv >= 50:
                score += 5; fatores.append(f"HRV {hrv:.0f} normal")
            elif hrv >= 30:
                score -= 10; fatores.append(f"HRV {hrv:.0f} ⚠️ baixo")
            else:
                score -= 20; fatores.append(f"HRV {hrv:.0f} 🔴 muito baixo")

        # Sono (peso 20%)
        sono = w.get("sono_score") or w.get("sono_qualidade")
        sono_h = w.get("sono_horas")
        if sono_h:
            if sono_h >= 7.5:
                score += 10; fatores.append(f"Sono {sono_h:.1f}h ✅")
            elif sono_h >= 6:
                score += 3; fatores.append(f"Sono {sono_h:.1f}h ok")
            else:
                score -= 10; fatores.append(f"Sono {sono_h:.1f}h ⚠️ insuficiente")

        # FC repouso (peso 10%)
        fc_rep = w.get("fc_repouso")
        if fc_rep:
            # FC repouso elevada = sinal de fadiga (baseline ~39bpm para Nicollas)
            baseline_fc = 42
            diff = fc_rep - baseline_fc
            if diff <= 2:
                score += 5; fatores.append(f"FC repouso {fc_rep}bpm ✅")
            elif diff <= 5:
                score += 0; fatores.append(f"FC repouso {fc_rep}bpm normal")
            else:
                score -= 8; fatores.append(f"FC repouso {fc_rep}bpm ⚠️ elevada")

    score = max(0, min(100, score))

    if score >= 80:
        label, cor, status = "PRONTO", "#4ade80", "Ótimo para treino intenso"
    elif score >= 65:
        label, cor, status = "BOM", "#86efac", "Bom para treino moderado"
    elif score >= 45:
        label, cor, status = "REGULAR", "#fbbf24", "Prefira treino leve"
    else:
        label, cor, status = "BAIXO", "#f87171", "Recuperação recomendada"

    return {
        "score": score,
        "label": label,
        "cor": cor,
        "status": status,
        "fatores": fatores,
        "wellness": w,
    }


def treino_adaptativo(plano_dia, readiness, tsb):
    """
    Adapta o treino do dia baseado em readiness + TSB.
    Retorna plano original ou versão adaptada + motivo.
    """
    score = readiness["score"]
    adaptado = False
    motivo = ""
    plano = dict(plano_dia)

    # Regra 1: Score < 45 ou TSB < -25 → troca para Z2 recovery
    if score < 45 or tsb < -25:
        tipo = plano.get("tipo", "")
        if tipo == "ciclismo" and plano.get("tss_alvo", 0) > 60:
            plano = {
                "nome": "🔄 Z2 Recovery (adaptado)",
                "tipo": "ciclismo",
                "horario": plano.get("horario", "05:30"),
                "dur_total": 60,
                "tss_alvo": 45,
                "blocos": [
                    {"nome": "Warm-up leve", "dur": 10, "pct_min": 0.40, "pct_max": 0.55, "zona": "Z1"},
                    {"nome": "Z2 Endurance", "dur": 40, "pct_min": 0.60, "pct_max": 0.68, "zona": "Z2"},
                    {"nome": "Cooldown", "dur": 10, "pct_min": 0.35, "pct_max": 0.50, "zona": "Z1"},
                ],
            }
            adaptado = True
            razao = "TSB crítico" if tsb < -25 else "Readiness baixo"
            motivo = f"⚠️ Treino reduzido para Z2 Recovery ({razao}: score {score}/100)"

    # Regra 2: Score 45-65 → reduz intensidade (% mais baixo nos blocos)
    elif score < 65 and not adaptado:
        if plano.get("blocos"):
            blocos_adj = []
            for b in plano["blocos"]:
                b2 = dict(b)
                # Reduz intensidade em 5%
                b2["pct_min"] = round(b["pct_min"] * 0.95, 2)
                b2["pct_max"] = round(b["pct_max"] * 0.95, 2)
                blocos_adj.append(b2)
            plano = dict(plano)
            plano["blocos"] = blocos_adj
            plano["nome"] = plano["nome"] + " (intensidade -5%)"
            adaptado = True
            motivo = f"🟡 Intensidade reduzida 5% (readiness {score}/100)"

    return plano, adaptado, motivo


def progressao_adaptativa(analise_semana, semana_atual, bloco_atual):
    """
    Decide se avança semana ou repete baseado no TSS completado vs planejado.
    Retorna próxima semana recomendada + motivo.
    """
    tss_real = analise_semana.get("tss_realizado", 0)
    tss_alvo = analise_semana.get("tss_alvo", 1)
    aderencia = analise_semana.get("aderencia_pct", 100)
    treinos_perdidos = analise_semana.get("treinos_perdidos", 0)

    pct_tss = round((tss_real / tss_alvo * 100) if tss_alvo > 0 else 100)

    # Completo 90%+: avança
    if pct_tss >= 90 and aderencia >= 80 and treinos_perdidos <= 1:
        if semana_atual < 4:
            return semana_atual + 1, bloco_atual, f"✅ Progredindo: {pct_tss}% do TSS completado"
        else:
            return 1, _proximo_bloco(bloco_atual), f"✅ Bloco completo! Iniciando próximo ciclo"

    # 70-89%: repete a semana
    elif pct_tss >= 70:
        return semana_atual, bloco_atual, f"🔄 Repetindo semana {semana_atual} ({pct_tss}% TSS — abaixo de 90%)"

    # < 70%: volta uma semana se possível
    else:
        sem_anterior = max(1, semana_atual - 1)
        return sem_anterior, bloco_atual, f"⚠️ Recuando para semana {sem_anterior} ({pct_tss}% TSS — carga insuficiente)"


def _proximo_bloco(bloco_atual):
    ordem = ["base", "threshold", "vo2max", "integracao"]
    idx = ordem.index(bloco_atual) if bloco_atual in ordem else 0
    return ordem[(idx + 1) % len(ordem)]


def previsao_forma(historico, data_alvo_str, tss_planejado_semana=350):
    """
    Projeta CTL/ATL/TSB até data alvo.
    Retorna projeção diária + sugestão de taper.
    """
    if not historico:
        return None

    try:
        data_alvo = datetime.strptime(data_alvo_str, "%Y-%m-%d")
    except Exception:
        return None

    hoje = datetime.now()
    dias_faltam = (data_alvo - hoje).days
    if dias_faltam <= 0 or dias_faltam > 120:
        return None

    # Estado atual
    reais = [h for h in historico if not h.get("forecast")]
    if not reais:
        return None
    ultimo = reais[-1]
    ctl = ultimo["ctl"]
    atl = ultimo["atl"]

    # TSS diário médio planejado por dia da semana
    tss_por_dia = {0: 70, 1: 0, 2: 100, 3: 0, 4: 95, 5: 180, 6: 60}

    projecao = []
    ctl_proj, atl_proj = ctl, atl

    for i in range(1, dias_faltam + 1):
        dia = hoje + timedelta(days=i)
        wd = dia.weekday()

        # Taper: últimos 7 dias reduz TSS em 50%
        if i > dias_faltam - 7:
            tss_dia = tss_por_dia.get(wd, 0) * 0.3
        elif i > dias_faltam - 14:
            tss_dia = tss_por_dia.get(wd, 0) * 0.6
        else:
            tss_dia = tss_por_dia.get(wd, 0)

        ctl_proj = ctl_proj + (tss_dia - ctl_proj) / 42
        atl_proj = atl_proj + (tss_dia - atl_proj) / 7
        tsb_proj = ctl_proj - atl_proj

        projecao.append({
            "data": dia.strftime("%Y-%m-%d"),
            "ctl": round(ctl_proj, 1),
            "atl": round(atl_proj, 1),
            "tsb": round(tsb_proj, 1),
            "dias_faltam": dias_faltam - i,
        })

    # Estado no dia alvo
    estado_alvo = projecao[-1] if projecao else None

    # Melhor dia para iniciar taper (TSB entre +5 e +20 no dia alvo)
    tsb_alvo = estado_alvo["tsb"] if estado_alvo else 0
    if 5 <= tsb_alvo <= 20:
        sugestao = f"✅ TSB previsto: {tsb_alvo:+.0f} — forma ideal para a prova!"
    elif tsb_alvo < 5:
        sugestao = f"⚠️ TSB previsto: {tsb_alvo:+.0f} — taper insuficiente, considere reduzir mais a carga"
    else:
        sugestao = f"🟡 TSB previsto: {tsb_alvo:+.0f} — forma positiva mas pode estar descansado demais"

    return {
        "data_alvo": data_alvo_str,
        "dias_faltam": dias_faltam,
        "projecao": projecao,
        "estado_alvo": estado_alvo,
        "sugestao": sugestao,
    }


def calcular_watts_bloco(bloco, ftp):
    """Adiciona watts exatos e FC esperada a cada bloco de treino."""
    b = dict(bloco)
    w_min = int(ftp * b["pct_min"])
    w_max = int(ftp * b["pct_max"])
    w_avg = int(ftp * (b["pct_min"] + b["pct_max"]) / 2)
    b["watts_min"] = w_min
    b["watts_max"] = w_max
    b["watts_str"] = f"{w_min}-{w_max}W"
    b["cadencia_alvo"] = _cadencia_por_zona(b.get("zona", "Z2"))
    return b


def _cadencia_por_zona(zona):
    return {
        "Z1": "80-85rpm", "Z2": "85-90rpm", "Z3": "88-92rpm",
        "Z4": "90-95rpm", "Z5": "95-100rpm", "Z4-Z5": "90-100rpm",
        "Z1-Z2": "80-90rpm", "Z2-Z1": "80-90rpm", "Z3-Z4": "88-95rpm",
    }.get(zona, "85-90rpm")


def resumo_rpe_recente(atividades, dias=14):
    """Calcula RPE médio das últimas N atividades para calibrar dificuldade."""
    corte = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    recentes = [a for a in atividades if a["data"] >= corte and a.get("rpe")]
    if not recentes:
        return None
    rpes = [a["rpe"] for a in recentes]
    avg = sum(rpes) / len(rpes)
    return {
        "rpe_medio": round(avg, 1),
        "n_treinos": len(recentes),
        "interpretacao": (
            "Treinos muito fáceis — considere aumentar intensidade" if avg < 4 else
            "Carga adequada" if avg <= 6 else
            "Treinos muito duros — monitore recuperação" if avg <= 8 else
            "⚠️ Carga excessiva — risco de overtraining"
        )
    }
