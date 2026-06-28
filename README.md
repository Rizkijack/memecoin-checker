# 🔍 Memecoin Checker

**Multi-platform memecoin analysis aggregator** — cek token dari berbagai sumber dalam satu dashboard.

![Screenshot](https://img.shields.io/badge/status-live-brightgreen)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ✨ Fitur

| Fitur | Sumber Data |
|-------|------------|
| 📊 **Market Data** (MC, Price, Volume, Liquidity) | DexScreener API |
| 🛡️ **Security Score** & Risk Report | RugCheck.xyz |
| 🔍 **On-Chain Analysis** (holders, snipers, whales) | GMGN-style simulation |
| 📈 **Top Trading Pairs** per chain | DexScreener |
| 🔗 **Quick Links** to DexScreener, RugCheck, Birdeye, Solscan | Auto-generated |

## 🚀 Cara Menjalankan

### Prerequisites

- Python 3.10+
- pip

### 1. Clone & Install

```bash
cd memecoin-checker
pip install -r backend/requirements.txt
```

### 2. Jalankan Server

```bash
python backend/main.py
```

Atau via uvicorn langsung:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Buka Browser

➡️ **http://localhost:8000**

### 🐳 Deploy ke Production

**Heroku / Railway / Render:**

```bash
# Build command
pip install -r backend/requirements.txt

# Start command
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Docker:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ .
COPY frontend/ ../frontend/
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze?q=<token>` | GET | Full token analysis (DexScreener + RugCheck + OnChain) |
| `/api/onchain?address=<addr>` | GET | Detailed on-chain analysis only |
| `/api/trending` | GET | Latest trending token profiles |
| `/api/health` | GET | Health check |
| `/docs` | GET | Swagger API documentation |

### Example

```bash
curl "http://localhost:8000/api/analyze?q=bonk"
```

## 📁 Project Structure

```
memecoin-checker/
├── backend/
│   ├── main.py              # FastAPI server entry point
│   ├── api_providers.py     # API integration layer (DexScreener, RugCheck)
│   ├── onchain_analysis.py  # GMGN-style on-chain analysis module
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main page
│   ├── style.css            # Dark theme styles
│   └── app.js               # Frontend app logic
├── start.sh                 # Quick start script
└── README.md                # This file
```

## 🧠 Data Sources

- **[DexScreener](https://dexscreener.com)** — Public API for token pairs, pricing, volume, liquidity
- **[RugCheck.xyz](https://rugcheck.xyz)** — Token security scoring and risk assessment (Solana)
- **On-Chain Analysis** — Simulated GMGN-style holder distribution, sniper/whale detection, LP analysis

> ⚠️ **Disclaimer:** Beberapa analisis on-chain bersifat simulasi berdasarkan data yang tersedia dari DexScreener. Selalu lakukan verifikasi manual (DYOR) sebelum mengambil keputusan trading.

## 🛡️ Safety Features

- CLMM/DLMM pair filtering untuk mencegah market cap inflation
- Multi-platform cross-reference (cek data dari 3+ sumber)
- Risk scoring yang disesuaikan untuk token established vs baru
- External links untuk verifikasi manual

## 📝 License

MIT — Use freely, contribute back if you can.

---

**Built with ❤️ by Hermes Agent**
