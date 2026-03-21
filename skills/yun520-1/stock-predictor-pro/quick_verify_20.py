#!/usr/bin/env python3
import json, numpy as np, subprocess, time
from datetime import datetime

mcp = subprocess.Popen(['uvx', 'china-stock-mcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(3)

init = {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'v','version':'1.0'}}}
mcp.stdin.write(json.dumps(init)+'\n'); mcp.stdin.flush(); mcp.stdout.readline()

with open('/home/admin/openclaw/workspace/predictions/2026-03-18.json') as f: data = json.load(f)
preds = []
for e in data:
    if isinstance(e,dict) and 'predictions' in e: preds.extend(e['predictions'])
codes = list(set(p['stock_code'] for p in preds if 'stock_code' in p))[:20]
pd = {p['stock_code']:p for p in preds}

print('='*70); print(f'20 只股票验证 {datetime.now().strftime("%H:%M:%S")}'); print('='*70)

rs = []
for i,c in enumerate(codes):
    p = pd.get(c,{}); pc = p.get('predicted_change',0)
    call = {'jsonrpc':'2.0','method':'tools/call','params':{'name':'get_hist_data','arguments':{'symbol':c,'interval':'day'}}}
    mcp.stdin.write(json.dumps(call)+'\n'); mcp.stdin.flush(); time.sleep(1.5)
    try:
        r = json.loads(mcp.stdout.readline())
        ct = r['result']['content'][0]['text'].strip().split('\n')
        if len(ct)>=3:
            l = ct[-1].split('|')[1:-1]; pv = ct[-2].split('|')[1:-1]
            if len(l)>=5:
                cl = float(l[4].strip()); cp = float(pv[4].strip())
                ac = (cl-cp)/cp*100
                dc = (pc>0)==(ac>0); ae = abs(pc-ac)
                rs.append({'code':c,'name':p.get('stock_name','-'),'pred':pc,'actual':ac,'correct':dc,'error':ae})
                print(f'[{i+1:2d}/20] {c} {p.get("stock_name","-"):8s} 预测{pc:+6.2f}% 实际{ac:+6.2f}% {"✅" if dc else "❌"}')
    except Exception as e: print(f'[{i+1:2d}/20] {c} ❌ {e}')

mcp.terminate()

if rs:
    import pandas as pd
    df = pd.DataFrame(rs); t=len(rs); c=len(df[df['correct']]); a=c/t*100; m=df['error'].mean()
    print('\n'+'='*70); print(f'样本:{t} 正确:{c} 准确率:{a:.1f}% 平均误差:{m:.2f}%')
    print('\n✅ 正确:'); print(df[df['correct']].head(10).to_string(index=False))
    print('\n❌ 错误:'); print(df[~df['correct']].to_string(index=False))
    
    with open(f'/home/admin/openclaw/workspace/stock-recommendations/backtest/verify20_{datetime.now().strftime("%H%M")}.json','w') as f:
        json.dump({'time':datetime.now().isoformat(),'total':t,'correct':c,'accuracy':round(a,1),'mae':round(m,2),'details':rs},f,indent=2)
