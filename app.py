import os
from flask import Flask, request, render_template_string, redirect, url_for, session
from supabase import create_client

app = Flask(__name__)
app.secret_key = "msm_arena_v2"

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

STYLE = "<style>body{background:#050505;color:#fff;font-family:sans-serif;text-align:center;padding:50px;}.btn{display:block;padding:15px;background:#00e5ff;color:#000;text-decoration:none;font-weight:bold;border-radius:5px;margin:10px auto;max-width:300px;border:none;cursor:pointer;}input{padding:12px;margin:10px;width:280px;border-radius:5px;border:none;background:#111;color:#fff;}</style>"

@app.route('/')
def home(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mql = request.form.get('mql_id')
        res = supabase.table("users_msm").select("*").eq("mql_id", mql).execute()
        if res.data:
            session['mql_id'] = mql
            return redirect(url_for('monitor'))
        return "ID Invalido."
    return render_template_string(STYLE + '<h1>AREA MSM</h1><form method="POST"><input name="mql_id" placeholder="ID MQL"><button class="btn">ENTRAR</button></form>')

@app.route('/monitor')
def monitor():
    mql = session.get('mql_id')
    if not mql: return redirect(url_for('login'))
    s_res = supabase.table("sinais_msm").select("*").order("created_at", desc=True).limit(10).execute()
    return render_template_string(STYLE + '<h1>SINAIS</h1>{% for s in l %}<div style="border:1px solid #222;margin:10px;padding:10px;">{{s.msg}}</div>{% endfor %}<a href="/logout" class="btn">SAIR</a>', l=s_res.data)

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
