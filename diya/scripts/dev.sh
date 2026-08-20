#!/bin/bash
# DIYA - Local Development Runner
# Starts all services in development mode.

set -e

echo "=== DIYA Development Server ==="
echo ""

# Start API Gateway in background
echo "Starting API Gateway on :8000..."
cd apps/api-gateway
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ../..

# Start Mesh Service in background
echo "Starting Mesh Service on :8001..."
cd apps/mesh-service
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8001 &
MESH_PID=$!
cd ../..

# Start Agent Service in background
echo "Starting Agent Service on :8002..."
cd apps/agent-service
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8002 &
AGENT_PID=$!
cd ../..

# Start Notice Service in background
echo "Starting Notice Service on :8003..."
cd apps/notice-service
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8003 &
NOTICE_PID=$!
cd ../..

# Start Frontend
echo "Starting Frontend on :3000..."
cd apps/web
npx next dev --port 3000 &
WEB_PID=$!
cd ../..

echo ""
echo "=== All services started ==="
echo "  Frontend:       http://localhost:3000"
echo "  API Gateway:    http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo "  Mesh Service:   http://localhost:8001"
echo "  Agent Service:  http://localhost:8002"
echo "  Notice Service: http://localhost:8003"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap to kill all background processes
trap "kill $API_PID $MESH_PID $AGENT_PID $NOTICE_PID $WEB_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for any process to exit
wait
