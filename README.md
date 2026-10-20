# Asset Hunter (Screen Finance)

Asset Hunter is a stock research application for US and Indian equities. It combines market data, charts, natural-language financial screening, and AI research grounded in retrieved financial evidence. The frontend uses React and Vite; the backend uses FastAPI, PostgreSQL, SQLAlchemy, and LangGraph.

## NVIDIA Nemotron usage

NVIDIA Nemotron powers two implemented features:

| Feature | How Nemotron is used | What the backend verifies |
| --- | --- | --- |
| Natural-language stock screening | Converts requests such as “Find US companies with ROE above 20% and debt-to-equity below 0.5” into structured JSON filters. | Supported metrics, original thresholds, units, markets, and reporting periods are validated before parameterized SQLAlchemy queries run against PostgreSQL. The model never generates executable SQL or stock results. |
| Stock analysis | Selects and ranks verified financial findings into summary, strengths, risks, and watch items. | Financial calculations, listing identity, currencies, reporting periods, source references, and selected finding IDs are checked by the server. Final claim wording and citations come from verified findings. |

When Nebius is configured, both features use **`nvidia/nemotron-3-super-120b-a12b`** through Token Factory. The direct NVIDIA API configuration defaults to **`nvidia/nemotron-3-ultra-550b-a55b`**; `NVIDIA_SCREENER_MODEL` can select a separate screening model for that provider.

Screening disables model thinking for structured filter extraction. Stock analysis enables thinking, but collects only final response content; reasoning deltas are not stored or displayed. Users can review and edit screening conditions before rerunning them without another model call.

Implementation references:

- [Provider and model selection](backend/app/config.py)
- [Nemotron filter extraction](backend/app/services/screener/parser.py) and [LangGraph screening workflow](backend/app/agents/screener/graph.py)
- [AI stock analysis](backend/app/services/ai/stock_analysis_service.py) and [financial evidence validation](backend/app/services/ai/financial_evidence.py)

## How Nebius Token Factory accelerated the workflow

Token Factory provides the hosted inference endpoint used by the two AI features. The backend connects through the existing OpenAI-compatible Python client:

```text
FastAPI -> OpenAI-compatible client -> Nebius Token Factory -> NVIDIA Nemotron
```

This integration reduced infrastructure and integration work in three concrete places:

- **Model access:** hosted inference removes the need to download model weights or provision and maintain a GPU inference server for local application development.
- **Provider integration:** screening and analysis share the same provider configuration and client interface. Selecting Token Factory requires environment variables rather than separate implementations of those features.
- **Prompt iteration:** the existing streaming client supports both JSON filter extraction and evidence-based finding selection, allowing work to focus on prompts, validation, and the research UI.

These are workflow benefits of the integration; this repository does not include measured development-time, latency, or cost improvements. [Provider integration tests](backend/app/tests/test_nebius_client.py) verify that both AI entry points use the configured Nebius endpoint, model, and credentials with mocked responses.

### Nebius tools and services used

| Tool or service | Role in this project |
| --- | --- |
| Nebius Token Factory | Hosted NVIDIA Nemotron inference for natural-language screening and stock analysis, configured with `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, and `NEBIUS_MODEL`. |

Token Factory is the Nebius service integrated in the current codebase. No additional Nebius compute, storage, training, or deployment services are configured. Application deployment is documented separately in [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md).

## Local setup

### Prerequisites

- Python 3.11 or newer.
- Node.js 22.12 or newer and npm.
- Docker with Docker Compose for local PostgreSQL and Redis, or equivalent running services.
- A Nebius Token Factory API key for AI features, or a direct NVIDIA API key.
- Internet access to retrieve market data and call the selected inference provider.

The commands below use PowerShell and start from the repository root.

### 1. Configure environment files

For a fresh checkout, copy the examples. Keep any existing local configuration instead of overwriting it.

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Set the following values in `backend/.env`, replacing the placeholders with your own secrets:

```dotenv
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/screenfinance
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=replace-with-a-long-random-secret

NEBIUS_API_KEY=your-token-factory-api-key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
```

For direct NVIDIA inference instead, leave `NEBIUS_API_KEY` empty and configure:

```dotenv
NVIDIA_API_KEY=your-nvidia-api-key
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
# Optional separate model for screening:
NVIDIA_SCREENER_MODEL=nvidia/nemotron-3-super-120b-a12b
```

A nonempty `NEBIUS_API_KEY` takes precedence for both AI features. Failed Nebius calls do not silently switch to NVIDIA. The OpenAI SDK is used as a compatible client; these features do not use `OPENAI_API_KEY`. Restart the backend after changing its environment settings.

In `frontend/.env`, use:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

Email/password registration works without Google OAuth. For Google sign-in, configure `GOOGLE_CLIENT_ID` in the backend and the same public client ID as `VITE_GOOGLE_CLIENT_ID` in the frontend, with the frontend origin authorized in Google Cloud. Additional market-provider keys are listed in [backend/.env.example](backend/.env.example).

Keep API keys in the backend environment. Only public frontend settings should use the `VITE_` prefix. Never commit real credentials.

### 2. Start the local data services

```powershell
docker compose up -d postgres redis
```

This starts PostgreSQL on port `5432` and Redis on port `6379`. Wait for PostgreSQL to become healthy before applying migrations. Qdrant is available separately with `docker compose up -d qdrant`; it is not required by the current screening and stock-analysis flows.

### 3. Install and run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/refresh_screener.py
python -m uvicorn app.main:app --reload --port 8000
```

The refresh imports the starter universe of sixteen real US/Indian stock symbols and their available verified metrics. It calls market-data providers and may take time or encounter provider limits. Screening uses this imported universe, so a fresh database needs the refresh before it can return stock matches. It is not an exchange-wide dataset.

To refresh specific companies later, run this from `backend/` with the virtual environment activated:

```powershell
python ../scripts/refresh_screener.py AAPL NVDA RELIANCE.NS MTARTECH.NS
```

### 4. Install and run the frontend

Open a second terminal at the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`, register an account, and sign in. The API documentation is at `http://localhost:8000/docs`. Check database connectivity at `http://localhost:8000/health/db`; a successful response includes `"status": "ok"`.

### 5. Try the AI features

1. Open **AI Screener** from the feed and ask: “Find US companies with ROE above 20% and debt-to-equity below 0.5.”
2. Review the extracted filters and the matching imported stocks. Empty results can reflect the available dataset and thresholds.
3. Open a stock such as `AAPL` or `NVDA` and choose **Analyze with AI** to generate a report from available financial evidence.

AI requests require authentication, a valid provider key, and sufficient available provider quota. Unsupported screening conditions request clarification. Provider failures return an error rather than fabricated research.

## Validation and further documentation

Run the provider and AI regression checks from `backend/` with the virtual environment activated:

```powershell
python -m pytest app/tests/test_nebius_client.py app/tests/test_nl_screener.py app/tests/test_stock_analysis.py app/tests/test_financial_evidence.py -q
```

These checks use mocked inference responses and do not establish live provider availability. To verify the frontend build, run `npm run build` from `frontend/`.

- [Deployment instructions](VERCEL_DEPLOYMENT.md)
- [Screening behavior, supported metrics, and data coverage](docs/nl-screener/README.md)
- [Stock-analysis evidence checks and recorded verification](docs/ai-stock-analysis/README.md)

Some older feature notes describe the original NVIDIA-only configuration; the provider selection documented above reflects the current code. General chat, comparison, and several background/embedding pipelines remain placeholders and are not part of the implemented Nemotron flows.
