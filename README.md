# ⚡ Trading Bot — Binance Futures Testnet

A Python trading bot with a **live web dashboard** for placing and managing orders on Binance Futures Testnet (USDT-M).

> ⚠️ **Testnet only** — uses `https://testnet.binancefuture.com`. No real money is involved.

---

## Features

- Place **Market** and **Limit** orders via CLI or web UI
- Support for both **BUY** and **SELL** sides
- **Live web dashboard** at `http://localhost:5050` with:
  - Real-time price tickers (auto-refresh every 4s)
  - Account balance & PnL display
  - Open orders list with one-click cancel
  - Activity log
- Structured logging to `logs/trading_bot.log`
- Full input validation and error handling
- Clean layered architecture (CLI / API / logic / client)

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # package exports
│   ├── client.py            # Binance REST client + signing
│   ├── orders.py            # order construction & placement
│   ├── validators.py        # input validation
│   └── logging_config.py   # rotating file + console logger
├── cli.py                   # CLI entry point (argparse)
├── app.py                   # Flask API + web dashboard
├── logs/                    # auto-created, log files go here
├── .env.example             # copy this to .env and add your keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet API Keys

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register / log in
3. Navigate to **API Management** → **Create API Key**
4. Copy your **API Key** and **Secret Key**

### 2. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/trading-bot.git
cd trading-bot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> Your `.env` file is listed in `.gitignore` and will **never** be committed.

---

## Usage

### Option A — Web Dashboard (recommended)

```bash
python app.py
```

Open **[http://localhost:5050](http://localhost:5050)** in your browser.

You'll see a live dashboard where you can place orders, view your balance, and manage open orders — all with real testnet data.

---

### Option B — CLI

```bash
# Market order
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Limit order
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3000
```

#### All CLI arguments

| Argument     | Required        | Description                          |
|-------------|-----------------|--------------------------------------|
| `--symbol`  | Yes             | Trading pair e.g. `BTCUSDT`          |
| `--side`    | Yes             | `BUY` or `SELL`                      |
| `--type`    | Yes             | `MARKET` or `LIMIT`                  |
| `--quantity`| Yes             | Order quantity                       |
| `--price`   | LIMIT only      | Limit price in USDT                  |

#### Supported symbols
`BTCUSDT` · `ETHUSDT` · `BNBUSDT` · `SOLUSDT` · `XRPUSDT`

---

## API Endpoints

The Flask server exposes these endpoints (used by the dashboard):

| Method   | Endpoint                  | Description              |
|----------|---------------------------|--------------------------|
| `GET`    | `/`                       | Web dashboard UI         |
| `GET`    | `/api/health`             | Server + testnet status  |
| `GET`    | `/api/account`            | Wallet balance & PnL     |
| `POST`   | `/api/order`              | Place an order           |
| `GET`    | `/api/open-orders`        | List open orders         |
| `DELETE` | `/api/cancel-order`       | Cancel an open order     |
| `GET`    | `/api/price/<symbol>`     | Live price ticker        |

---

## Logging

All activity is logged to `logs/trading_bot.log`:

```
2026-05-09 22:58:01 | INFO     | Placing BUY MARKET order | symbol=BTCUSDT qty=0.01
2026-05-09 22:58:01 | INFO     | Order placed | orderId=123456 status=FILLED executedQty=0.01
```

- Rotating file handler: keeps last **5 files × 2 MB**
- Console shows INFO and above
- File logs everything including DEBUG (request/response details)

---

## Security

- API keys are loaded from `.env` — **never hardcoded**
- `.env` is in `.gitignore` — **never committed**
- `.env.example` is committed as a safe template
- This bot only connects to the **testnet** — no real funds at risk

---

## Requirements

- Python 3.9+
- Binance Futures Testnet account

```
requests
python-dotenv
flask
flask-cors
```

---

## Assumptions

- Testnet only — base URL is hardcoded to `https://testnet.binancefuture.com`
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled)
- Valid symbols are limited to the 5 most common pairs
- Python 3.9+ required (`from __future__ import annotations` used for compatibility)

---

## Project Demo Video

[![Watch the video](https://img.youtube.com/vi/YlF_4pzqonQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=YlF_4pzqonQ)

## License

No Restrictions — free to use, modify, and distribute.
