"""
API Providers for Memecoin Checker
Integrasi dengan: DexScreener, RugCheck.xyz, GMGN-style on-chain, dan lain-lain
"""
import httpx
import asyncio
from typing import Optional
from onchain_analysis import full_onchain_analysis
from gmgn_analysis import gmgn_full_analysis
from pumpfun_tracker import pumpfun_detect_new_tokens
from sharpeai_analysis import sharpeai_full_analysis
from tokensniffer_analysis import tokensniffer_full_analysis

DEXSCREENER_BASE = "https://api.dexscreener.com"
RUGCHECK_BASE = "https://api.rugcheck.xyz"

# ─── DexScreener ────────────────────────────────────────────────

async def dexscreener_search_token(query: str) -> dict:
    """Search token by name/symbol on DexScreener."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DEXSCREENER_BASE}/latest/dex/search", params={"q": query})
        resp.raise_for_status()
        return resp.json()


async def dexscreener_token_pairs(token_address: str) -> dict:
    """Get all pairs for a token address on DexScreener."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DEXSCREENER_BASE}/latest/dex/tokens/{token_address}")
        resp.raise_for_status()
        return resp.json()


async def dexscreener_latest_profiles() -> dict:
    """Get latest token profiles."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DEXSCREENER_BASE}/token-profiles/latest/v1")
        resp.raise_for_status()
        return resp.json()


# ─── RugCheck.xyz ──────────────────────────────────────────────

async def rugcheck_report(token_mint: str) -> Optional[dict]:
    """Get full RugCheck report for a Solana token."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{RUGCHECK_BASE}/v1/tokens/{token_mint}/report")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def rugcheck_summary(token_mint: str) -> Optional[dict]:
    """Get RugCheck risk summary for a Solana token."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{RUGCHECK_BASE}/v1/tokens/{token_mint}/report/summary")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def rugcheck_metadata(token_mint: str) -> Optional[dict]:
    """Get RugCheck token metadata."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{RUGCHECK_BASE}/v1/tokens/{token_mint}/metadata")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


# ─── Aggregator ─────────────────────────────────────────────────

async def analyze_token(query: str) -> dict:
    """
    Full memecoin analysis aggregator.
    Menggabungkan DexScreener + RugCheck + metadata.
    """
    result = {
        "query": query,
        "dexScreener": None,
        "rugCheck": None,
        "summary": None
    }
    token_addr = ""

    # 1. Cari di DexScreener
    dex_data = await dexscreener_search_token(query)
    pairs = dex_data.get("pairs", [])

    # Sort by liquidity (highest first), but prefer standard DEX pairs over CLMM
    # CLMM (Concentrated Liquidity) pairs often show inflated market cap
    def pair_score(p):
        liq = p.get("liquidity", {}).get("usd", 0) if p.get("liquidity") else 0
        mc = p.get("marketCap", 0) or 0
        labels = p.get("labels", [])
        dex = p.get("dexId", "")
        chain = p.get("chainId", "")
        labels_str = str(labels).lower() if labels else ""

        # Penalize CLMM/DLMM/DYN pairs — inflated market caps
        is_clmm = any(l in labels_str for l in ["clmm", "dlmm", "dyn", "concentrated"])
        if is_clmm:
            liq *= 0.05  # heavy discount

        # Boost standard DEX pairs
        if dex in ("raydium", "orca", "pumpfun", "pumpswap", "uniswap") and not is_clmm:
            liq *= 2.0

        # Prefer non-CLMM by heavily penalizing CLMM MC
        if is_clmm and mc > 1_000_000_000_000:  # trillions = clearly inflated
            liq = 0  # kill these

        # Prefer well-known Solana DEXes for Solana tokens
        if chain == "solana" and dex in ("raydium", "orca") and not is_clmm:
            liq *= 3.0

        return liq

    pairs.sort(key=pair_score, reverse=True)

    result["dexScreener"] = {
        "totalPairs": len(pairs),
        "topPairs": pairs[:10] if pairs else [],
    }

    # 2. Ambil token address Solana pertama untuk RugCheck
    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    if solana_pairs:
        token_addr = solana_pairs[0].get("baseToken", {}).get("address", "")
        if token_addr:
            rug_summary = await rugcheck_summary(token_addr)
            rug_report = await rugcheck_report(token_addr)
            rug_meta = await rugcheck_metadata(token_addr)
            result["rugCheck"] = {
                "summary": rug_summary,
                "report": rug_report,
                "metadata": rug_meta,
            }

    # 2b. On-chain analysis (GMGN-style) — fallback for token_addr
    if not token_addr:
        for p in pairs:
            addr = p.get("baseToken", {}).get("address", "")
            if addr:
                token_addr = addr
                break

    if token_addr:
        result["onchain"] = full_onchain_analysis(token_addr, pairs)

    # 3a. GMGN Enhanced Analysis
    if token_addr:
        symbol = pairs[0].get("baseToken", {}).get("symbol", query) if pairs else query
        result["gmgn"] = gmgn_full_analysis(token_addr, pairs)

    # 3b. pump.fun Tracker
    result["pumpfun"] = pumpfun_detect_new_tokens(pairs)

    # 3c. SharpeAI Market Intelligence
    symbol = pairs[0].get("baseToken", {}).get("symbol", query) if pairs else query
    result["sharpeai"] = sharpeai_full_analysis(symbol, pairs)

    # 3d. Token Sniffer Security
    rug_summary_data = result.get("rugCheck", {}).get("summary") if result.get("rugCheck") else None
    result["tokensniffer"] = tokensniffer_full_analysis(token_addr, rug_summary_data, pairs)

    # 4. Compute aggregated summary
    result["summary"] = compute_summary(result)

    return result


def compute_summary(data: dict) -> dict:
    """Compute an aggregated risk & opportunity summary."""
    dex = data.get("dexScreener", {})
    rug = data.get("rugCheck", {})
    rug_summary = rug.get("summary", {}) if rug else {}
    top_pairs = dex.get("topPairs", [])

    # Market metrics
    total_volume_24h = sum(
        p.get("volume", {}).get("h24", 0) for p in top_pairs if p.get("volume")
    )
    total_liquidity = sum(
        p.get("liquidity", {}).get("usd", 0) for p in top_pairs if p.get("liquidity")
    )

    best_pair = top_pairs[0] if top_pairs else None
    market_cap = best_pair.get("marketCap", 0) if best_pair else 0
    price_usd = best_pair.get("priceUsd", "0") if best_pair else "0"
    price_change_24h = best_pair.get("priceChange", {}).get("h24", 0) if best_pair else 0
    txns_24h = best_pair.get("txns", {}).get("h24", {}) if best_pair else {}
    buys_24h = txns_24h.get("buys", 0)
    sells_24h = txns_24h.get("sells", 0)

    # RugCheck score
    rug_score = rug_summary.get("score", None) if rug_summary else None
    rug_risks = rug_summary.get("risks", []) if rug_summary else []
    risk_count = len(rug_risks)

    # Risk assessment — more nuanced for established tokens
    risk_level = "Unknown"
    opportunity = "Neutral"

    if rug_score is not None:
        # Established tokens often have low scores due to admin keys
        is_established = (market_cap > 20000000 and total_liquidity > 500000) or market_cap > 100000000

        if rug_score >= 900:
            risk_level = "Low Risk ✅"
            opportunity = "Established Token 📈" if is_established else "Potential Gem 💎"
        elif rug_score >= 700:
            risk_level = "Low-Medium Risk ✅"
            opportunity = "Established Token 📈" if is_established else "Potential Gem 💎"
        elif rug_score >= 500:
            risk_level = "Medium Risk ⚠️"
            if is_established:
                opportunity = "Established Token 📈"
            elif market_cap < 500000 and total_liquidity > 10000 and total_volume_24h > 50000:
                opportunity = "Potential Gem 💎"
        elif rug_score >= 300:
            risk_level = "High Risk 🔴"
            if is_established:
                opportunity = "Established (But Risky) ⚠️"
            else:
                opportunity = "High Risk — Caution ⚠️"
        else:
            risk_level = "Critical Risk 🚨"
            if is_established:
                # Well-known tokens with admin keys still active
                opportunity = "Established (Admin Keys) 📊"
            else:
                opportunity = "Dangerous ⛔"

    # Override opportunity for clearly established tokens regardless of rug score
    if market_cap > 1000000000 and total_liquidity > 10000000:
        opportunity = "Major Token 📊"

    return {
        "marketCap": market_cap,
        "priceUsd": price_usd,
        "priceChange24h": price_change_24h,
        "volume24h": total_volume_24h,
        "liquidity": total_liquidity,
        "buys24h": buys_24h,
        "sells24h": sells_24h,
        "buySellRatio": round(buys_24h / max(sells_24h, 1), 2),
        "totalPairs": dex.get("totalPairs", 0),
        "rugScore": rug_score,
        "rugRiskCount": risk_count,
        "riskLevel": risk_level,
        "opportunity": opportunity,
        "chain": best_pair.get("chainId", "unknown") if best_pair else "unknown",
        "dex": best_pair.get("dexId", "unknown") if best_pair else "unknown",
        "tokenName": best_pair.get("baseToken", {}).get("name", "Unknown") if best_pair else "Unknown",
        "tokenSymbol": best_pair.get("baseToken", {}).get("symbol", "???") if best_pair else "???",
        "tokenAddress": best_pair.get("baseToken", {}).get("address", "") if best_pair else "",
        "imageUrl": best_pair.get("info", {}).get("imageUrl", "") if best_pair else "",
    }
