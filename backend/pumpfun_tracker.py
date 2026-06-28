"""
pump.fun New Token Tracker
Memantau token baru yang lahir di pump.fun (Solana).
Lacak bonding curve, market cap milestone, dan early entry opportunities.

pump.fun API (frontend-api.pump.fun) bersifat private.
Module ini menggunakan data DexScreener yang mencakup pump.fun pairs.
"""
import random
import math
from datetime import datetime, timedelta


def pumpfun_detect_new_tokens(pairs: list) -> dict:
    """
    Deteksi token dari pump.fun / pump swap.
    Analisis bonding curve progress dan early signals.
    """
    # Filter pump.fun pairs
    pump_pairs = [
        p for p in pairs 
        if p.get("dexId", "") in ("pumpfun", "pumpswap")
    ]
    
    if not pump_pairs:
        return {
            "platform": "pump.fun Tracker",
            "found": False,
            "message": "No pump.fun pairs detected for this token",
        }

    pair = pump_pairs[0]
    base = pair.get("baseToken", {})
    
    # Bonding curve info dari data
    mc = pair.get("marketCap", 0) or 0
    liq = pair.get("liquidity", {}).get("usd", 0) or 0 if pair.get("liquidity") else 0
    created_at = pair.get("pairCreatedAt", 0)
    age_hours = (datetime.now() - datetime.fromtimestamp(created_at / 1000)).total_seconds() / 3600 if created_at else 0
    vol_h24 = pair.get("volume", {}).get("h24", 0) or 0

    # Bonding curve stage detection
    if mc < 69000:
        curve_stage = "Bonding Curve (Early)"
        progress_pct = min(100, round((mc / 69000) * 100, 1))
    elif mc < 100000:
        curve_stage = "Bonding Curve (Graduating)"
        progress_pct = min(100, round((mc / 69000) * 100, 1))
    else:
        curve_stage = "Raydium Migration ✅"
        progress_pct = 100

    # Token age assessment
    if age_hours < 1:
        age_label = "Brand New 🔥"
    elif age_hours < 6:
        age_label = "Very Recent ⏰"
    elif age_hours < 24:
        age_label = "Today's Launch 📅"
    elif age_hours < 72:
        age_label = "Recent 🕐"
    else:
        age_label = "Established 📊"

    # Buy pressure analysis
    txns = pair.get("txns", {})
    h24_txns = txns.get("h24", {}) or {}
    h1_txns = txns.get("h1", {}) or {}
    buys_h24 = h24_txns.get("buys", 0)
    sells_h24 = h24_txns.get("sells", 0)
    buys_h1 = h1_txns.get("buys", 0)
    sells_h1 = h1_txns.get("sells", 0)
    
    buy_pressure_24h = buys_h24 / max(sells_h24, 1)
    buy_pressure_1h = buys_h1 / max(sells_h1, 1)

    # Price change
    px_change = pair.get("priceChange", {}) or {}
    
    return {
        "platform": "pump.fun Tracker",
        "found": True,
        "tokenAddress": base.get("address", ""),
        "tokenName": base.get("name", ""),
        "tokenSymbol": base.get("symbol", ""),
        "bondingCurve": {
            "stage": curve_stage,
            "progressPct": progress_pct,
            "currentMc": mc,
            "liqUsd": liq,
            "liqForMigration": 12000,
        },
        "age": {
            "hoursSinceLaunch": round(age_hours, 1),
            "label": age_label,
        },
        "buyPressure": {
            "h1": round(buy_pressure_1h, 2),
            "h24": round(buy_pressure_24h, 2),
            "status": "BULLISH 💚" if buy_pressure_1h > 1.5 else "NEUTRAL ⚪" if buy_pressure_1h > 0.5 else "BEARISH ❤️",
        },
        "priceChange": {
            "m5": px_change.get("m5", 0),
            "h1": px_change.get("h1", 0),
            "h6": px_change.get("h6", 0),
            "h24": px_change.get("h24", 0),
        },
        "volume24h": vol_h24,
        "createdAt": datetime.fromtimestamp(created_at / 1000).isoformat() if created_at else None,
        "pumpLink": f"https://pump.fun/coin/{base.get('address', '')}" if base.get("address") else None,
    }


def pumpfun_trending_tokens(profiles: list) -> list:
    """
    Filter trending new tokens from latest profiles.
    Identifikasi token pump.fun yang baru trending.
    """
    trending = []
    for p in profiles[:50]:
        url = p.get("url", "")
        chain = p.get("chainId", "")
        if "pump" in url.lower() or "pumpfun" in chain:
            trending.append({
                "url": url,
                "chainId": chain,
                "tokenAddress": p.get("tokenAddress", ""),
                "description": p.get("description", "")[:100] if p.get("description") else "",
            })
    return trending[:10]
