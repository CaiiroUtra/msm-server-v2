import os
from flask import Flask, request, render_template_string, redirect, url_for, session
from supabase import create_client
from datetime import datetime

app = Flask(__name__)
app.secret_key = "msm_arena_ultra_v9_final"

# Configurações
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin123")
ONE_SIGNAL_ID = "9d4cafb3-0dd3-4420-a502-bf4b4a6ee2b3"
SERVER_KEY_EA = "MTC_MSM_2026"

supabase = create_client(url, key)

STYLE = """
<style>
    body{background:#020202;color:#fff;font-family:'Segoe UI',sans-serif;margin:0;padding:0;}
    .nav{display:flex;background:#080808;border-bottom:1px solid #111;justify-content:center;position:sticky;top:0;z-index:100;}
    .nav a{color:#555;padding:18px;text-decoration:none;font-weight:bold;font-size:13px;transition:0.3s;}
    .nav a.active{color:#00e5ff;text-shadow: 0 0 10px #00e5ff;}
    .status-bar{background:#0a0a0a;padding:15px;border-radius:12px;margin-bottom:15px;border:1px solid #1a1a1a;}
    .dot {height:10px;width:10px;background-color:#00e5ff;border-radius:50%;display:inline-block;margin-right:8px;box-shadow:0 0 8px #00e5ff;animation:pulse 1.5s infinite;}
    @keyframes pulse {0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;}}
    .container{padding:20px;max-width:500px;margin:auto;}
    .card-signal{background:#0d0d0d;border:1px solid #1a1a1a;padding:18px;border-radius:15px;margin-bottom:12px;position:relative;}
    .buy{border-left:5px solid #00e5ff;}
    .sell{border-left:5px solid #ff0055;}
    .time{font-size:11px;color:#444;position:absolute;top:15px;right:15px;}
    .btn{background:#00e5ff;color:#000;padding:14px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;width:100%;text-decoration:none;display:inline-block;text-align:center;}
    .check-list{max-height:450px;overflow-y:auto;background:#080808;padding:10px;border-radius:10px;border:1px solid #111;}
    .check-item{display:flex;align-items:center;padding:12px;border-bottom:1px solid #111;justify-content:space-between;}
    input[type="checkbox"]{width:22px;height:22px;accent-color:#00e5ff;}
    input[type="text"], input[type="password"]{width:100%;padding:15px;background:#0d0d0d;border:1px solid #1a1a1a;color:#fff;border-radius:10px;margin-bottom:10px;box-sizing:border-box;}
</style>
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
<script>
  window.OneSignalDeferred = window.OneSignalDeferred || [];
  OneSignalDeferred.push(function(OneSignal) {
    OneSignal.init({ appId: \"""" + ONE_SIGNAL_ID + """\" });
  });
</script>
"""

@app.route('/')
def home(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mql = request.form.get('mql_id')
        user = supabase.table("users_msm").select("*").eq("mql_id", mql).execute().data
        if user:
            u = user[0]
            if u.get('validade') and datetime.strptime(u['validade'], '%Y-%m-%d').date() < datetime.now().date():
                return "Acesso Expirado."
            curr = request.headers.get('User-Agent', 'unknown')
            if not u.get('device_id'):
                supabase.table("users_msm").update({"device_id": curr}).eq("mql_id", mql).execute()
            elif u.get('device_id') != curr:
                return "Erro: Dispositivo não autorizado."
            session['user_mql'] = mql
            session['user_nome'] = u.get('nome', 'Trader')
            session['user_val'] = u.get('validade', '---')
            return redirect(url_for('monitor'))
        return "ID Inválido."
    return render_template_string(STYLE + '<div class="container" style="margin-top:100px;text-align:center;"><h1 style="color:#00e5ff;">MSM ARENA</h1><form method="POST"><input name="mql_id" placeholder="TEU ID MQL"><button class="btn">ENTRAR</button></form></div>')

@app.route('/monitor')
def monitor():
    if 'user_mql' not in session: return redirect(url_for('login'))
    u = supabase.table("users_msm").select("ativos").eq("mql_id", session['user_mql']).execute().data[0]
    meus_ativos_str = u.get('ativos', '')
    meus_ativos = meus_ativos_str.split(',') if meus_ativos_str else []
    
    sinais = supabase.table("sinais_msm").select("*").order("created_at", desc=True).limit(50).execute().data
    filtrados = [s for s in sinais if any(a.upper() in s['msg'].upper() for a in meus_ativos)][:10]
    
    return render_template_string(STYLE + """
    <div class="nav"><a href="/monitor" class="active">MONITOR</a><a href="/aba/config">CONFIG</a></div>
    <div class="container">
        <p style="font-size:12px; color:#555; margin-bottom:10px;">Olá, <b>{{nome}}</b></p>
        <div class="status-bar">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div><span class="dot"></span><span style="font-size:12px;color:#00e5ff;">LIVE MONITOR</span></div>
                <div style="text-align:right;"><small style="color:#444;">Expira em:</small> <b style="font-size:12px;">{{val}}</b></div>
            </div>
            <div style="margin-top:10px; padding-top:10px; border-top:1px solid #111;">
                <small style="color:#333; display:block; font-size:10px;">A MONITORIZAR:</small>
                <span style="font-size:11px; color:#666;">{{ativos_list if ativos_list else 'Nenhum ativo selecionado'}}</span>
            </div>
        </div>
        
        {% for s in filtrados %}
        <div class="card-signal {% if 'BUY' in s.msg.upper() or 'COMPRA' in s.msg.upper() %}buy{% elif 'SELL' in s.msg.upper() or 'VENDA' in s.msg.upper() %}sell{% endif %}">
            <span class="time">{{s.created_at[11:16]}}</span>
            <p style="margin:0; font-size:14px;">{{s.msg}}</p>
        </div>
        {% else %}
        <div style="text-align:center; padding:40px 0; color:#222;">Aguardando novos sinais...</div>
        {% endfor %}
    </div>
    """, filtrados=filtrados, val=session.get('user_val'), nome=session.get('user_nome'), ativos_list=meus_ativos_str)

@app.route('/aba/config', methods=['GET', 'POST'])
def config():
    if 'user_mql' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        ativos = request.form.getlist('ativos')
        supabase.table("users_msm").update({"ativos": ",".join(ativos)}).eq("mql_id", session['user_mql']).execute()
        return redirect(url_for('monitor'))
    
    superlista = ["EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD", "NAS100", "USTEC", "US30", "US500", "GER40", "HK50", "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD", "BOOM1000", "BOOM500", "BOOM300", "CRASH1000", "CRASH500", "CRASH300", "Volatility 10", "Volatility 25", "Volatility 50", "Volatility 75", "Volatility 100", "Volatility 10(1s)", "Volatility 25(1s)", "Volatility 50(1s)", "Volatility 75(1s)", "Volatility 100(1s)", "Volatility 250(1s)"]
    return render_template_string(STYLE + """
    <div class="nav"><a href="/monitor">MONITOR</a><a href="/aba/config" class="active">CONFIG</a></div>
    <div class="container">
        <div class="card-signal" style="border:1px dashed #00e5ff; text-align:center;">
            <button onclick="OneSignal.showNativePrompt()" class="btn" style="background:transparent;border:1px solid #00e5ff;color:#00e5ff;font-size:11px;">🔔 ATIVAR NOTIFICAÇÕES</button>
        </div>
        <form method="POST">
            <div class="check-list">
            {% for a in lista %}<div class="check-item"><span>{{a}}</span><input type="checkbox" name="ativos" value="{{a}}"></div>{% endfor %}
            </div>
            <button class="btn" style="margin-top:20px;">SALVAR CONFIGURAÇÃO</button>
        </form>
    </div>
    """, lista=superlista)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'adm' not in session:
        if request.method == 'POST' and request.form.get('pw') == ADMIN_PASS:
            session['adm'] = True
            return redirect(url_for('admin'))
        return render_template_string(STYLE + '<div class="container"><h3>ADMIN</h3><form method="POST"><input type="password" name="pw" placeholder="Senha"><button class="btn">LOGIN</button></form></div>')
    
    if request.args.get('restart'):
        supabase.table("users_msm").update({"device_id": None}).eq("mql_id", request.args.get('restart')).execute()
        return redirect(url_for('admin'))

    if request.method == 'POST':
        supabase.table("users_msm").insert({"mql_id": request.form.get('id'), "nome": request.form.get('nome'), "validade": request.form.get('validade'), "status": "ACTIVO"}).execute()

    users = supabase.table("users_msm").select("*").execute().data
    return render_template_string(STYLE + """
    <div class="container"><h3>GESTÃO</h3>
    <form method="POST" class="card-signal"><input name="nome" placeholder="Nome"><input name="id" placeholder="ID MQL"><input name="validade" type="date" style="width:100%;padding:15px;margin-bottom:10px;background:#0d0d0d;color:#fff;border:1px solid #1a1a1a;border-radius:10px;"><button class="btn">CADASTRAR</button></form>
    {% for u in users %}<div class="card-signal" style="display:flex;justify-content:space-between;align-items:center;">
    <div><b>{{u.nome}}</b><br><small>{{u.mql_id}} | {{u.validade}}</small></div>
    <a href="/admin?restart={{u.mql_id}}" class="btn" style="width:auto;font-size:10px;">RESET</a></div>{% endfor %}</div>
    """, users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and data.get('key') == SERVER_KEY_EA:
        if 'msg' in data:
            supabase.table("sinais_msm").insert({"msg": data['msg']}).execute()
            return "ok", 200
    return "error", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
