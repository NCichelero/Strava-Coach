"""
🔐 Strava OAuth — Gera novo Refresh Token
"""

import requests
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time

# Suas credenciais
STRAVA_CLIENT_ID = "234497"
STRAVA_CLIENT_SECRET = input("Cole seu STRAVA_CLIENT_SECRET: ").strip()

# URLs
AUTH_URL = f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8000&scope=activity:read_all"
TOKEN_URL = "https://www.strava.com/oauth/token"

print(f"\n✅ Abrindo navegador para autenticação...\n")
print(f"URL: {AUTH_URL}\n")

# Abre navegador
webbrowser.open(AUTH_URL)

# Aguarda resposta
code = None

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global code
        query = urlparse(self.path).query
        params = parse_qs(query)
        code = params.get('code', [None])[0]
        
        if code:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write("<h1>OK - Autenticado!</h1><p>Voce pode fechar esta janela.</p>".encode('utf-8'))
            print(f"\n✅ Código recebido: {code}\n")
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Silencia logs

print("⏳ Aguardando autorização (janela do navegador abriu)...")
print("💡 Quando terminar de autorizar, feche a janela do navegador.\n")

server = HTTPServer(('localhost', 8000), AuthHandler)
timeout = time.time() + 300  # 5 minutos

while code is None and time.time() < timeout:
    server.handle_request()

if not code:
    print("❌ Timeout — nenhum código recebido")
    exit(1)

# Troca código por token
print("🔄 Trocando código por token...")

data = {
    'client_id': STRAVA_CLIENT_ID,
    'client_secret': STRAVA_CLIENT_SECRET,
    'code': code,
    'grant_type': 'authorization_code'
}

response = requests.post(TOKEN_URL, data=data)

if response.status_code != 200:
    print(f"❌ Erro: {response.status_code}")
    print(response.json())
    exit(1)

tokens = response.json()
refresh_token = tokens['refresh_token']
access_token = tokens['access_token']

print(f"\n✅ Tokens obtidos!")
print(f"\nCopie estas linhas e atualize seu .env:\n")
print(f"STRAVA_REFRESH_TOKEN={refresh_token}")
print(f"\n(Access Token expira em breve, use sempre o Refresh Token)")

# Salva no .env
with open('.env', 'a') as f:
    f.write(f"\nSTRAVA_REFRESH_TOKEN={refresh_token}\n")

print(f"\n✅ .env atualizado automaticamente!")