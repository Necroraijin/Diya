# DIYA - Multi-Agent Infrastructure Conflict Resolution System

> Preventing municipal departments from digging up the same road repeatedly.

DIYA uses a fleet of AI agents (Google ADK + Gemini) to detect spatial and temporal conflicts across department infrastructure plans, propose consolidated work windows, and generate real citizen notices — turning months of siloed planning into coordinated "dig once" execution.

## Architecture

```
Microservices: web (Next.js) | api-gateway (FastAPI) | agent-service (ADK) | mesh-service | notice-service
```

## Quick Start

```bash
# Install frontend dependencies
cd apps/web && npm install

# Run frontend
npm run dev

# Or run everything with Docker
docker compose -f docker/docker-compose.yml up --build
```

## Tech Stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Framer Motion, deck.gl
- **Backend:** FastAPI (Python), Firestore, Pub/Sub, Cloud Storage
- **AI Agents:** Google ADK, Gemini 3.5 Flash via Vertex AI
- **Governance:** Agent Identity, Gateway, Model Armor, Memory Bank, Observability
- **Infrastructure:** Docker, Cloud Run, GCP

## Data

All department data is **synthetic/demo data** generated for demonstration purposes. It uses real OSM road names and realistic Indian municipal department naming but does not represent any actual government records or citizen data.

## License

MIT

## Hackathon

Built for the All Things Agentic Hackathon 2026 (Google) — Fortified Enterprise Fleet Track.
