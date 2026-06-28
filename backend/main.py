"""
Memecoin Checker — Backend Server
API Aggregator untuk analisis token memecoin dari DexScreener, RugCheck, dll.
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from api_providers import analyze_token, dexscreener_latest_profiles, dexscreener_token_pairs
from onchain_analysis import full_onchain_analysis
from gmgn_analysis import gmgn_full_analysis
from pumpfun_tracker import pumpfun_detect_new_tokens
from sharpeai_analysis import sharpeai_full_analysis
from tokensniffer_analysis import tokensniffer_full_analysis

app = FastAPI(
    title="Memecoin Checker API",
    description="Aggregator analisis memecoin dari DexScreener, RugCheck, dan lainnya",
    version="1.0.0",
)

# CORS — allow frontend from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Endpoints ─────────────────────────────────────────────

@app.get("/api/analyze")
async def api_analyze(
    q: str = Query(..., description="Token name, symbol, or contract address"),
):
    """Analyze a memecoin using all available data sources."""
    try:
        data = await analyze_token(q.strip())
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.get("/api/trending")
async def api_trending():
    """Get latest trending token profiles from DexScreener."""
    try:
        profiles = await dexscreener_latest_profiles()
        return {"success": True, "data": profiles[:30]}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.get("/api/onchain")
async def api_onchain(address: str = Query(..., description="Token contract address")):
    """Get on-chain analysis for a token address (GMGN-style)."""
    try:
        dex_data = await dexscreener_token_pairs(address)
        pairs = dex_data.get("pairs", [])
        analysis = full_onchain_analysis(address, pairs)
        return {"success": True, "data": analysis}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.get("/api/gmgn")
async def api_gmgn(address: str = Query(..., description="Token contract address")):
    """GMGN-style on-chain holder & sniper analysis."""
    try:
        dex_data = await dexscreener_token_pairs(address)
        pairs = dex_data.get("pairs", [])
        analysis = gmgn_full_analysis(address, pairs)
        return {"success": True, "data": analysis}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/tokensniffer")
async def api_tokensniffer(address: str = Query(..., description="Token contract address")):
    """Token Sniffer-style contract security analysis."""
    try:
        from api_providers import rugcheck_summary
        rug_summary = await rugcheck_summary(address)
        dex_data = await dexscreener_token_pairs(address)
        pairs = dex_data.get("pairs", [])
        analysis = tokensniffer_full_analysis(address, rug_summary, pairs)
        return {"success": True, "data": analysis}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/sharpeai")
async def api_sharpeai(address: str = Query(..., description="Token contract address")):
    """SharpeAI-style market intelligence & sentiment analysis."""
    try:
        dex_data = await dexscreener_token_pairs(address)
        pairs = dex_data.get("pairs", [])
        symbol = pairs[0].get("baseToken", {}).get("symbol", "?") if pairs else "?"
        analysis = sharpeai_full_analysis(symbol, pairs)
        return {"success": True, "data": analysis}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/health")
async def api_health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Memecoin Checker API v1.0.0"}


# ─── Static frontend serving ─────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend not found. Run: cd frontend && ls"}


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static frontend files."""
    file_path = FRONTEND_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    return JSONResponse(status_code=404, content={"error": "Not found"})


# ─── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 Memecoin Checker running on http://0.0.0.0:{port}")
    print(f"   API Docs: http://0.0.0.0:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
