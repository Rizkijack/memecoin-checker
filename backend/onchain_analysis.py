"""
On-Chain Analysis Module
Simulasi analisis on-chain: holder distribution, sniper detection, whale activity.
Inspirasi dari GMGN, BubbleMaps, dan platform on-chain analytics.
"""
import random
import math


def simulate_holder_analysis(token_address: str) -> dict:
    """
    Simulated holder distribution analysis.
    In production, this would query Solana RPC for actual holder data.
    """
    # Deterministic simulation based on address hash
    seed = hash(token_address) % 10000
    rng = random.Random(seed)

    total_holders = rng.randint(150, 50000)
    
    # Top 10 holder concentration
    top10_pct = round(rng.uniform(5, 65), 1)
    creator_pct = round(rng.uniform(0.5, 15), 1)
    
    # Whale detection
    whales = rng.randint(0, 8)
    
    # Sniper detection
    snipers = rng.randint(0, 12)
    sniper_bought_pct = round(snipers * rng.uniform(0.5, 3), 1)
    
    # Holder distribution
    dist = {
        "top1": round(rng.uniform(1, 25), 1),
        "top10": top10_pct,
        "top50": round(min(top10_pct + rng.uniform(5, 20), 98), 1),
        "creator": creator_pct,
        "whales": whales,
        "snipers": snipers,
        "sniperSupplyPct": min(sniper_bought_pct, 30),
    }

    # Risk assessment
    risks = []
    if top10_pct > 50:
        risks.append("Highly concentrated top 10 holders (>50%)")
    if creator_pct > 10:
        risks.append(f"Creator holds {creator_pct}% — high insider risk")
    if snipers > 5:
        risks.append(f"{snipers} sniper wallets detected")
    if whales > 5:
        risks.append(f"{whales} whale wallets with large positions")

    return {
        "totalHolders": total_holders,
        "distribution": dist,
        "risks": risks,
        "whaleActivity": "high" if whales > 3 else "moderate" if whales > 1 else "low",
        "sniperActivity": "high" if snipers > 5 else "moderate" if snipers > 1 else "low",
    }


def simulate_tx_velocity(token_address: str, dex_pairs: list) -> dict:
    """
    Transaction velocity analysis — detect wash trading and bot activity.
    """
    seed = hash(token_address + "tx") % 10000
    rng = random.Random(seed)

    # Base metrics from pairs
    total_vol = sum(p.get("volume", {}).get("h24", 0) or 0 for p in dex_pairs[:5])
    total_txns = sum(
        (p.get("txns", {}).get("h24", {}) or {}).get("buys", 0) + 
        (p.get("txns", {}).get("h24", {}) or {}).get("sells", 0)
        for p in dex_pairs[:5]
    )

    avg_tx_size = total_vol / max(total_txns, 1)
    bot_pct = round(rng.uniform(5, 60), 1)
    wash_trade_risk = "low" if bot_pct < 15 else "moderate" if bot_pct < 35 else "high"

    return {
        "avgTxSizeUsd": round(avg_tx_size, 2),
        "botActivityPct": bot_pct,
        "washTradeRisk": wash_trade_risk,
        "uniqueWallets24h": rng.randint(50, 5000),
        "suspiciousTxPct": round(rng.uniform(0, 25), 1),
    }


def simulate_liquidity_analysis(token_address: str, pairs: list) -> dict:
    """
    Liquidity health analysis — lock status, LP concentration.
    """
    seed = hash(token_address + "liq") % 10000
    rng = random.Random(seed)

    total_liq = sum(p.get("liquidity", {}).get("usd", 0) or 0 for p in pairs[:5])
    
    lp_locked_pct = round(rng.uniform(30, 100), 1)
    lp_holders = rng.randint(1, 50)
    top_lp_pct = round(rng.uniform(10, 80), 1)

    risks = []
    if lp_locked_pct < 50:
        risks.append(f"Only {lp_locked_pct}% LP locked — high removal risk")
    if top_lp_pct > 50:
        risks.append(f"Top LP holder owns {top_lp_pct}% — centralization risk")

    return {
        "totalLiquidityUsd": round(total_liq, 2),
        "lpLockedPct": lp_locked_pct,
        "lpHolders": lp_holders,
        "topLpHolderPct": top_lp_pct,
        "risks": risks,
    }


def full_onchain_analysis(token_address: str, dex_pairs: list) -> dict:
    """
    Full on-chain analysis combining holder, tx, and liquidity analysis.
    """
    holder = simulate_holder_analysis(token_address)
    tx = simulate_tx_velocity(token_address, dex_pairs)
    liq = simulate_liquidity_analysis(token_address, dex_pairs)

    # Overall risk score (simulated)
    all_risks = holder.get("risks", []) + liq.get("risks", [])
    risk_score = max(1, 10 - len(all_risks) * 2 - 
                     (1 if holder["distribution"]["top10"] < 30 else 0) -
                     (1 if tx["washTradeRisk"] == "low" else 0) -
                     (1 if liq["lpLockedPct"] > 80 else 0))

    return {
        "holderAnalysis": holder,
        "txVelocity": tx,
        "liquidityHealth": liq,
        "totalRisks": all_risks,
        "onChainRiskScore": min(10, max(1, risk_score)),
        "onChainRiskLevel": "Low" if risk_score <= 3 else "Medium" if risk_score <= 6 else "High",
    }
