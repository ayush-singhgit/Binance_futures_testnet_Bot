import { useState, useEffect, useCallback, useRef } from "react";

const API = "http://localhost:5050/api";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"];

const SYMBOL_COLORS = {
  BTCUSDT: "#F7931A",
  ETHUSDT: "#627EEA",
  BNBUSDT: "#F3BA2F",
  SOLUSDT: "#9945FF",
  XRPUSDT: "#00AAE4",
};

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

function useInterval(cb, delay) {
  const ref = useRef(cb);
  useEffect(() => { ref.current = cb; }, [cb]);
  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => ref.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}

// ── Sparkline ────────────────────────────────────────────────────────────────
function Sparkline({ data, color }) {
  if (!data || data.length < 2) return null;
  const w = 80, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.8" />
    </svg>
  );
}

// ── Price Card ───────────────────────────────────────────────────────────────
function PriceCard({ symbol, selected, onClick }) {
  const [price, setPrice] = useState(null);
  const [history, setHistory] = useState([]);
  const [change, setChange] = useState(0);
  const color = SYMBOL_COLORS[symbol] || "#00ff88";

  const fetchPrice = useCallback(async () => {
    try {
      const r = await fetch(`${API}/price/${symbol}`);
      const d = await r.json();
      if (d.price) {
        const p = parseFloat(d.price);
        setPrice(p);
        setHistory(prev => {
          const next = [...prev, p].slice(-20);
          if (next.length > 1) setChange(((next[next.length-1] - next[0]) / next[0]) * 100);
          return next;
        });
      }
    } catch {}
  }, [symbol]);

  useEffect(() => { fetchPrice(); }, [fetchPrice]);
  useInterval(fetchPrice, 4000);

  const isUp = change >= 0;

  return (
    <button
      onClick={onClick}
      style={{
        background: selected ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.03)",
        border: selected ? `1px solid ${color}55` : "1px solid rgba(255,255,255,0.08)",
        borderRadius: 12,
        padding: "14px 16px",
        cursor: "pointer",
        textAlign: "left",
        transition: "all 0.2s",
        outline: "none",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, display: "inline-block", boxShadow: `0 0 6px ${color}` }} />
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, color: "#aaa", letterSpacing: 1 }}>{symbol.replace("USDT", "")}/USDT</span>
          </div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 18, fontWeight: 700, color: "#f0f0f0" }}>
            {price ? `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}` : "—"}
          </div>
        </div>
        <span style={{
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          color: isUp ? "#00c896" : "#ff5252",
          background: isUp ? "rgba(0,200,150,0.1)" : "rgba(255,82,82,0.1)",
          padding: "2px 7px",
          borderRadius: 6,
        }}>
          {isUp ? "▲" : "▼"} {Math.abs(change).toFixed(2)}%
        </span>
      </div>
      <Sparkline data={history} color={color} />
    </button>
  );
}

// ── Order Form ───────────────────────────────────────────────────────────────
function OrderForm({ defaultSymbol, onOrderPlaced }) {
  const [symbol, setSymbol] = useState(defaultSymbol || "BTCUSDT");
  const [side, setSide] = useState("BUY");
  const [orderType, setOrderType] = useState("MARKET");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => { setSymbol(defaultSymbol); }, [defaultSymbol]);

  const submit = async () => {
    if (!quantity) { setResult({ error: "Quantity is required" }); return; }
    if (orderType === "LIMIT" && !price) { setResult({ error: "Price required for LIMIT orders" }); return; }
    setLoading(true);
    setResult(null);
    try {
      const body = { symbol, side, order_type: orderType, quantity: parseFloat(quantity) };
      if (orderType === "LIMIT") body.price = parseFloat(price);
      const r = await fetch(`${API}/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const d = await r.json();
      setResult(d);
      if (d.success && onOrderPlaced) onOrderPlaced(d.order);
    } catch (e) {
      setResult({ error: `Network error: ${e.message}` });
    } finally {
      setLoading(false);
    }
  };

  const accent = side === "BUY" ? "#00c896" : "#ff5252";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Symbol */}
      <div>
        <label style={labelStyle}>Symbol</label>
        <select value={symbol} onChange={e => setSymbol(e.target.value)} style={selectStyle}>
          {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Side toggle */}
      <div>
        <label style={labelStyle}>Side</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["BUY", "SELL"].map(s => (
            <button
              key={s}
              onClick={() => setSide(s)}
              style={{
                flex: 1, padding: "10px 0", borderRadius: 8, border: "none", cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: 13,
                letterSpacing: 1,
                transition: "all 0.2s",
                background: side === s
                  ? (s === "BUY" ? "rgba(0,200,150,0.2)" : "rgba(255,82,82,0.2)")
                  : "rgba(255,255,255,0.05)",
                color: side === s ? (s === "BUY" ? "#00c896" : "#ff5252") : "#666",
                outline: side === s ? `1px solid ${s === "BUY" ? "#00c896" : "#ff5252"}` : "1px solid rgba(255,255,255,0.1)",
              }}
            >{s}</button>
          ))}
        </div>
      </div>

      {/* Order type */}
      <div>
        <label style={labelStyle}>Order Type</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["MARKET", "LIMIT"].map(t => (
            <button
              key={t}
              onClick={() => setOrderType(t)}
              style={{
                flex: 1, padding: "10px 0", borderRadius: 8, border: "none", cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: 12,
                letterSpacing: 0.5,
                transition: "all 0.2s",
                background: orderType === t ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.03)",
                color: orderType === t ? "#f0f0f0" : "#555",
                outline: orderType === t ? "1px solid rgba(255,255,255,0.3)" : "1px solid rgba(255,255,255,0.07)",
              }}
            >{t}</button>
          ))}
        </div>
      </div>

      {/* Quantity */}
      <div>
        <label style={labelStyle}>Quantity</label>
        <input
          type="number"
          value={quantity}
          onChange={e => setQuantity(e.target.value)}
          placeholder="e.g. 0.01"
          step="0.001"
          style={inputStyle}
        />
      </div>

      {/* Price (LIMIT only) */}
      {orderType === "LIMIT" && (
        <div>
          <label style={labelStyle}>Limit Price (USDT)</label>
          <input
            type="number"
            value={price}
            onChange={e => setPrice(e.target.value)}
            placeholder="e.g. 95000"
            style={inputStyle}
          />
        </div>
      )}

      {/* Submit */}
      <button
        onClick={submit}
        disabled={loading}
        style={{
          padding: "14px 0",
          borderRadius: 10,
          border: "none",
          cursor: loading ? "not-allowed" : "pointer",
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: 1,
          background: loading ? "rgba(255,255,255,0.05)"
            : side === "BUY"
              ? "linear-gradient(135deg, #00c896, #00a87a)"
              : "linear-gradient(135deg, #ff5252, #e03e3e)",
          color: loading ? "#555" : "#fff",
          transition: "all 0.2s",
          boxShadow: loading ? "none" : side === "BUY"
            ? "0 4px 20px rgba(0,200,150,0.25)"
            : "0 4px 20px rgba(255,82,82,0.25)",
        }}
      >
        {loading ? "⏳ Placing..." : `${side === "BUY" ? "▲" : "▼"} Place ${side} ${orderType}`}
      </button>

      {/* Result */}
      {result && (
        <div style={{
          padding: "12px 14px",
          borderRadius: 8,
          background: result.error ? "rgba(255,82,82,0.08)" : "rgba(0,200,150,0.08)",
          border: `1px solid ${result.error ? "rgba(255,82,82,0.3)" : "rgba(0,200,150,0.3)"}`,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11,
        }}>
          {result.error ? (
            <div style={{ color: "#ff5252" }}>✗ {result.error}</div>
          ) : (
            <div style={{ color: "#00c896" }}>
              <div>✓ Order placed successfully</div>
              <div style={{ marginTop: 6, color: "#aaa", lineHeight: 1.7 }}>
                <div>ID: {result.order?.orderId}</div>
                <div>Status: {result.order?.status}</div>
                <div>Executed: {result.order?.executedQty} {result.order?.symbol?.replace("USDT","")}</div>
                {result.order?.avgPrice && parseFloat(result.order.avgPrice) > 0 && (
                  <div>Avg Price: ${parseFloat(result.order.avgPrice).toLocaleString()}</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Open Orders Table ─────────────────────────────────────────────────────────
function OpenOrders({ refresh }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/open-orders`);
      const d = await r.json();
      setOrders(d.orders || []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { fetch_(); }, [fetch_, refresh]);
  useInterval(fetch_, 8000);

  const cancel = async (symbol, orderId) => {
    setCancelling(orderId);
    try {
      await fetch(`${API}/cancel-order`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, orderId }),
      });
      fetch_();
    } catch {}
    setCancelling(null);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <span style={{ ...labelStyle, fontSize: 11, margin: 0 }}>OPEN ORDERS {orders.length > 0 && `(${orders.length})`}</span>
        <button onClick={fetch_} style={{ background: "none", border: "none", color: "#555", cursor: "pointer", fontFamily: "'JetBrains Mono', monospace", fontSize: 10 }}>
          {loading ? "syncing..." : "↻ refresh"}
        </button>
      </div>
      {orders.length === 0 ? (
        <div style={{ color: "#444", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, textAlign: "center", padding: "24px 0" }}>
          no open orders
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {orders.map(o => (
            <div key={o.orderId} style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
              borderRadius: 8,
              padding: "10px 12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, lineHeight: 1.7 }}>
                <div style={{ color: o.side === "BUY" ? "#00c896" : "#ff5252", fontWeight: 700 }}>
                  {o.side} {o.symbol?.replace("USDT","")}/USDT
                </div>
                <div style={{ color: "#666" }}>
                  {o.type} · qty {o.origQty}
                  {o.price && parseFloat(o.price) > 0 && ` @ $${parseFloat(o.price).toLocaleString()}`}
                </div>
              </div>
              <button
                onClick={() => cancel(o.symbol, o.orderId)}
                disabled={cancelling === o.orderId}
                style={{
                  background: "rgba(255,82,82,0.1)",
                  border: "1px solid rgba(255,82,82,0.2)",
                  borderRadius: 6,
                  color: "#ff5252",
                  cursor: "pointer",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  padding: "4px 10px",
                  transition: "all 0.15s",
                }}
              >
                {cancelling === o.orderId ? "..." : "cancel"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Account Panel ─────────────────────────────────────────────────────────────
function AccountPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`${API}/account`);
      const d = await r.json();
      if (d.error) setErr(d.error);
      else { setData(d); setErr(null); }
    } catch (e) {
      setErr("Cannot reach API server — is app.py running?");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);
  useInterval(fetch_, 15000);

  if (loading) return <div style={{ color: "#444", fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>loading account...</div>;
  if (err) return (
    <div style={{ color: "#ff5252", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, lineHeight: 1.7 }}>
      <div>⚠ {err}</div>
      <div style={{ marginTop: 8, color: "#555" }}>Start the backend: python app.py</div>
    </div>
  );

  const bal = parseFloat(data?.totalWalletBalance || 0);
  const pnl = parseFloat(data?.totalUnrealizedProfit || 0);
  const avail = parseFloat(data?.availableBalance || 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {[
          { label: "Wallet Balance", value: `$${bal.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, color: "#f0f0f0" },
          { label: "Available", value: `$${avail.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, color: "#f0f0f0" },
          { label: "Unrealized PnL", value: `${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)}`, color: pnl >= 0 ? "#00c896" : "#ff5252" },
          { label: "Margin Balance", value: `$${parseFloat(data?.totalMarginBalance || 0).toFixed(2)}`, color: "#f0f0f0" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, padding: "10px 12px" }}>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: "#555", marginBottom: 4, letterSpacing: 1, textTransform: "uppercase" }}>{label}</div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, fontWeight: 700, color }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Log Viewer ────────────────────────────────────────────────────────────────
function LogFeed({ entries }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [entries]);

  return (
    <div ref={ref} style={{
      background: "rgba(0,0,0,0.4)",
      border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: 8,
      padding: "10px 12px",
      height: 140,
      overflowY: "auto",
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 10,
      lineHeight: 1.8,
    }}>
      {entries.length === 0 ? (
        <span style={{ color: "#333" }}>awaiting activity...</span>
      ) : entries.map((e, i) => (
        <div key={i} style={{ color: e.type === "error" ? "#ff5252" : e.type === "success" ? "#00c896" : "#555" }}>
          <span style={{ color: "#333", marginRight: 8 }}>{e.time}</span>
          {e.msg}
        </div>
      ))}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const labelStyle = {
  display: "block",
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 9,
  fontWeight: 600,
  color: "#555",
  letterSpacing: 1.5,
  textTransform: "uppercase",
  marginBottom: 6,
};
const inputStyle = {
  width: "100%",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  padding: "10px 12px",
  color: "#f0f0f0",
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
  transition: "border-color 0.15s",
};
const selectStyle = {
  ...inputStyle,
  cursor: "pointer",
  appearance: "none",
  WebkitAppearance: "none",
};

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function TradingDashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [orderRefresh, setOrderRefresh] = useState(0);
  const [logs, setLogs] = useState([
    { time: new Date().toLocaleTimeString(), msg: "Dashboard initialised — testnet mode", type: "info" }
  ]);
  const [apiStatus, setApiStatus] = useState("checking");

  const addLog = (msg, type = "info") => {
    setLogs(prev => [...prev.slice(-49), {
      time: new Date().toLocaleTimeString(),
      msg, type
    }]);
  };

  // Check API health
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API}/health`);
        const d = await r.json();
        if (d.status === "ok") {
          setApiStatus("online");
          addLog("API server connected ✓", "success");
        }
      } catch {
        setApiStatus("offline");
        addLog("API server offline — run: python app.py", "error");
      }
    };
    check();
  }, []);

  useInterval(async () => {
    try {
      const r = await fetch(`${API}/health`);
      const d = await r.json();
      setApiStatus(d.status === "ok" ? "online" : "offline");
    } catch {
      setApiStatus("offline");
    }
  }, 10000);

  const handleOrderPlaced = (order) => {
    setOrderRefresh(v => v + 1);
    addLog(`Order ${order?.orderId} — ${order?.side} ${order?.origQty} ${order?.symbol} @ ${order?.status}`, "success");
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      color: "#f0f0f0",
      padding: "0 0 40px 0",
      fontFamily: "'JetBrains Mono', monospace",
    }}>
      {/* Top bar */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 24px",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        background: "rgba(0,0,0,0.5)",
        backdropFilter: "blur(10px)",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: "linear-gradient(135deg, #00c896, #006650)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16, fontWeight: 900, color: "#fff",
          }}>⚡</div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: 1, color: "#f0f0f0" }}>TRADING BOT</div>
            <div style={{ fontSize: 9, color: "#444", letterSpacing: 2 }}>BINANCE FUTURES TESTNET</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%",
            background: apiStatus === "online" ? "#00c896" : apiStatus === "offline" ? "#ff5252" : "#f59e0b",
            display: "inline-block",
            boxShadow: apiStatus === "online" ? "0 0 8px #00c896" : "none",
          }} />
          <span style={{ fontSize: 10, color: "#555", letterSpacing: 1 }}>
            {apiStatus === "online" ? "API LIVE" : apiStatus === "offline" ? "API OFFLINE" : "CHECKING"}
          </span>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 20px" }}>

        {/* Offline banner */}
        {apiStatus === "offline" && (
          <div style={{
            background: "rgba(255,82,82,0.08)",
            border: "1px solid rgba(255,82,82,0.2)",
            borderRadius: 10,
            padding: "12px 16px",
            marginBottom: 20,
            fontSize: 12,
            color: "#ff8080",
            lineHeight: 1.7,
          }}>
            <strong>Backend not running.</strong> Start it with:
            <code style={{ display: "block", marginTop: 6, color: "#aaa", background: "rgba(0,0,0,0.3)", padding: "6px 10px", borderRadius: 6 }}>
              pip install flask flask-cors &amp;&amp; python app.py
            </code>
          </div>
        )}

        {/* Prices row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginBottom: 24 }}>
          {SYMBOLS.map(s => (
            <PriceCard
              key={s}
              symbol={s}
              selected={selectedSymbol === s}
              onClick={() => setSelectedSymbol(s)}
            />
          ))}
        </div>

        {/* Main grid */}
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16 }}>

          {/* Left: Order form */}
          <div style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 14,
            padding: "20px",
          }}>
            <div style={{ fontSize: 10, color: "#444", letterSpacing: 2, marginBottom: 16 }}>PLACE ORDER</div>
            <OrderForm defaultSymbol={selectedSymbol} onOrderPlaced={handleOrderPlaced} />
          </div>

          {/* Right: account + orders + log */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Account */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 14,
              padding: "20px",
            }}>
              <div style={{ fontSize: 10, color: "#444", letterSpacing: 2, marginBottom: 14 }}>ACCOUNT — TESTNET</div>
              <AccountPanel />
            </div>

            {/* Open orders */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 14,
              padding: "20px",
            }}>
              <OpenOrders refresh={orderRefresh} />
            </div>

            {/* Activity log */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 14,
              padding: "20px",
            }}>
              <div style={{ fontSize: 10, color: "#444", letterSpacing: 2, marginBottom: 10 }}>ACTIVITY LOG</div>
              <LogFeed entries={logs} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
