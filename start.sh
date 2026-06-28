#!/usr/bin/env bash
# Memecoin Checker — Quick Start
# Jalankan dari folder ini: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "========================================"
echo "  🔍 Memecoin Checker — Quick Start"
echo "========================================"
echo ""

# Install deps
echo "📦 Installing backend dependencies..."
cd "$BACKEND_DIR"
python -m pip install -q -r requirements.txt 2>&1 | tail -1

# Start server
echo ""
echo "🚀 Starting server on http://0.0.0.0:8000"
echo "   Open http://localhost:8000 in your browser"
echo "   API Docs: http://localhost:8000/docs"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
