"""
app.py — Flask REST API for the Trading Bot UI
Place this file in the root of your trading_bot/ directory.
Run: python app.py
"""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

from bot import BinanceClient, place_order, validate_order_inputs
from bot.client import BASE_URL
from bot.logging_config import setup_logger

load_dotenv()
logger = setup_logger("trading_bot.api")

app = Flask(__name__)
CORS(app)  # Allow the React UI (different port) to call this API


def get_client() -> BinanceClient:
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env")
    return BinanceClient(api_key, api_secret)


# ── Homepage UI ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return render_template_string(DASHBOARD_HTML)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trading Bot — Binance Futures Testnet</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#f0f0f0;font-family:'JetBrains Mono',monospace;min-height:100vh}
input,select{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px 12px;color:#f0f0f0;font-family:'JetBrains Mono',monospace;font-size:12px;outline:none;width:100%;transition:border-color 0.15s}
input:focus,select:focus{border-color:rgba(255,255,255,0.3)}
input[type=number]::-webkit-inner-spin-button{opacity:0.3}
select{cursor:pointer;appearance:none}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#222;border-radius:2px}
.lbl{display:block;font-size:9px;font-weight:600;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px}
.card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px}
.section-title{font-size:10px;color:#444;letter-spacing:2px;margin-bottom:14px}
.price-val{font-size:16px;font-weight:700;color:#f0f0f0;line-height:1}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
@keyframes fadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.fade-in{animation:fadeIn 0.3s ease forwards}
.dot-live{width:7px;height:7px;border-radius:50%;background:#00c896;box-shadow:0 0 8px #00c896;display:inline-block;animation:pulse 2s infinite}
@media(max-width:800px){.main-grid{grid-template-columns:1fr !important}.price-grid{grid-template-columns:repeat(2,1fr) !important}}
</style>
</head>
<body>

<!-- TOP BAR -->
<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 22px;border-bottom:1px solid rgba(255,255,255,0.07);background:rgba(0,0,0,0.7);position:sticky;top:0;z-index:10;backdrop-filter:blur(10px)">
  <div style="display:flex;align-items:center;gap:12px">
    <div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#00c896,#006650);display:flex;align-items:center;justify-content:center;font-size:16px">⚡</div>
    <div>
      <div style="font-size:14px;font-weight:700;letter-spacing:1px">TRADING BOT</div>
      <div style="font-size:9px;color:#444;letter-spacing:2px">BINANCE FUTURES TESTNET</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:8px">
    <span id="status-dot" class="dot-live"></span>
    <span id="status-txt" style="font-size:10px;color:#555;letter-spacing:1px">CONNECTED</span>
  </div>
</div>

<div style="max-width:1100px;margin:0 auto;padding:22px 18px">

  <!-- PRICE CARDS -->
  <div id="price-grid" class="price-grid" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:22px"></div>

  <!-- MAIN GRID -->
  <div class="main-grid" style="display:grid;grid-template-columns:340px 1fr;gap:16px">

    <!-- ORDER FORM -->
    <div class="card">
      <div class="section-title">PLACE ORDER</div>

      <div style="margin-bottom:14px">
        <label class="lbl">Symbol</label>
        <select id="sym" onchange="updateSubmitBtn()">
          <option>BTCUSDT</option><option>ETHUSDT</option><option>BNBUSDT</option><option>SOLUSDT</option><option>XRPUSDT</option>
        </select>
      </div>

      <div style="margin-bottom:14px">
        <label class="lbl">Side</label>
        <div style="display:flex;gap:8px">
          <button id="btn-buy" onclick="setSide('BUY')" style="flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(0,200,150,0.18);color:#00c896;outline:1px solid #00c896;transition:all 0.2s">▲ BUY</button>
          <button id="btn-sell" onclick="setSide('SELL')" style="flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(255,255,255,0.04);color:#444;outline:1px solid rgba(255,255,255,0.08);transition:all 0.2s">▼ SELL</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label class="lbl">Order Type</label>
        <div style="display:flex;gap:8px">
          <button id="btn-market" onclick="setType('MARKET')" style="flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:11px;background:rgba(255,255,255,0.1);color:#f0f0f0;outline:1px solid rgba(255,255,255,0.3);transition:all 0.2s">MARKET</button>
          <button id="btn-limit" onclick="setType('LIMIT')" style="flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:11px;background:rgba(255,255,255,0.03);color:#444;outline:1px solid rgba(255,255,255,0.07);transition:all 0.2s">LIMIT</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label class="lbl">Quantity</label>
        <input type="number" id="qty" placeholder="e.g. 0.01" step="0.001">
      </div>

      <div id="price-row" style="margin-bottom:14px;display:none">
        <label class="lbl">Limit Price (USDT)</label>
        <input type="number" id="lmt-price" placeholder="e.g. 95000">
      </div>

      <button id="submit-btn" onclick="submitOrder()" style="width:100%;padding:13px 0;border-radius:10px;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px;letter-spacing:1px;background:linear-gradient(135deg,#00c896,#00a87a);color:#fff;box-shadow:0 4px 20px rgba(0,200,150,0.25);transition:all 0.2s">
        ▲ PLACE BUY MARKET ORDER
      </button>

      <div id="order-result" style="display:none;margin-top:12px;padding:12px 14px;border-radius:8px;font-size:11px;line-height:1.8"></div>
    </div>

    <!-- RIGHT COLUMN -->
    <div style="display:flex;flex-direction:column;gap:14px">

      <!-- ACCOUNT -->
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div class="section-title" style="margin:0">ACCOUNT — TESTNET</div>
          <button onclick="loadAccount()" style="background:none;border:none;color:#444;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:10px">↻ refresh</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;color:#555;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">Wallet Balance</div>
            <div id="acct-wallet" class="price-val">—</div>
          </div>
          <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;color:#555;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">Available</div>
            <div id="acct-avail" class="price-val">—</div>
          </div>
          <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;color:#555;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">Unrealized PnL</div>
            <div id="acct-pnl" class="price-val">—</div>
          </div>
          <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;color:#555;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">Margin Balance</div>
            <div id="acct-margin" class="price-val">—</div>
          </div>
        </div>
      </div>

      <!-- OPEN ORDERS -->
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <div class="section-title" style="margin:0">OPEN ORDERS</div>
          <button onclick="loadOpenOrders()" style="background:none;border:none;color:#444;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:10px">↻ refresh</button>
        </div>
        <div id="open-orders">
          <div style="color:#333;font-size:12px;text-align:center;padding:20px 0">loading...</div>
        </div>
      </div>

      <!-- ACTIVITY LOG -->
      <div class="card">
        <div class="section-title">ACTIVITY LOG</div>
        <div id="log" style="background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px 12px;height:130px;overflow-y:auto;font-size:10px;line-height:1.9"></div>
      </div>

    </div>
  </div>
</div>

<script>
const SYMBOLS=[
  {s:'BTCUSDT',color:'#F7931A'},
  {s:'ETHUSDT',color:'#627EEA'},
  {s:'BNBUSDT',color:'#F3BA2F'},
  {s:'SOLUSDT',color:'#9945FF'},
  {s:'XRPUSDT',color:'#00AAE4'},
];
const prices={},histories={},changes={};
SYMBOLS.forEach(({s})=>{prices[s]=null;histories[s]=[];changes[s]=0});

let currentSide='BUY',currentType='MARKET';

function log(msg,type='info'){
  const el=document.getElementById('log');
  const colors={info:'#444',success:'#00c896',error:'#ff5252',warn:'#f59e0b'};
  const t=new Date().toLocaleTimeString();
  el.innerHTML+=`<div style="color:${colors[type]||'#444'}"><span style="color:#2a2a2a;margin-right:8px">${t}</span>${msg}</div>`;
  el.scrollTop=el.scrollHeight;
}

function setSide(s){
  currentSide=s;
  const b=document.getElementById('btn-buy'),sl=document.getElementById('btn-sell');
  if(s==='BUY'){
    b.style.cssText='flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(0,200,150,0.18);color:#00c896;outline:1px solid #00c896;transition:all 0.2s';
    sl.style.cssText='flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(255,255,255,0.04);color:#444;outline:1px solid rgba(255,255,255,0.08);transition:all 0.2s';
  }else{
    sl.style.cssText='flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(255,82,82,0.18);color:#ff5252;outline:1px solid #ff5252;transition:all 0.2s';
    b.style.cssText='flex:1;padding:10px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;letter-spacing:1px;background:rgba(255,255,255,0.04);color:#444;outline:1px solid rgba(255,255,255,0.08);transition:all 0.2s';
  }
  updateSubmitBtn();
}

function setType(t){
  currentType=t;
  const m=document.getElementById('btn-market'),l=document.getElementById('btn-limit');
  const pr=document.getElementById('price-row');
  if(t==='MARKET'){
    m.style.cssText='flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-size:11px;background:rgba(255,255,255,0.1);color:#f0f0f0;outline:1px solid rgba(255,255,255,0.3);transition:all 0.2s';
    l.style.cssText='flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-size:11px;background:rgba(255,255,255,0.03);color:#444;outline:1px solid rgba(255,255,255,0.07);transition:all 0.2s';
    pr.style.display='none';
  }else{
    l.style.cssText='flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-size:11px;background:rgba(255,255,255,0.1);color:#f0f0f0;outline:1px solid rgba(255,255,255,0.3);transition:all 0.2s';
    m.style.cssText='flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;font-family:"JetBrains Mono",monospace;font-size:11px;background:rgba(255,255,255,0.03);color:#444;outline:1px solid rgba(255,255,255,0.07);transition:all 0.2s';
    pr.style.display='block';
  }
  updateSubmitBtn();
}

function updateSubmitBtn(){
  const btn=document.getElementById('submit-btn');
  const arrow=currentSide==='BUY'?'▲':'▼';
  btn.style.background=currentSide==='BUY'?'linear-gradient(135deg,#00c896,#00a87a)':'linear-gradient(135deg,#ff5252,#e03e3e)';
  btn.style.boxShadow=currentSide==='BUY'?'0 4px 20px rgba(0,200,150,0.25)':'0 4px 20px rgba(255,82,82,0.25)';
  btn.textContent=`${arrow} PLACE ${currentSide} ${currentType} ORDER`;
}

async function submitOrder(){
  const sym=document.getElementById('sym').value;
  const qty=document.getElementById('qty').value;
  const lp=document.getElementById('lmt-price').value;
  const res=document.getElementById('order-result');
  if(!qty){showResult('✗ Quantity is required',false);return;}
  if(currentType==='LIMIT'&&!lp){showResult('✗ Price required for LIMIT orders',false);return;}
  const btn=document.getElementById('submit-btn');
  btn.textContent='⏳ Placing...';btn.disabled=true;btn.style.background='rgba(255,255,255,0.05)';btn.style.boxShadow='none';
  const body={symbol:sym,side:currentSide,order_type:currentType,quantity:parseFloat(qty)};
  if(currentType==='LIMIT') body.price=parseFloat(lp);
  try{
    const r=await fetch('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    if(d.success){
      const o=d.order;
      showResult(`✓ Order placed!<br><span style="color:#888">ID: ${o.orderId} · Status: ${o.status} · Qty: ${o.executedQty}</span>`,true);
      log(`${currentSide} ${currentType} ${sym} qty=${qty} → ${o.status}`,'success');
      loadOpenOrders();
    }else{
      showResult('✗ '+d.error,false);
      log('Order failed: '+d.error,'error');
    }
  }catch(e){
    showResult('✗ API error: '+e.message,false);
    log('Request error: '+e.message,'error');
  }
  btn.disabled=false;updateSubmitBtn();
}

function showResult(msg,ok){
  const el=document.getElementById('order-result');
  el.style.display='block';
  el.style.background=ok?'rgba(0,200,150,0.08)':'rgba(255,82,82,0.08)';
  el.style.border='1px solid '+(ok?'rgba(0,200,150,0.3)':'rgba(255,82,82,0.3)');
  el.style.color=ok?'#00c896':'#ff5252';
  el.innerHTML=msg;
}

async function loadAccount(){
  try{
    const r=await fetch('/api/account');
    const d=await r.json();
    if(d.error){log('Account error: '+d.error,'error');return;}
    const fmt=v=>'$'+parseFloat(v||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
    document.getElementById('acct-wallet').textContent=fmt(d.totalWalletBalance);
    document.getElementById('acct-avail').textContent=fmt(d.availableBalance);
    document.getElementById('acct-margin').textContent=fmt(d.totalMarginBalance);
    const pnl=parseFloat(d.totalUnrealizedProfit||0);
    const pnlEl=document.getElementById('acct-pnl');
    pnlEl.textContent=(pnl>=0?'+$':'−$')+Math.abs(pnl).toFixed(2);
    pnlEl.style.color=pnl>=0?'#00c896':'#ff5252';
    log('Account refreshed','info');
  }catch(e){log('Account fetch error: '+e.message,'error')}
}

async function loadOpenOrders(){
  try{
    const r=await fetch('/api/open-orders');
    const d=await r.json();
    const orders=d.orders||[];
    const el=document.getElementById('open-orders');
    if(!orders.length){
      el.innerHTML='<div style="color:#333;font-size:12px;text-align:center;padding:20px 0">no open orders</div>';
    }else{
      el.innerHTML=orders.map(o=>`
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <div style="font-size:11px;line-height:1.7">
            <div style="color:${o.side==='BUY'?'#00c896':'#ff5252'};font-weight:700">${o.side} ${o.symbol.replace('USDT','')}/USDT</div>
            <div style="color:#555">${o.type} · qty ${o.origQty}${parseFloat(o.price||0)>0?' @ $'+parseFloat(o.price).toLocaleString():''}</div>
          </div>
          <button onclick="cancelOrder('${o.symbol}',${o.orderId})" style="background:rgba(255,82,82,0.1);border:1px solid rgba(255,82,82,0.2);border-radius:6px;color:#ff5252;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:10px;padding:4px 10px">cancel</button>
        </div>`).join('');
    }
  }catch(e){log('Open orders error: '+e.message,'error')}
}

async function cancelOrder(symbol,orderId){
  try{
    const r=await fetch('/api/cancel-order',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol,orderId})});
    const d=await r.json();
    if(d.success){log('Cancelled order '+orderId,'warn');loadOpenOrders();}
    else log('Cancel failed: '+d.error,'error');
  }catch(e){log('Cancel error: '+e.message,'error')}
}

async function fetchPrices(){
  for(const {s,color} of SYMBOLS){
    try{
      const r=await fetch('/api/price/'+s);
      const d=await r.json();
      if(d.price){
        const p=parseFloat(d.price);
        prices[s]=p;
        histories[s]=[...histories[s],p].slice(-20);
        if(histories[s].length>1){
          changes[s]=((histories[s][histories[s].length-1]-histories[s][0])/histories[s][0])*100;
        }
      }
    }catch{}
  }
  renderPriceCards();
}

function sparkline(hist,color){
  if(hist.length<2) return '';
  const W=80,H=26,min=Math.min(...hist),max=Math.max(...hist),range=max-min||1;
  const pts=hist.map((v,i)=>`${((i/(hist.length-1))*W).toFixed(1)},${(H-((v-min)/range)*H).toFixed(1)}`).join(' ');
  return `<svg width="${W}" height="${H}"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/></svg>`;
}

function renderPriceCards(){
  const selected=document.getElementById('sym')?.value||'BTCUSDT';
  document.getElementById('price-grid').innerHTML=SYMBOLS.map(({s,color})=>{
    const p=prices[s],c=changes[s]||0,isUp=c>=0;
    const isSel=s===selected;
    const displayPrice=p?'$'+p.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:4}):'loading...';
    return `<button onclick="selectSymbol('${s}')" style="background:${isSel?'rgba(255,255,255,0.07)':'rgba(255,255,255,0.02)'};border:1px solid ${isSel?color+'44':'rgba(255,255,255,0.07)'};border-radius:12px;padding:13px 14px;cursor:pointer;text-align:left;transition:all 0.2s;width:100%;outline:none">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:7px">
        <div>
          <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px">
            <span style="width:7px;height:7px;border-radius:50%;background:${color};display:inline-block;box-shadow:0 0 5px ${color}"></span>
            <span style="font-size:10px;font-weight:600;color:#666;letter-spacing:0.5px">${s.replace('USDT','')}/USDT</span>
          </div>
          <div style="font-size:15px;font-weight:700;color:#f0f0f0">${displayPrice}</div>
        </div>
        <span style="font-size:10px;font-weight:600;color:${isUp?'#00c896':'#ff5252'};background:${isUp?'rgba(0,200,150,0.1)':'rgba(255,82,82,0.1)'};padding:2px 6px;border-radius:5px;white-space:nowrap">${isUp?'▲':'▼'}${Math.abs(c).toFixed(2)}%</span>
      </div>
      ${sparkline(histories[s],color)}
    </button>`;
  }).join('');
}

function selectSymbol(s){
  document.getElementById('sym').value=s;
  updateSubmitBtn();
  renderPriceCards();
}

// Init
log('Dashboard loaded — connected to local API','success');
renderPriceCards();
loadAccount();
loadOpenOrders();
fetchPrices();
setInterval(fetchPrices, 4000);
setInterval(loadOpenOrders, 10000);
setInterval(loadAccount, 30000);
</script>
</body>
</html>
"""


# ── Health check ─────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "testnet": BASE_URL, "time": datetime.utcnow().isoformat()})


# ── Account info ──────────────────────────────────────────────────────────────
@app.route("/api/account", methods=["GET"])
def account():
    try:
        client = get_client()
        data = client.get_account_info()
        # Return only useful fields
        assets = [
            a for a in data.get("assets", [])
            if float(a.get("walletBalance", 0)) > 0
        ]
        return jsonify({
            "totalWalletBalance": data.get("totalWalletBalance"),
            "totalUnrealizedProfit": data.get("totalUnrealizedProfit"),
            "totalMarginBalance": data.get("totalMarginBalance"),
            "availableBalance": data.get("availableBalance"),
            "assets": assets,
        })
    except RuntimeError as e:
        logger.error("Account fetch failed: %s", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Unexpected error in /api/account")
        return jsonify({"error": str(e)}), 500


# ── Place order ───────────────────────────────────────────────────────────────
@app.route("/api/order", methods=["POST"])
def order():
    body = request.get_json(force=True) or {}

    symbol    = body.get("symbol", "")
    side      = body.get("side", "")
    order_type = body.get("order_type", "")
    quantity  = str(body.get("quantity", ""))
    price     = str(body.get("price")) if body.get("price") else None

    logger.info("API order request: %s", body)

    # Validate
    try:
        validated = validate_order_inputs(symbol, side, order_type, quantity, price)
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        return jsonify({"error": str(e)}), 422

    # Execute
    try:
        client = get_client()
        response = place_order(
            client=client,
            symbol=validated["symbol"],
            side=validated["side"],
            order_type=validated["order_type"],
            quantity=validated["quantity"],
            price=validated.get("price"),
        )
        return jsonify({"success": True, "order": response})
    except RuntimeError as e:
        logger.error("Order placement failed: %s", e)
        return jsonify({"error": str(e)}), 400
    except (ConnectionError, TimeoutError) as e:
        logger.error("Network error: %s", e)
        return jsonify({"error": f"Network error: {e}"}), 503
    except Exception as e:
        logger.exception("Unexpected error in /api/order")
        return jsonify({"error": str(e)}), 500


# ── Open orders ───────────────────────────────────────────────────────────────
@app.route("/api/open-orders", methods=["GET"])
def open_orders():
    symbol = request.args.get("symbol", "")
    try:
        client = get_client()
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        data = client._request("GET", "/fapi/v1/openOrders", params)
        return jsonify({"orders": data if isinstance(data, list) else []})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error fetching open orders")
        return jsonify({"error": str(e)}), 500


# ── Cancel order ──────────────────────────────────────────────────────────────
@app.route("/api/cancel-order", methods=["DELETE"])
def cancel_order():
    body = request.get_json(force=True) or {}
    symbol   = body.get("symbol", "").upper()
    order_id = body.get("orderId")
    if not symbol or not order_id:
        return jsonify({"error": "symbol and orderId are required"}), 422
    try:
        client = get_client()
        data = client._request("DELETE", "/fapi/v1/order", {
            "symbol": symbol,
            "orderId": order_id,
        })
        return jsonify({"success": True, "order": data})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error cancelling order")
        return jsonify({"error": str(e)}), 500


# ── Price ticker ──────────────────────────────────────────────────────────────
@app.route("/api/price/<symbol>", methods=["GET"])
def price(symbol):
    try:
        client = get_client()
        # No auth needed for public ticker but we reuse the session
        import requests as req
        r = req.get(
            f"{BASE_URL}/fapi/v1/ticker/price",
            params={"symbol": symbol.upper()},
            timeout=5
        )
        data = r.json()
        if "code" in data:
            return jsonify({"error": data.get("msg")}), 400
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n  🚀  Trading Bot API running at http://localhost:5050")
    print("  📡  Testnet:", BASE_URL)
    print("  Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5050, debug=True)