# Vercel deployment

This repository is configured as one Vercel project:

- `frontend/` builds with Vite into `frontend/dist`.
- `/api/*` routes are handled by the FastAPI app through `api/index.py`.
- React Router paths fall back to `index.html`.

## Required production environment variables

Set these in Vercel Project Settings > Environment Variables:

```text
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<strong-random-secret>
DATABASE_URL=<hosted-postgres-url>
BACKEND_CORS_ORIGINS=["https://assest-hunter.vercel.app","https://your-custom-domain.com"]
```

Optional, depending on enabled features:

```text
REDIS_URL=<hosted-redis-url>
QDRANT_URL=<hosted-qdrant-url>
OPENAI_API_KEY=<key>
FINNHUB_API_KEY=<key>
ALPHA_VANTAGE_API_KEY=<key>
POLYGON_API_KEY=<key>
GOOGLE_CLIENT_ID=<client-id>
```

## Deploy from CLI

```powershell
npm install -g vercel
vercel login
vercel
vercel --prod
```

When prompted, use the repository root as the project directory. Vercel will read `vercel.json`.

## Important hosting note

Vercel does not run the Docker services from `docker-compose.yml`. Use hosted services for Postgres, Redis, and Qdrant, then put their connection URLs in Vercel environment variables.
