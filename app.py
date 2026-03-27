import os
from flask import Flask, request, render_template_string, redirect, url_for, session
from supabase import create_client
from datetime import datetime

app = Flask(__name__)
app.secret_key = "msm_super_lista_v6_final"

# Configuração Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin123")
supabase = create_client(url, key)

# Design Profissional Traders Arena (Ciano & Dark)
STYLE = """
<style>
    body{background:#050505;color:#fff;font-family:sans-serif;margin:0;padding:0;}
    .nav{display:flex;background:#0a0a0a;border-bottom:1px solid #1a1a1a;justify-content:center;position:sticky;top:0;z-index:100;}
    .nav a{color:#666;padding:15px;text-decoration:none;font-weight:bold;font-size:13px;}
    .nav a.active{color:#00e5ff;border-bottom:2px solid #00e5ff;}
    .container{padding:20px;max-width:600px;margin:auto;text-align:center;}
    .card{background:#0a0a0a;border:1px solid #1a1a1a;padding:20px;border-radius:15px;margin-bottom:15px;text-align:left;}
    .btn{background:#00e5ff;color:#000;padding:12px 20px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;width:100%;margin-top:10px;text-decoration:none;display:inline-block;text-align:center;}
    input, select{width:100%;padding:12px;margin:10px 0;background:#111;border:1px solid #222;color:#fff;border-radius:8px;box-sizing:border-box;}
    .signal{border-left:4px solid #00e5ff;padding:15px;background:#0f0f0f;margin:10px 0;border-radius:0 10px 10px 0;}
    .tag{font-size:10px;color:#00e5ff;text-transform:uppercase;letter-spacing:1px;}
    .check-list{max-height:400px;overflow-y:auto;background:#111;padding:10px;border-radius:10px;text-align:left;}
    .check-item{display:flex;align-items:center;padding:10px;border-bottom:1px solid #1a1a1a;justify-content:space-between;}
    .check-item input{width:18px;height:18px;margin:0;}
</style>
"""

def get_device(): return request.headers.get('User-Agent', 'unknown')

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
                return "Assinatura Expirada. Contacte o Admin."
            curr = get_device()
            if not u.get('device_id'):
                supabase.table("users_msm").update({"device_id": curr}).eq("mql_id", mql).execute()
            elif u.get('device_id') != curr:
                return "Erro: Este ID está trancado noutro dispositivo."
            session['user_mql'] = mql
            return redirect(url_for('monitor'))
        return "ID MQL não autorizado."
    return render_template_string(STYLE + '<div class="container"><div class="card"><h2>MSM ARENA</h2><form method="POST"><input name="mql_id" placeholder="ID MQL"><button class="btn">ACESSAR</button></form></div></div>')

@app.route('/aba/config', methods=['GET', 'POST'])
def config():
    if 'user_mql' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        ativos = request.form.getlist('ativos')
        supabase.table("users_msm").update({"ativos": ",".join(ativos)}).eq("mql_id", session['user_mql']).execute()
        return redirect(url_for('monitor'))
    
    superlista = [
        "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "USDCAD", "USDCHF", 
        "NAS100", "USTEC", "US30", "US500", "GER40", 
        "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD",
        "BOOM100", "BOOM500", "BOOM300", "CRASH1000", "CRASH500", "CRASH300",
        "Volatility 10", "Volatility 25", "Volatility 50", "Volatility 75", "Volatility 100",
        "Volatility 10(1s)", "Volatility 25(1s)", "Volatility 50(1s)", "Volatility 75(1s)", "Volatility 100(1s)", "Volatility 250(1s)"
    ]
    return render_template_string(STYLE + """
    <div class="nav"><a href="/monitor">MONITOR</a><a href="/aba/config" class="active">CONFIG</a></div>
    <div class="container"><div class="card"><h3>Seus Ativos</h3><form method="POST"><div class="check-list">
    {% for a in lista %}<div class="check-item"><span>{{a}}</span><input type="checkbox" name="ativos" value="{{a}}"></div>{% endfor %}
    </div><button class="btn">SALVAR ESCOLHAS</button></form></div></div>
    """, lista=superlista)

@app.route('/monitor')
def monitor():
    if 'user_mql' not in session: return redirect(url_for('login'))
    u = supabase.table("users_msm").select("ativos").eq("mql_id", session['user_mql']).execute().data[0]
    meus_ativos = u.get('ativos', '').split(',') if u.get('ativos') else []
    
    sinais = supabase.table("sinais_msm").select("*").order("created_at", desc=True).limit(100).execute().data
    filtrados = [s for s in sinais if any(a.upper() in s['msg'].upper() for a in meus_ativos)][:10]
    
    return render_template_string(STYLE + """
    <div class="nav"><a href="/monitor" class="active">MONITOR</a><a href="/aba/config">CONFIG</a></div>
    <div class="container">
    {% for s in filtrados %}<div class="signal"><span class="tag">{{s.created_at[11:16]}}</span><p>{{s.msg}}</p></div>
    {% else %}<p>Nenhum sinal dos teus ativos escolhidos.</p>{% endfor %}
    <br><a href="/logout" style="color:#444;text-decoration:none;font-size:11px;">Sair do Sistema</a></div>
    """, filtrados=filtrados)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'adm' not in session:
        if request.method == 'POST' and request.form.get('pw') == ADMIN_PASS:
            session['adm'] = True
            return redirect(url_for('admin'))
        return render_template_string(STYLE + '<div class="container"><h3>ADMIN MSM</h3><form method="POST"><input type="password" name="pw" placeholder="Senha Mestre"><button class="btn">ENTRAR</button></form></div>')
    
    if request.args.get('restart'):
        supabase.table("users_msm").update({"device_id": None}).eq("mql_id", request.args.get('restart')).execute()
        return redirect(url_for('admin'))

    if request.method == 'POST':
        supabase.table("users_msm").insert({"mql_id": request.form.get('id'), "nome": request.form.get('nome'), "validade": request.form.get('validade'), "status": "ACTIVO"}).execute()

    users = supabase.table("users_msm").select("*").execute().data
    return render_template_string(STYLE + """
    <div class="container"><h3>GESTÃO DE CLIENTES</h3>
    <form method="POST" class="card"><input name="nome" placeholder="Nome"><input name="id" placeholder="ID MQL"><input name="validade" type="date"><button class="btn">CADASTRAR</button></form>
    {% for u in users %}<div class="card" style="display:flex;justify-content:space-between;align-items:center;">
    <div><b>{{u.nome}}</b><br><small>ID: {{u.mql_id}} | Exp: {{u.validade}}</small></div>
    <a href="/admin?restart={{u.mql_id}}" class="btn" style="width:auto;font-size:10px;padding:5px 10px;">RESTART DEVICE</a></div>{% endfor %}</div>
    """, users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and 'msg' in data:
        supabase.table("sinais_msm").insert({"msg": data['msg']}).execute()
        return "ok", 200
    return "error", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
