#!/bin/bash
# DIYA - Project Setup Script
# Run this once after cloning the repository.

set -e

echo "=== DIYA Setup ==="
echo ""

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "Node.js is required. Install from https://nodejs.org"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required. Install Node.js from https://nodejs.org"; exit 1; }

echo "[1/4] Installing frontend dependencies..."
cd apps/web
npm install
cd ../..

echo ""
echo "[2/4] Setting up Python virtual environments..."
for service in api-gateway mesh-service agent-service notice-service; do
    echo "  Setting up $service..."
    cd "apps/$service"
    python -m venv .venv 2>/dev/null || python3 -m venv .venv 2>/dev/null || echo "  Warning: Could not create venv for $service (Python 3 required)"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        pip install -q -r requirements.txt
        deactivate
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        pip install -q -r requirements.txt
        deactivate
    fi
    cd ../..
done

echo ""
echo "[3/4] Creating environment files..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# DIYA Environment Configuration
GOOGLE_CLOUD_PROJECT=diya-demo
VERTEX_AI_LOCATION=us-central1
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "  Created .env file"
else
    echo "  .env already exists, skipping"
fi

echo ""
echo "[4/4] Verifying setup..."
cd apps/web
npx next build --no-lint 2>/dev/null && echo "  Frontend build: OK" || echo "  Frontend build: FAILED"
cd ../..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Quick start:"
echo "  Frontend:     cd apps/web && npm run dev"
echo "  API Gateway:  cd apps/api-gateway && uvicorn main:app --port 8000 --reload"
echo "  Docker:       docker compose -f docker/docker-compose.yml up --build"
echo ""
