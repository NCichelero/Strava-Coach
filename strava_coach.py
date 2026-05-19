"""
🚴 STRAVA COACH v9.4
- Zonas FC corrigidas (Z3: 145-160, Z4: 161-175, Z5: 176-190)
- Stream de potência para pico real de 5min
- VO2max duplo (FC + Potência)
- FC repouso por dia
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta

# ─── Configuração ──────────────────────────────────────────────────────────

def load_env():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    return env

ENV = load_env()

CLAUDE_API_KEY = ENV.get('CLAUDE_API_KEY', '')
INTERVALS_API_KEY = ENV.get('INTERVALS_API_KEY', '')
STRAVA_CLIENT_ID = ENV.get('STRAVA_CLIENT_ID', '')
STRAVA_CLIENT_SECRET = ENV.get('STRAVA_CLIENT_SECRET', '')
STRAVA_REFRESH_TOKEN = ENV.get('STRAVA_REFRESH_TOKEN', '')

FTP = 210
PESO = 75.6
FC_MAX = 190
FC_REPOUSO = 39

# Zonas FC corrigidas
ZONAS_FC = {
    'Z1': (115, 129),
    'Z2': (129, 145),
    'Z3': (145, 161),
    'Z4': (161, 176),
    'Z5': (176, 200),
}

# ─── Strava API ────────────────────────────────────────────────────────────

def get_strava_access_token():
    if not STRAVA_REFRESH_TOKEN:
        print("❌ STRAVA_REFRESH_TOKEN não encontrado")
        return None
    
    url = "https://www.strava.com/oauth/token"
    data = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 200:
            return r.json()['access_token']
        return None
    except:
        return None

def fetch_activities(access_token, days=60):
    after = int((datetime.now() - timedelta(days=days)).timestamp())
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'after': after, 'per_page': 100}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            ativ = r.json()
            print(f"✅ {len(ativ)} atividades baixadas")
            return ativ
        return []
    except:
        return []

def fetch_laps(access_token, activity_id):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/laps"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            time.sleep(15)
            return fetch_laps(access_token, activity_id)
        return []
    except:
        return []

def fetch_power_stream(access_token, activity_id):
    """Busca stream de potência (segundos) - para calcular pico de 5min"""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'keys': 'watts', 'key_by_type': 'true'}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            watts_data = data.get('watts', {}).get('data', [])
            return watts_data
        elif r.status_code == 429:
            time.sleep(15)
            return fetch_power_stream(access_token, activity_id)
        return []
    except:
        return []

# ─── Cálculos ──────────────────────────────────────────────────────────────

def pico_5min(watts_stream):
    """Calcula pico de potência de 5 minutos (300s)"""
    if not watts_stream or len(watts_stream) < 60:
        return 0
    
    janela = 300  # 5 min em segundos
    if len(watts_stream) < janela:
        # Atividade curta — usa média
        return round(sum(watts_stream) / len(watts_stream))
    
    melhor = 0
    soma = sum(watts_stream[:janela])
    melhor = soma / janela
    
    for i in range(janela, len(watts_stream)):
        soma += watts_stream[i] - watts_stream[i - janela]
        media = soma / janela
        if media > melhor:
            melhor = media
    
    return round(melhor)

def zona_por_fc(fc):
    """Zona baseado em FC (corrigida)"""
    if fc <= 0: return '—'
    if fc < 115: return 'Z1'
    if fc < 129: return 'Z1'
    if fc < 145: return 'Z2'
    if fc < 161: return 'Z3'
    if fc < 176: return 'Z4'
    return 'Z5'

def processar_laps(laps):
    """Processa laps com zonas corrigidas"""
    if not laps:
        return []
    
    laps_proc = []
    for i, lap in enumerate(laps):
        dur_seg = lap.get('elapsed_time', 0) or 0
        avg_pot = lap.get('average_watts', 0) or 0
        avg_fc = lap.get('average_heartrate', 0) or 0
        max_fc = lap.get('max_heartrate', 0) or 0
        
        # Zona — prioriza FC (mais confiável)
        if avg_fc > 0:
            zona = zona_por_fc(avg_fc)
        elif avg_pot > 50:
            pct = avg_pot / FTP
            if pct < 0.55: zona = 'Z1'
            elif pct < 0.75: zona = 'Z2'
            elif pct < 0.90: zona = 'Z3'
            elif pct < 1.05: zona = 'Z4'
            else: zona = 'Z5'
        else:
            zona = '—'
        
        laps_proc.append({
            'idx': i + 1,
            'nome': lap.get('name', f'Lap {i+1}'),
            'dur_seg': int(dur_seg),
            'dur_min': round(dur_seg / 60, 1),
            'dist_km': round((lap.get('distance', 0) or 0) / 1000, 2),
            'vel_avg': round((lap.get('average_speed', 0) or 0) * 3.6, 1),
            'pot_avg': int(avg_pot),
            'pot_max': int(lap.get('max_watts', 0) or 0),
            'fc_avg': int(avg_fc),
            'fc_max': int(max_fc),
            'zona': zona,
        })
    
    return laps_proc

def categorizar(activity):
    nome = activity.get('name', '').lower()
    tipo = activity.get('type', '').lower()
    sport_type = activity.get('sport_type', '').lower()
    
    if any(k in tipo or k in sport_type for k in ['ride', 'cycling', 'ebike']):
        return 'ciclismo'
    if any(k in nome for k in ['bike', 'ciclismo', 'pedal', 'mtb']):
        return 'ciclismo'
    if any(k in tipo or k in sport_type for k in ['weight', 'workout', 'crossfit', 'strength']):
        return 'academia'
    if any(k in nome for k in ['academia', 'gym', 'força', 'forca', 'musculação']):
        return 'academia'
    return 'outros'

# ─── Wellness Intervals.icu ────────────────────────────────────────────────

def fetch_wellness(days=60):
    if not INTERVALS_API_KEY:
        return []
    
    headers = {'Authorization': f'Bearer {INTERVALS_API_KEY}'}
    oldest = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    newest = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://intervals.icu/api/v1/athlete/0/wellness?oldest={oldest}&newest={newest}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Wellness: {len(data)} dias")
            return data
        else:
            print(f"⚠️  Wellness indisponível ({r.status_code})")
            return []
    except:
        return []

# ─── Fitness Local ─────────────────────────────────────────────────────────

def calcular_fitness_local(atividades):
    if not atividades:
        return {'ctl': 36, 'atl': 54, 'tsb': -18}
    
    tss_diario = {}
    for a in atividades:
        try:
            data = a.get('start_date', '')[:10]
            duracao = (a.get('elapsed_time', 0) or 0) / 60
            pot = a.get('weighted_average_watts') or a.get('average_watts') or 0
            
            if pot > 50:
                tss = duracao * (pot / FTP) ** 2 * 100 / 60
            else:
                fc = a.get('average_heartrate', 0) or 0
                if fc > 0:
                    tss = duracao * (fc / FC_MAX) ** 2 * 100 / 60
                else:
                    tss = duracao * 0.5
            
            tss_diario[data] = tss_diario.get(data, 0) + tss
        except:
            continue
    
    hoje = datetime.now().date()
    ctl = atl = 0
    for i in range(42, -1, -1):
        data = (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        tss = tss_diario.get(data, 0)
        ctl = ctl + (tss - ctl) / 42
        if i <= 7:
            atl = atl + (tss - atl) / 7
    
    return {'ctl': round(ctl, 1), 'atl': round(atl, 1), 'tsb': round(ctl - atl, 1)}

# ─── Salvar ────────────────────────────────────────────────────────────────

def save_data(atividades, wellness, fitness, laps_dict, pico5min_dict):
    os.makedirs('data', exist_ok=True)
    
    # Map wellness por data (para FC repouso por dia)
    wellness_por_data = {w.get('id', w.get('date', '')): w for w in wellness}
    
    treinos = {}
    for a in atividades:
        tid = str(a.get('id', ''))
        cat = categorizar(a)
        data = a.get('start_date_local', '')[:10]
        
        treino = {
            'id': tid,
            'data': data,
            'nome': a.get('name', 'Sem nome'),
            'categoria': cat,
            'tipo': a.get('type', ''),
            'sport_type': a.get('sport_type', ''),
            'duracao_min': round((a.get('elapsed_time', 0) or 0) / 60, 1),
            'distancia_km': round((a.get('distance', 0) or 0) / 1000, 2),
            'potencia_avg': a.get('average_watts', 0) or 0,
            'potencia_max': a.get('max_watts', 0) or 0,
            'potencia_norm': a.get('weighted_average_watts', 0) or 0,
            'fc_avg': a.get('average_heartrate', 0) or 0,
            'fc_max': a.get('max_heartrate', 0) or 0,
            'elevacao': a.get('total_elevation_gain', 0) or 0,
            'velocidade_avg': round((a.get('average_speed', 0) or 0) * 3.6, 1),
            'velocidade_max': round((a.get('max_speed', 0) or 0) * 3.6, 1),
            'calorias': a.get('calories', 0) or 0,
            'cadence_avg': a.get('average_cadence', 0) or 0,
            'kilojoules': a.get('kilojoules', 0) or 0,
            'source': 'strava',
            'laps': laps_dict.get(tid, []),
            'pico_5min': pico5min_dict.get(tid, 0),
        }
        
        # FC repouso do dia (do wellness, se disponível)
        wellness_dia = wellness_por_data.get(data, {})
        treino['fc_repouso_dia'] = wellness_dia.get('restingHR', 0) or 0
        
        treinos[tid] = treino
    
    with open('data/treinos.json', 'w', encoding='utf-8') as f:
        json.dump(treinos, f, ensure_ascii=False, indent=2)
    with open('data/wellness.json', 'w', encoding='utf-8') as f:
        json.dump(wellness, f, ensure_ascii=False, indent=2)
    with open('data/fitness.json', 'w', encoding='utf-8') as f:
        json.dump(fitness, f, ensure_ascii=False, indent=2)
    
    return treinos

# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    print("🚴 Strava Coach v9.4 (Laps + Streams + VO2max duplo)\n")
    
    print("🔐 Autenticando...")
    token = get_strava_access_token()
    if not token:
        print("❌ Falha")
        sys.exit(1)
    print("✅ OK\n")
    
    print("📥 Baixando atividades (60d)...")
    ativ = fetch_activities(token, days=60)
    
    # Filtra ciclismo
    ciclismo = [a for a in ativ if categorizar(a) == 'ciclismo']
    print(f"\n📥 Processando {len(ciclismo)} treinos de ciclismo...")
    print("   (laps + streams de potência — pode demorar)")
    
    laps_dict = {}
    pico5_dict = {}
    
    for i, a in enumerate(ciclismo, 1):
        aid = str(a.get('id', ''))
        nome = a.get('name', '')[:40]
        
        # Laps
        laps = fetch_laps(token, aid)
        if laps:
            laps_dict[aid] = processar_laps(laps)
        
        # Stream de potência (só se tiver powermeter)
        pico5 = 0
        if a.get('average_watts', 0) > 50:
            stream = fetch_power_stream(token, aid)
            pico5 = pico_5min(stream)
            pico5_dict[aid] = pico5
        
        info_pico = f" · Pico5min: {pico5}W" if pico5 > 0 else ""
        info_laps = f" · {len(laps_dict.get(aid, []))} laps" if laps_dict.get(aid) else ""
        print(f"   [{i}/{len(ciclismo)}] {nome}{info_laps}{info_pico}")
        
        # Rate limit pause
        if i % 8 == 0:
            time.sleep(3)
    
    print(f"\n✅ {sum(len(v) for v in laps_dict.values())} laps")
    print(f"✅ {len(pico5_dict)} streams processados")
    
    print("\n📊 Wellness Intervals.icu...")
    wellness = fetch_wellness(days=60)
    
    if wellness:
        latest = wellness[-1]
        fitness = {
            'ctl': latest.get('ctl', 36),
            'atl': latest.get('atl', 54),
            'tsb': latest.get('ctl', 36) - latest.get('atl', 54)
        }
    else:
        print("📊 Fitness local...")
        fitness = calcular_fitness_local(ativ)
    
    print(f"\n💪 CTL={fitness['ctl']} | ATL={fitness['atl']} | TSB={fitness['tsb']}")
    
    treinos = save_data(ativ, wellness, fitness, laps_dict, pico5_dict)
    
    cic = sum(1 for t in treinos.values() if t['categoria'] == 'ciclismo')
    ac = sum(1 for t in treinos.values() if t['categoria'] == 'academia')
    
    # Pico de 5min das últimas 2 semanas
    duas_sem = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    pico5_recent = [t['pico_5min'] for t in treinos.values() 
                    if t['data'] >= duas_sem and t.get('pico_5min', 0) > 0]
    melhor_pico5 = max(pico5_recent) if pico5_recent else 0
    
    print(f"\n📈 Resumo:")
    print(f"   🚴 Ciclismo: {cic} | 🏋️ Academia: {ac} | Total: {len(treinos)}")
    print(f"   ⚡ Melhor pico 5min (14d): {melhor_pico5}W")
    if melhor_pico5 > 0:
        wkg_5min = melhor_pico5 / PESO
        vo2_pot = 16.6 + (8.87 * wkg_5min)
        print(f"   🫁 VO2max (potência 5min): {vo2_pot:.1f} ml/kg/min ({wkg_5min:.2f} W/kg)")
    
    vo2_fc = 15 * (FC_MAX / FC_REPOUSO)
    print(f"   🫁 VO2max (FC): {vo2_fc:.1f} ml/kg/min")
    
    print("\n✅ Dados salvos!")

if __name__ == '__main__':
    main()
