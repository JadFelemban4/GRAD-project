"""Temporary localhost acceptance fixture, explicitly separate from real results.

Run from the repository root with -B. All generated data stays under app.
This server is never mounted by app.server and must be stopped after testing.
"""
import json
from pathlib import Path
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.record_api import install_record_routes

APP_ROOT=Path(__file__).resolve().parents[1]
FIXTURE_ROOT=APP_ROOT/'.superpowers/training-linked-app/tmp/browser-record-root'
assert FIXTURE_ROOT.resolve().is_relative_to(APP_ROOT)
POLICY=FIXTURE_ROOT/'results/agents/browser_fixture/sighted_seed0'
POLICY.mkdir(parents=True,exist_ok=True)
(POLICY.parent/'index.json').write_text(json.dumps({'policies':{'sighted_seed0':{}}}),encoding='utf-8')
(POLICY/'eval_summary.json').write_text(json.dumps({'policy':'sighted_seed0','protocol':'browser fixture dt 0.25'}),encoding='utf-8')
n=240
action=np.zeros((1,n,5),dtype=np.float32)
action[0,:,0]=np.linspace(-1,1,n)
applied=np.zeros((1,n,5),dtype=np.float32)
applied[0,:,0]=np.arange(n)*.01
obs=np.zeros((1,n,23),dtype=np.float32)
obs[0,:,14]=.2
np.savez_compressed(POLICY/'eval_record.npz',action=action,applied=applied,obs=obs,
  reward=np.linspace(-2,0,n,dtype=np.float32)[None,:],t_turb=(573.15+np.arange(n))[None,:],
  t_oil=np.full((1,n),363.15),t_block=np.full((1,n),373.15),
  torque=np.full((1,n),120.),torque_req=np.full((1,n),125.),grade=np.zeros((1,n)))
app=FastAPI()
app.mount('/static',StaticFiles(directory=APP_ROOT/'static'),name='static')
install_record_routes(app,FIXTURE_ROOT)
@app.get('/')
def fixture_page():
    return fixture_response()

@app.get('/fallback')
def fallback_page():
    return fixture_response(fallback=True)

@app.get('/fixture-no-webgl.mjs')
def no_webgl_module():
    return Response("export * from '/static/vendor/three/three.module.js'; export class WebGLRenderer { constructor() { throw new Error('Acceptance fixture: WebGL unavailable'); } }", media_type='text/javascript')

def fixture_response(fallback=False):
    html='''<!doctype html><html lang="ar" dir="rtl" data-theme="dark"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/sim/style.css"><link rel="stylesheet" href="/static/sim/agents.css"><link rel="stylesheet" href="/static/sim/results.css">
<script type="importmap">{"imports":{"three":"/static/vendor/three/three.module.js","three/addons/":"/static/vendor/three/addons/"}}</script>
<body><main class="agents-main"><p style="padding:12px;border:2px solid #c99045">اختبار واجهة ببيانات صغيرة — ليست نتيجة تجربة / UI fixture, not scientific results</p>
<button id="fixture-lang">EN / AR</button><button id="fixture-theme">Light / Dark</button><section id="saved-records" class="saved-records"></section></main>
<script type="module">import {createRecordView} from '/static/sim/record-view.mjs?v=20261009';let lang='ar';
const viewer=createRecordView(document.getElementById('saved-records'),{lang,initialSource:'results/agents/browser_fixture'});viewer.refresh();
document.getElementById('fixture-lang').onclick=()=>{lang=lang==='ar'?'en':'ar';document.documentElement.lang=lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr';viewer.setLanguage(lang);};
document.getElementById('fixture-theme').onclick=()=>{const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;viewer.setTheme(t);};
window.addEventListener('pagehide',()=>viewer.dispose());</script></body></html>'''
    if fallback:
        html=html.replace('"three":"/static/vendor/three/three.module.js"', '"three":"/fixture-no-webgl.mjs"')
    return HTMLResponse(html)
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8881,log_level='warning')
