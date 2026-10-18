# AI Stock Analysis Agent

On `/stock/:symbol`, **Analyze with AI** opens a ChaiUI dialog. The launcher stays at the bottom right; other routes have no launcher. Analysis starts only on click. Reports include a summary, strengths, risks, watch items and clickable evidence with amounts, reporting currencies, periods, formulas and calculation inputs. Yahoo Finance source links, Advanced chart and View market quote links are removed from the UI. Closing the dialog preserves pending work; changing stock aborts that page's request.

## Configuration

In `backend/.env`:

```dotenv
NVIDIA_API_KEY=your-nvidia-key
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```

The model shown above is the default when `NVIDIA_MODEL` is absent. The backend uses the installed OpenAI SDK as an HTTP client for NVIDIA's API, with `base_url=https://integrate.api.nvidia.com/v1` and `api_key=NVIDIA_API_KEY`. It never falls back to `OPENAI_API_KEY`, another model or another provider. Credentials stay server-side and NVIDIA response bodies are not returned to clients. The request matches [NVIDIA's streaming example](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b): `temperature=1`, `top_p=0.95`, `max_tokens=16384`, `chat_template_kwargs.enable_thinking=True` and `stream=True`. Only final `delta.content` is collected; reasoning deltas are neither stored nor displayed. Empty-choice chunks are skipped and a successful finish is required before validating the final research JSON. Each attempt has a two-minute overall timeout, including streaming; SDK automatic retries are disabled in favor of the existing bounded retry.

`POST /api/v1/ai/analyze` accepts only `{"symbol":"NVDA"}` and requires the existing user Bearer token. `GET /api/v1/ai/summary/:symbol` now uses the same real agent, preserving its legacy summary/keyPoints fields. Bare Indian names such as `RELIANCE` and `MTARTECH` resolve through stock search, preferring NSE; explicit `.NS`/`.BO` symbols also work.

## Data and verification boundaries

Yahoo Finance/yfinance provides quotes, profile, annual/quarterly income statements, balance sheets and cash flows. Calculations run in Python, using raw amounts rather than UI-scaled figures. Ratios require comparable periods and positive denominators. Missing statement currency causes those amounts/ratios to be omitted. ADR quote and reporting currencies remain separate.

Before NVIDIA runs, `financial_evidence.py` checks listing identity, source URLs, source fields and exact original values. Every derived metric is independently recomputed from its input evidence, with matching currencies, units and fiscal periods. The output is checked again before returning it. This verifies consistency with the retrieved provider records, not agreement with independent audited filings.

The backend produces a finite set of financial findings from those checks. NVIDIA selects and ranks their IDs within allowed report sections; the server supplies the final wording, citations and significance. Unknown IDs, duplicate findings, wrong-section selections and free-form claims are rejected, with one correction attempt. This prevents the model from introducing unsupported financial assertions through otherwise valid citation IDs. Significance represents a deterministic ordering of the reported financial facts, not a probability, price forecast or investment rating.

Reports bind `companyId` (exchange plus symbol), `analysisRunId`, quote identity and every evidence record. The frontend rejects mismatched listing identities and identifies NVIDIA explicitly as the AI provider. Cached reports retain their original run ID and generation time.

Period types distinguish fiscal-year, quarterly, balance-sheet dates, TTM, provider snapshots and comparisons. Provider trailing metrics explicitly say when their exact end date is unknown. Annual ROE uses annual net income divided by average positive beginning/end shareholders equity; it is separate from the provider's trailing ROE percentage conversion. The UI labels the latter **Provider · unit conversion**, not **Recalculated**. TTM revenue and profit require four consecutive reported quarters; missing quarters do not become a TTM estimate. [ROE methodology example](https://www.sec.gov/Archives/edgar/data/946673/000119312523104991/d469726dars.pdf), [yfinance financial statement frequencies](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.get_income_stmt.html).

The Financial trends tab displays up to five available annual and six quarterly periods with revenue, net income, net margin and clickable fiscal-period evidence. No missing history is fabricated. Evidence quality shows actual history counts and calculation checks, with limited/partial/available coverage rather than an invented AI confidence percentage. Specific data checks explain annual loss versus positive trailing P/E, inconsistent provider EPS/P/E, missing inputs and stale observations (seven days for quotes, 550 days for annual statements, 210 days for quarterly statements). Disputed provider EPS/P/E values are excluded from headline metric cards. Unknown provider trailing dates remain explicit.

Primary filings, management guidance and recent news are outside this version's coverage. Filing RAG/Qdrant ingestion, peer valuation benchmarks, follow-up document questions and specialist LangGraph agents remain later milestones; they require a filing/document corpus and independently comparable data. The generic coverage/limitations section, investment disclaimer and external source links stay omitted from the UI at the user's request.

Successful reports are cached for ten minutes per worker with a bounded cache and four concurrent jobs. Concurrent requests for the same symbol/model share work. Shared Redis caching can replace this if multiple workers need the same cache. NVIDIA gateway/unavailable errors (502/503/504) and SDK stream error events get one retry after two seconds, within the same two-attempt budget used for structured output correction. NVIDIA can also open an HTTP 200 stream and then emit an overload error event; partial output from a failed stream is discarded. Persistent unavailability returns HTTP 503 with a safe explanation and `Retry-After: 30`. Logs record only the model, upstream status (when available) and attempt, without response bodies or credentials. Authentication, quota and request configuration failures are not automatically retried. The UI handles these errors and retry; it never substitutes fabricated research.

## Checks

From `backend` (set `DEBUG=false` if an inherited environment value is incompatible):

```powershell
.\venv\Scripts\python.exe -m pytest app/tests/test_ai.py app/tests/test_stock_analysis.py app/tests/test_financial_evidence.py app/tests/test_stock_detail.py app/tests/test_us_stocks.py app/tests/test_stocks.py app/tests/test_config.py -q
# Optional live provider calls, using backend/.env:
.\venv\Scripts\python.exe ../docs/ai-stock-analysis/live_check.py NVDA AAPL RELIANCE MTARTECH
# Public financial evidence checks without any LLM call:
.\venv\Scripts\python.exe ../docs/ai-stock-analysis/live_check.py --evidence BE NVDA AAPL RELIANCE MTARTECH
```

With Vite running, from the repository root:

```powershell
$env:APP_URL = 'http://127.0.0.1:5175'
node docs/ai-stock-analysis/verify.cjs
```

Browser checks use isolated authentication, stock and report fixtures; they do not modify user data or invoke NVIDIA. Screenshots cover dark/light modes at desktop/mobile widths. The live check writes public-data reports only on success and never prints credentials. `--probe` checks the exact model's status with a short request.

Live verification on 2026-10-17 retrieved enough financial evidence for NVDA, AAPL, RELIANCE and MTARTECH to reach NVIDIA, but NVIDIA returned an overload error. A direct non-streaming probe returned **HTTP 503: Service temporarily overloaded**. The exact official SDK streaming example also opened a stream and then raised **APIError: Service temporarily overloaded**. Consequently live report generation remains unverified; deterministic tests cover successful streaming, reasoning/content separation, truncated streams and errors inside HTTP-success streams.

After the validation upgrade, live source checks passed for BE, NVDA, AAPL, RELIANCE.NS and MTARTECH.NS, with four complete annual and five quarterly periods each. BE/NVDA/AAPL had 20 independently checked calculations each; RELIANCE/MTARTECH had 17 each. BE correctly triggered an annual-versus-trailing earnings-period note. The live BE NVIDIA stream still failed on both attempts with a provider error. `live-evidence-*.json` records the public financial checks; these are evidence-only results, not successful AI-generated reports.
