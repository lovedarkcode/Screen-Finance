# Vercel deployment

This repository is configured as one Vercel project:

- `frontend/` builds with Vite into `frontend/dist`.
- `/api/*` routes are handled by the FastAPI app through `api/index.py`.
- React Router paths fall back to `index.html`.

Production: https://assest-hunter.vercel.app

The fresh project uses Neon PostgreSQL and Upstash Redis connected through Vercel
Marketplace. Both inject their production connection URLs into the backend.
The Python function has a 300-second limit for financial research requests.
Provider cookies and timezone caches use the function's writable temp directory.

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
NEBIUS_API_KEY=<key>
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
FINNHUB_API_KEY=<key>
ALPHA_VANTAGE_API_KEY=<key>
POLYGON_API_KEY=<key>
GOOGLE_CLIENT_ID=<client-id>
VITE_GOOGLE_CLIENT_ID=<same-public-client-id>
```

## Deploy from CLI

The backend reads `backend/.env` locally. For deployed AI screening and stock
analysis, set `NEBIUS_API_KEY` in Vercel's server environment and redeploy;
the local `.env` file is not uploaded. Never use a `VITE_` prefix for this key.
The URL and model above are defaults and can be omitted. A configured Nebius
key takes precedence over NVIDIA credentials for both features. Without a Nebius
key, the existing NVIDIA configuration is used; failed Nebius calls do not
silently retry against NVIDIA. Restart the local backend after changing `.env`.

```powershell
npm install -g vercel
vercel login
vercel
vercel --prod
```

When prompted, use the repository root as the project directory. Vercel will read `vercel.json`.

## Important hosting note

Vercel does not run the Docker services from `docker-compose.yml`. Use hosted services for Postgres, Redis, and Qdrant, then put their connection URLs in Vercel environment variables.

Only PostgreSQL and Redis are used by the current deployed API paths; Qdrant and
Celery workers are not running on Vercel. Quarterly results have a separate,
implemented worker: it must run on a persistent host against the same production
database. Vercel does not start it from Docker Compose. The screener's original
sixteen-symbol metric import is separate from the quarterly exchange catalog.
The new database starts with fresh user accounts. Local test accounts were not
copied. Google OAuth's authorized origins must include the production domain in
the Google Cloud console; email/password sign-in is independently verified.

Migrations are applied explicitly with `alembic upgrade head` using a hosted
`DATABASE_URL` (prefer the unpooled URL for migrations). They do not run during
function startup. To refresh public screening data, run
`python ../scripts/refresh_screener.py` from `backend/` with the hosted connection
set in the shell. This updates only the imported stock universe.

## Quarterly results returning HTTP 503

The database health endpoint tests connectivity with `SELECT 1`; it does not
verify the feature's schema. A healthy database can still lack newly deployed
tables or columns. The results endpoint uses the shared screening database
dependency, which is why older deployments report "The screening database is
unavailable" for these schema failures too.

On 20 October 2026, production was still at revision `a31f70d293c1`, while the
local backend used a different, already migrated database. Production lacked
`quarterly_results`, `quarterly_poll_state` and `result_listings`. Applying the
four additive migrations through `e0c42b5138df` fixed the live 503. Authenticated
checks of `/api/v1/results?page_size=12` and the `/api/results/latest` alias
returned 200. See [the production verification](docs/deployment/results-database-verification.json).

Before using a newly deployed database feature, set `DATABASE_URL` in the
operator terminal to the **production** database, preferably its unpooled URL
for migrations, then run from `backend/`:

```powershell
$env:DEBUG = 'false'
python -m alembic current
python -m alembic upgrade head
```

Running this against the URL in a developer's `backend/.env` does not migrate a
different Vercel database. `vercel env pull` can help retrieve configuration,
but sensitive values may be replaced by `[SENSITIVE]`; those markers are not
usable credentials. Keep downloaded environment files ignored and never print
connection strings or keys into logs.

After migrations, an empty results catalog means ingestion has not populated
that database yet. Start the worker on a persistent host with the production
`DATABASE_URL` and the appropriate server-side Nebius configuration:

```powershell
python -m app.workers.quarterly_results_worker --bootstrap
```

This discovers exchange catalogs, fetches Yahoo statements in paced batches,
and then follows the 15-minute schedule. A worker writing to a local database
will not update the production UI. Read requests do not launch ingestion.
See [worker settings, coverage and API details](docs/quarterly-results/PIPELINE.md).

The shared database dependency now logs exception type and SQLSTATE without SQL,
parameters or credentials. Missing-table/column errors (`42P01`, `42703`) return
an explicit migration instruction after deploying the updated code. The live
schema repair itself does not require a redeploy.

The root requirements file contains only packages needed by deployed API routes.
The full backend requirements include local tooling and workers and should not
be substituted for the production list. Environment files, virtual environments,
tests, docs and scripts are excluded from deployment uploads. Production secrets
are stored in Vercel; sensitive values are not returned by `vercel env pull`.

Live verification results are recorded in `docs/deployment/live-verification.json`.
