<p align="center">
  <img src="assets/TauricResearch.png" style="width: 60%; height: auto;">
</p>

<div align="center" style="line-height: 1;">
  <a href="https://arxiv.org/abs/2412.20138" target="_blank"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2412.20138-B31B1B?logo=arxiv"/></a>
  <a href="https://discord.com/invite/hk9PGKShPK" target="_blank"><img alt="Discord" src="https://img.shields.io/badge/Discord-TradingResearch-7289da?logo=discord&logoColor=white&color=7289da"/></a>
  <a href="https://x.com/TauricResearch" target="_blank"><img alt="X Follow" src="https://img.shields.io/badge/X-TauricResearch-white?logo=x&logoColor=white"/></a>
  <a href="https://github.com/TauricResearch/" target="_blank"><img alt="Community" src="https://img.shields.io/badge/GitHub_Community-TauricResearch-14C290?logo=discourse"/></a>
</div>
<br>
<div align="center">
  <a href="https://github.com/TauricResearch" target="_blank"><img alt="TradingAgents #1 Repository of the Day" src="https://trendshift.io/api/badge/repositories/16192" width="250" height="55"/></a>
</div>
<br>
<div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=de">Deutsch</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=es">Español</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=fr">français</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ja">日本語</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ko">한국어</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=pt">Português</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ru">Русский</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=zh">中文</a>
</div>

---

# TradingAgents: Multi-Agents LLM Financial Trading Framework

## News
- [2026-09] **TradingAgents v0.5.0** released with point-in-time integrity across every dated path, SEC EDGAR fundamentals served as filed, backtesting over a ticker and date grid, portfolio-aware runs, and current model lineups across every provider. See [CHANGELOG.md](CHANGELOG.md) for the full list.
- [2026-08] **TradingAgents v0.4.0** released with look-ahead / point-in-time fixes across FRED macro, social sentiment, and the decision-log memory; clearer decision signals; working CLI checkpoint resume; Trader price grounding; and the GPT-5.6 and GLM-5.3 models.
- [2026-07] **TradingAgents v0.3.1** released with correctness and stability fixes: Alpha Vantage look-ahead filtering, graph-router crash-safety, graph-shape-aware checkpoint resume, working crypto sentiment sources, a configurable LLM retry budget, Bedrock API-key auth, and Claude Sonnet 5 / Fable 5 support.

<details>
<summary>Earlier releases</summary>

- [2026-06] **TradingAgents v0.3.0** released with a verified data-access contract, an expanded provider registry (NVIDIA, Kimi, Groq, Mistral, Bedrock, and any OpenAI-compatible endpoint), FRED and Polymarket data vendors, a current-generation model catalog, and a CI gate.
- [2026-05] **TradingAgents v0.2.5** released with the grounded Sentiment Analyst, GPT-5.5 etc. model coverage, Qwen/GLM/MiniMax dual-region support, `TRADINGAGENTS_*` env-var configurability with API-key auto-detection, remote Ollama support, non-US alpha benchmarks, and ticker path-traversal hardening.
- [2026-04] **TradingAgents v0.2.4** released with structured-output agents (Research Manager, Trader, Portfolio Manager), LangGraph checkpoint resume, persistent decision log, DeepSeek/Qwen/GLM/Azure provider support, Docker, and a Windows UTF-8 encoding fix.
- [2026-03] **TradingAgents v0.2.3** released with multi-language support, GPT-5.4 family models, unified model catalog, backtesting date fidelity, and proxy support.
- [2026-03] **TradingAgents v0.2.2** released with GPT-5.4/Gemini 3.1/Claude 4.6 model coverage, five-tier rating scale, OpenAI Responses API, Anthropic effort control, and cross-platform stability.
- [2026-02] **TradingAgents v0.2.0** released with multi-provider LLM support (GPT-5.x, Gemini 3.x, Claude 4.x, Grok 4.x) and improved system architecture.
- [2026-01] **Trading-R1** [Technical Report](https://arxiv.org/abs/2509.11420) released, with [Terminal](https://github.com/TauricResearch/Trading-R1) expected to land soon.

</details>

<div align="center">

🚀 [TradingAgents](#tradingagents-framework) | ⚡ [Installation & CLI](#installation-and-cli) | 🎬 [Demo](https://www.youtube.com/watch?v=90gr5lwjIho) | 📦 [Package Usage](#tradingagents-package) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

> 🎉 **TradingAgents** officially released! We have received numerous inquiries about the work, and we would like to express our thanks for the enthusiasm in our community.
>
> So we decided to fully open-source the framework. Looking forward to building impactful projects with you!

## TradingAgents Framework

TradingAgents is a multi-agent trading framework that mirrors the dynamics of real-world trading firms. By deploying specialized LLM-powered agents: from fundamental analysts, sentiment experts, and technical analysts, to trader, risk management team, the platform collaboratively evaluates market conditions and informs trading decisions. Moreover, these agents engage in dynamic discussions to pinpoint the optimal strategy.

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> TradingAgents framework is designed for research purposes. Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, the quality of data, and other non-deterministic factors. [It is not intended as financial, investment, or trading advice.](https://tauric.ai/disclaimer/)

Our framework decomposes complex trading tasks into specialized roles.

### Analyst Team
- Fundamentals Analyst: Evaluates company financials and performance metrics, identifying intrinsic values and potential red flags.
- Sentiment Analyst: Aggregates news headlines, StockTwits, and Reddit chatter into a single sentiment read to gauge short-term market mood.
- News Analyst: Monitors global news and macroeconomic indicators, interpreting the impact of events on market conditions.
- Technical Analyst: Utilizes technical indicators (like MACD and RSI) to detect trading patterns and forecast price movements.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Researcher Team
- Comprises both bullish and bearish researchers who critically assess the insights provided by the Analyst Team. Through structured debates, they balance potential gains against inherent risks.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Trader Agent
- Composes reports from the analysts and researchers to make informed trading decisions, determining the timing and magnitude of trades.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Risk Management and Portfolio Manager
- Continuously evaluates portfolio risk by assessing market volatility, liquidity, and other risk factors. The risk management team evaluates and adjusts trading strategies, providing assessment reports to the Portfolio Manager for final decision.
- The Portfolio Manager approves/rejects the transaction proposal. If approved, the order will be sent to the simulated exchange and executed.

<p align="center">
  <img src="assets/risk.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

## Installation and CLI

### Installation

Clone TradingAgents:
```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
```

Create a virtual environment in any of your favorite environment managers:
```bash
conda create -n tradingagents python=3.12
conda activate tradingagents
```

Or with [uv](https://docs.astral.sh/uv/):
```bash
uv venv --python 3.12
source .venv/bin/activate
```

Install the package and its dependencies (`uv pip install .` with uv):
```bash
pip install .
```

### Docker

Alternatively, run with Docker:
```bash
cp .env.example .env  # add your API keys
docker compose run --rm tradingagents
```

After updating the repository, rebuild the image with `docker compose build`.

For local models with Ollama:
```bash
docker compose --profile ollama run --rm tradingagents-ollama
```

### Required APIs

TradingAgents supports multiple LLM providers. Set the API key for your chosen provider:

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export DEEPSEEK_API_KEY=...        # DeepSeek
export DASHSCOPE_API_KEY=...       # Qwen — International (dashscope-intl.aliyuncs.com)
export DASHSCOPE_CN_API_KEY=...    # Qwen — China (dashscope.aliyuncs.com)
export ZHIPU_API_KEY=...           # GLM via Z.AI (international)
export ZHIPU_CN_API_KEY=...        # GLM via BigModel (China, open.bigmodel.cn)
export MINIMAX_API_KEY=...         # MiniMax — Global (api.minimax.io)
export MINIMAX_CN_API_KEY=...      # MiniMax — China (api.minimaxi.com)
export OPENROUTER_API_KEY=...      # OpenRouter
export MISTRAL_API_KEY=...         # Mistral
export MOONSHOT_API_KEY=...        # Kimi (Moonshot)
export GROQ_API_KEY=...            # Groq
export NVIDIA_API_KEY=...          # NVIDIA NIM
export FRED_API_KEY=...            # FRED macro data (free, optional)
export ALPHA_VANTAGE_API_KEY=...   # Alpha Vantage
```

For Azure OpenAI, copy `.env.enterprise.example` to `.env.enterprise` and fill in your credentials.

For AWS Bedrock, install the extra with `pip install ".[bedrock]"`, set `llm_provider: "bedrock"`, configure AWS credentials (environment variables, `~/.aws/credentials`, or an IAM role) and `AWS_DEFAULT_REGION`, and use a Bedrock model ID, e.g. `us.anthropic.claude-opus-4-8-v1:0`.

For local models, configure Ollama with `llm_provider: "ollama"`. The default endpoint is `http://localhost:11434/v1`; set `OLLAMA_BASE_URL` to point at a remote `ollama-serve`. Pull models with `ollama pull <name>`, and pick "Custom model ID" in the CLI for any model not listed by default.

For any other OpenAI-compatible server (vLLM, LM Studio, llama.cpp, or a custom relay), use `llm_provider: "openai_compatible"` and set the endpoint via `backend_url` (or `TRADINGAGENTS_LLM_BACKEND_URL`), e.g. `http://localhost:8000/v1` for vLLM or `http://localhost:1234/v1` for LM Studio. The model is whatever your server serves. No key is needed for local servers; set `OPENAI_COMPATIBLE_API_KEY` when the endpoint requires one.

Alternatively, copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### CLI Usage

Launch the interactive CLI:
```bash
tradingagents          # installed command
python -m cli.main     # alternative: run directly from source
```
You will see a screen where you can select your desired tickers, analysis date, LLM provider, research depth, and more. Your previous run's answers come back as the defaults, so pressing Enter accepts them. The `TRADINGAGENTS_*` variables in `.env` still skip their step entirely.

### Markets and tickers

TradingAgents works with any market Yahoo Finance covers, using the exchange-suffixed ticker. Company identity and the alpha benchmark resolve automatically per market.

- US: `AAPL`, `SPY`
- Hong Kong: `0700.HK` · Tokyo: `7203.T` · London: `AZN.L`
- India: `RELIANCE.NS`, `.BO` · Canada: `.TO` · Australia: `.AX`
- China A-shares: Shanghai `.SS`, Shenzhen `.SZ` (e.g. `600519.SS` for Kweichow Moutai)
- Crypto: `BTC-USD`, `ETH-USD`

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

An interface will appear showing results as they load, letting you track the agent's progress as it runs.

<p align="center">
  <img src="assets/cli/cli_news.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

<p align="center">
  <img src="assets/cli/cli_transaction.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

## TradingAgents Package

### Implementation Details

We built TradingAgents with LangGraph to ensure flexibility and modularity. The framework supports multiple LLM providers: OpenAI, Google, Anthropic, xAI, DeepSeek, Qwen (Alibaba DashScope, international and China endpoints), GLM (Zhipu), MiniMax (global + China), OpenRouter, Ollama for local models, and Azure OpenAI for enterprise.

### Python Usage

To use TradingAgents inside your code, you can import the `tradingagents` module and initialize a `TradingAgentsGraph()` object. The `.propagate()` function will return a decision. You can run `main.py`, here's also a quick example:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())

# forward propagate
_, decision = ta.propagate("NVDA", "2026-09-01")
print(decision)
```

You can also adjust the default configuration to set your own choice of LLMs, debate rounds, etc.

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"        # e.g. openai, google, anthropic, deepseek, groq, ollama; openai_compatible covers any OpenAI-compatible endpoint (vLLM, LM Studio, llama.cpp, ...)
config["deep_think_llm"] = "gpt-5.6"      # Model for complex reasoning
config["quick_think_llm"] = "gpt-5.6-luna" # Model for quick tasks
config["max_debate_rounds"] = 2

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("NVDA", "2026-09-01")
print(decision)
```

See `tradingagents/default_config.py` for all configuration options.

### Concurrent runs

Each `TradingAgentsGraph` keeps a deep-copied configuration and activates it
only for that graph's run. Separate worker threads or async tasks can therefore
run graphs with different providers, languages, vendor chains, and storage
paths without replacing one another's dataflow configuration.

Use `TradingAgentsGraph.propagate()` for programmatic runs. If an integration
streams `graph.graph` directly, as the CLI does, keep the complete stream inside
`with graph.config_scope():` so every tool call observes the owning graph's
configuration.

### Fundamentals as filed

US company statements can come from SEC EDGAR, which records the date every figure was filed. A run dated in the past then reads the statements exactly as they stood that day: a fiscal year that has ended but has not been filed yet is not served, and a figure restated later still reads as first reported. Apple's 2008 total assets were filed as $39.6B and restated to $36.2B in 2010, so a run dated in between reads $39.6B.

EDGAR needs no account or API key. Add the vendor to the chain:

```python
config["data_vendors"]["fundamental_data"] = "sec_edgar,yfinance"
```

SEC asks callers to identify themselves and refuses requests that carry no contact address, so a default one is sent. Set your own so SEC can reach you rather than the project:

```bash
SEC_EDGAR_USER_AGENT="Your Name your@email.com"
```

It covers companies that file with the SEC, including foreign companies listed in the US. Anything else, such as Hong Kong or A-share listings, falls through to the next vendor in the chain. EDGAR's machine-readable filings begin in 2009, and a fourth quarter is reported as unavailable rather than derived, because filers publish it only inside the annual figure.

### Current holdings

By default the agents do not know what you hold, so their guidance is written for a reader who applies it to their own position. Pass a portfolio to have the trader, the risk analysts and the portfolio manager work against your actual book.

```python
from tradingagents.portfolio import PortfolioContext

portfolio = PortfolioContext.model_validate({
    "cash": 25000.0,
    "currency": "USD",
    "positions": [{"ticker": "NVDA", "quantity": 120, "average_price": 150.0}],
})
_, decision = ta.propagate("NVDA", "2026-09-01", portfolio=portfolio)
```

The CLI takes the same content as a JSON file: `tradingagents --portfolio my_book.json`.

An empty `positions` list means a flat book, which is different from passing nothing. A run without a portfolio is never treated as flat.

## Persistence and Recovery

TradingAgents persists two kinds of state across runs.

### Decision log

The decision log is always on. Each completed run appends its decision to `~/.tradingagents/memory/trading_memory.md`. On the next run for the same ticker, TradingAgents fetches the realised return (raw, and alpha against the instrument's regional benchmark), generates a one-paragraph reflection, and injects the most recent same-ticker decisions plus recent cross-ticker lessons into the Portfolio Manager prompt, so each analysis carries forward what worked and what didn't.

Override the path with `TRADINGAGENTS_MEMORY_LOG_PATH`.

### Checkpoint resume

Checkpoint resume is opt-in via `--checkpoint`. When enabled, LangGraph saves state after each node so a crashed or interrupted run resumes from the last successful step instead of starting over. The run view says whether it resumed a saved run or started fresh. Checkpoints are cleared automatically on successful completion.

Per-ticker SQLite databases live at `~/.tradingagents/cache/checkpoints/<TICKER>.db` (override the base with `TRADINGAGENTS_CACHE_DIR`). Use `--clear-checkpoints` to reset all of them before a run.

```bash
tradingagents --checkpoint           # enable for this run
tradingagents --clear-checkpoints    # reset before running
```

```python
config = DEFAULT_CONFIG.copy()
config["checkpoint_enabled"] = True
ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("NVDA", "2026-09-01")
```

## Evaluating decisions over time

One run gives one decision, which cannot tell you whether the system decides well. `run_backtest` runs the same pipeline over a grid of tickers and dates, writes to a decision log of its own, and scores the decisions whose holding window has since traded.

```python
from tradingagents.backtest import iter_grid, run_backtest, summarize
from tradingagents.agents.utils.memory import TradingMemoryLog

dates = iter_grid("2026-06-01", "2026-08-01", every_n_days=7)
result = run_backtest(["NVDA", "AAPL"], dates, config, selected_analysts=["market", "news"])
print(summarize(TradingMemoryLog({"memory_log_path": str(result.log_path)})).render())
```

From the CLI:

```bash
tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7
```

Each cell is scored on realized alpha against the instrument's regional benchmark, grouped by rating. Your own decision log is never written to, and re-running the same grid with `run_id=result.run_id` skips the cells that already ran, so an interrupted sweep continues where it stopped.

## Reproducibility

TradingAgents is LLM-driven, so two runs of the same ticker and date can differ. This is expected for a research tool built on language models, not a defect. The variation comes from a few distinct sources, and it helps to separate them.

Language model sampling is non-deterministic. Even at a fixed temperature, providers do not guarantee byte-identical output across calls, and reasoning models (the default GPT-5.x family, and any thinking-mode model) vary the most because their internal reasoning is itself sampled.

Live data moves. News, StockTwits, and Reddit return different content as time passes, so a run today sees different inputs than a run last week even for the same historical trade date. Pin the analysis date to hold the price and indicator window fixed, but the social and news sources still reflect "now".

To reduce variation you can lower the sampling temperature. Set `temperature` in your config (or `TRADINGAGENTS_TEMPERATURE` in `.env`); lower values make models that honor it more repeatable. The current curated models are reasoning-first and largely ignore temperature, so for tighter reproducibility name a non-reasoning model in your config, or in `TRADINGAGENTS_DEEP_THINK_LLM` and `TRADINGAGENTS_QUICK_THINK_LLM`. Any model ID your provider serves is accepted, whether or not the picker lists it.

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["temperature"] = 0.0
# Reasoning models ignore temperature. For tighter reproducibility, name a
# non-reasoning model in deep_think_llm / quick_think_llm.
```

What does not vary anymore: the analyzed company identity is resolved deterministically from the ticker before any agent runs, and the market analyst grounds exact price and indicator claims in a verified data snapshot. Earlier reports of "different companies" or fabricated price levels across runs are addressed by these two mechanisms.

Backtest results are not guaranteed to match any published figure. Returns depend on the model, the temperature, the date range, data quality, and the sampling above. Treat the framework as a research scaffold for studying multi-agent analysis, not as a strategy with a fixed, replicable return.

## Private local research workspace

The optional `platform` extra now includes a private, authenticated FastAPI
foundation for durable analysis jobs and owner-scoped results. The `web/`
application provides Markets, Analysis, Portfolio and Decisions workspaces,
served locally through `tradingagents-api` after a separate frontend build.
It uses saved evidence, not a live trading feed. See the
[local startup guide](docs/platform/local-web-startup.md) and
[web build and verification guide](web/README.md).

The local UI supports **English / Tiếng Việt** with a persistent VI/EN switch.
The current remediation candidate adds snapshot-bound indicator tools, explicit
daily session labels, deterministic return endpoints, readable Markdown reports,
saved-report charts and separate source/research/portfolio states. It retains
the original debate/manager graph. Final report quantities are compiled from
snapshot-bound references before protected bilingual presentation. The research
workspace separates setup, actual-event progress and report summary/price/history
verification views; processing completion is not report approval. See the [implementation and verification
ledger](docs/platform/research-remediation.md); local tests are not live-model
quality or release approval.
Completed runs lead with their saved report; the processing timeline remains
available in a collapsed disclosure. Active and failed runs keep their status
visible. Reports retain missing coverage and validation findings in the main view.
Decisions show review readiness and the explicit
approve/reject controls before the report, without opening technical details.
These controls do not relax eligibility: matching successful research, data
quality, deterministic policy checks and backend revalidation are still required.
Reports embedded in Decisions omit navigation back to that same decision;
the linked decision action remains available when reading Analysis.
New research offers English, Vietnamese or bilingual English–Vietnamese reports
(bilingual is the web form default). The language choice is recorded on each
run; changing the UI language never translates or overwrites saved analysis.
Bilingual generation can consume more output tokens and still needs human
translation/financial review. See [language behavior](docs/platform/bilingual.md).

The current platform layer also provides canonical instrument identity,
immutable normalized price series, vendor-neutral equity/ETF evidence,
reference-only NQ/ES context, BTC/ETH UTC snapshots, a deterministic large-cap
stock screener, transparent derived factors, and consistent data-health
classification. These services operate on explicitly supplied or previously
stored snapshots; this milestone does not select or configure a production
market-data vendor. The web now also offers **Prepare latest prices** using the
existing Yahoo/yfinance integration for AAPL, SPY/QQQ, cash indices and BTC/ETH.
It verifies five years of completed daily sessions using the original engine's
shared history window, saves immutable evidence, then
requires separate paid-AI consent. The price action itself does not ingest
news/fundamental/macro sources and is not a historical-vintage feed;
The existing financial-review step receives complete selected immutable source
records as untrusted evidence, in addition to the draft and numeric facts. This
does not add a model call but may increase input tokens; it does not prove that
all qualitative claims are entailed or remove the need for human review.
The same validated social count facts are available during compilation and
financial review. Count bindings render complete source-owned EN/VI statements
about the supplied sample and user labels, not price, market probability or
neutral absence. Publication and translation preserve their unit and scope;
unreferenced `percent`/`per cent` values also require valid financial bindings.
These checks do not establish general qualitative entailment or live acceptance.

NQ/ES preparation remains unsupported. The preparation form groups instrument,
research time and report language together, and offers **Choose saved sources**
to open and focus the evidence inspector. This shortcut does not collect data,
select evidence or authorize AI. Optional source actions remain independent.
See [data preparation](docs/platform/data-preparation.md).

The analysis form can also **Add recent headlines** from the existing
Yahoo/yfinance source as an independent, optional, owner-scoped news snapshot.
The seven-day feed is explicitly non-exhaustive and current-vintage only;
empty, malformed or unavailable news cannot be selected as evidence. This
headline action does not fetch discussions or make a price-only or
market-plus-news report comprehensive. An owner-approved, separate **Add SEC
fundamentals** action now prepares AAPL US GAAP companyfacts with filing dates
and immutable provenance using the existing SEC EDGAR adapter. It requires a
real `SEC_EDGAR_USER_AGENT` contact in the ignored local environment; no key or
AI tokens are used for preparation. SEC facts are not a complete company profile,
and their current retrieval cannot be backdated. CLI vendor defaults are unchanged.
Final SEC quantities use application-owned sentences for the reported metric,
period and USD-million/per-share unit, rather than a model-written scale label.
The bilingual presentation protects complete verified fact sentences as well
as numbers. These structural checks do not prove qualitative reasoning or
translation quality; human review is still required.
NQ/ES automatic preparation remains unsupported.

The draft form offers independent **Add StockTwits discussions** and **Add Reddit
discussions** actions using the repository's original public endpoints and symbol
aliases. No API key or AI tokens are needed. Each feed retains every eligible
returned post's full text from the original seven-day window, with publication,
edit and current retrieval provenance; it is a non-exhaustive sample, not a
historical archive or market probability. Author/account profiles and inferred
engagement are not stored. StockTwits user labels are not verified events, and
unlabeled posts are not neutral sentiment; Reddit does not supply sentiment labels.
Authenticated preparation appends immutable owner evidence, audits distinct
failed feeds and never starts AI. Selecting one source preserves the other and
resets paid consent; oversized selections require review, not silent removal.
Bounded streamed transport and supervised child lifetime refuse late, malformed,
ambiguous or oversized results rather than truncating them. Original Sentiment
research receives full retained text and source-count facts, with missing-feed
coverage disclosed. CLI sources/defaults and all research/debate, financial,
translation, risk and human-approval gates remain unchanged. NQ/ES refuse this
preparation. Local fixtures do not prove live reachability, exhaustive social
coverage, source entailment or investment quality; dated receipts state the scope.

The draft analysis form now also offers **Add economic context** using the existing
FRED key/endpoints and immutable macro snapshots. It requires `FRED_API_KEY` on the
server, never a key in the browser. Explicitly choose a series and history window;
365 days matches the original macro default and can be extended to 36,525 days.
No AI call is made during preparation. Headline and other indicator selections
are retained when replacing the same dataset/series, with an explicit 16-source
selection limit rather than silently dropping evidence. Economic context and
headlines have separate coverage disclosures even though both enter News research.
The collector and storage reuse the existing configured FRED host/key,
accept an explicit series/window, retain every returned observation including
missing values, and pin metadata/values to the previous fully elapsed Chicago
vintage day. Native-frequency observation freshness is checked separately from
vintage/retrieval freshness. This day-level pin is not an exact release time or
complete macro coverage; retrieval is never backdated. Failure snapshots remain
auditable but ineligible. Validated stored FRED snapshots can now join the news
analyst through read-only full-history paging and exact native-unit, observation-
label, denominator and vintage-bound facts. Application-owned EN/VI statements
keep these meanings intact without changing research/debate roles, repairs,
deterministic risk or human approval. Macro-only input explicitly lacks headlines.
Current preparation authenticates owner/CSRF, reuses only recent eligible matching
series/window/vintage snapshots, spaces repeated requests and bounds streamed
responses/child output. A supervised 75-second acquisition deadline kills/reaps
unfinished children; late or invalid results are withheld. Failure snapshots cannot
authorize research. Oversized data is rejected, never silently shortened. The CLI
request/defaults remain unchanged. Local evidence is not live FRED availability,
comprehensive macro coverage or financial/editorial acceptance; see
[data integrity](docs/ops/data-integrity.md) and dated acceptance receipts.

The analysis layer now connects those snapshots to an `AnalysisEngine`,
asset-specific graph profiles, strict structured narrative, source-linked
evidence, deterministic portfolio/risk checks, and an audited owner-approval
lifecycle. Invalid, stale, incomplete, or unattested output remains `REVIEW`.
LLMs cannot choose portfolio weights or approve decisions. NQ/ES remain
reference-only; supported crypto analysis is BTC/ETH.

The candidate API provides owner/CSRF-protected
`POST /api/v1/runs/{id}/continuation/prepare` and
`POST /api/v1/runs/{id}/continuations`. Preparation derives the original
checkpoint identity and remaining allowance without calling a model. Reservation
requires its current observation hash, an idempotency UUID, literal confirmation
and acknowledgment of retained allowance, unknown provider cost and unvalidated
prior research. No client codec/config is accepted. Both responses explicitly
state `dispatch_enabled: false`: HTTP does not directly dispatch a model and
ordinary worker startup does not enable continuation polling. An operator can
explicitly enable polling with `tradingagents-worker --continuations`; ordinary
queued jobs take priority. Browser continuation controls are not integrated yet.
Reservation does not approve a decision or rewrite history.
Local/native API and full-candidate acceptance are recorded separately in HANDOFF.

The trusted worker operation can rebuild a reserved continuation's actual SDK
identity without browser credentials, claim once, retain original allowance,
restore the original graph and publish a separately fenced report. Uncertain
lease renewal blocks callbacks/publication; uncertain ACKs are not automatically
retried. Opt-in polling consumes durable reservations without stored browser
credentials. A preclaim preparation refusal is recorded separately and excluded
from subsequent polls across restart; it cannot grant a claim or retry. After a
claim, uncertainty never requeues or replenishes the original allowance.
Authenticated `GET /api/v1/runs/{id}/continuations/{execution_id}` reads validated
state without SDK construction; the corresponding `POST .../cancel` requires
CSRF/Origin and cancels a reservation or requests an active attempt's stop.
Completed status requires the full completion/report reader, not a database flag.
Candidate `GET /api/v1/runs/{id}/continuations` discovers owner-scoped attempts
after browser refresh, with descending attempt pagination (`limit` up to 50,
`before_attempt`) and explicit `has_more`. State includes attempt and report/
evidence/decision IDs only after the full completion reader verifies them. These
IDs are read links, not approval authority. The browser journey is still pending.
Migration `0018_preparation_refusals` is additive and requires an explicit operator
migration with a consistent private DB/artifact backup; worker startup never
migrates. Downgrading removes refusal receipts and must not be used to enable a
retry. Browser controls and live operational acceptance remain unfinished.
Synthetic native parity is not live financial/editorial proof.

Durable snapshot jobs retain private, immutable working notes when each graph
role returns reader text. Notes bind to the run, snapshots and declared config,
are always **unvalidated**, and cannot authorize portfolio approval. Prompts,
raw messages, model-reasoning fields and executable portfolio fields are not
retained in these notes. A cancellation or lost worker lease prevents new writes.
Notes are available on demand in the web artifact reader with a mandatory
unvalidated/nonapproval warning; interface language changes preserve original
stage text without calling AI. Graph resume remains unfinished. This does not enable the CLI's
checkpoint path for web jobs, increase execution allowances, skip any role or
recover text that was never saved by an older failed run.

Local stopped-attempt fixtures now lose an ACK after the first returned market
report's pending writes are durably committed. The supervisor actually stops
and reaps that child; a new original child restores the latest validated tuple
using the retained observer. Prefix plus continuation prompt/model trace and
final published fields match uninterrupted EN/VI/bilingual/invalid-translation
fixtures, without repeating the completed model call or rewriting old rows.
Killed SDK cleanup remains unknown; this is not abrupt-parent-crash recovery,
authenticated consent, linked execution or live financial acceptance.

The internal supervisor can optionally transfer restricted checkpoint bytes to
a new spawned original engine/recorder after parent thread/fingerprint/context
validation and revalidation before spawn. The child independently checks its
initialized original graph fingerprint before restore; database/lease/commit
remain parent-only. Synthetic new-child fixtures compare continuation traces
and outputs while debiting all first-attempt usage with the retained observer.
These mechanism tests are not authenticated consent, transactional execution
identity or permission to replay historical runs; default worker/API recovery
and live acceptance remain disabled/unverified.

The internal original-context recorder can now import restricted checkpoint
bytes after checking the initialized graph fingerprint and original observer
allowance. The paired snapshot graph hook invokes the original scheduler with
`None` under original config scope, sync durability and callbacks. Synthetic
recorder/engine fixtures compare continuation prompt traces and complete outputs
with an uninterrupted run, preserving old checkpoint rows. No new observer is
constructed here. New-child transport, consent, default worker/API recovery and
live acceptance remain unverified and disabled.

An internal committed saver restore method now imports a reviewed tuple only
into an empty saver, bound to the expected thread and codec fingerprint. It
preserves native versions, routing and completed pending writes without
republishing old history; malformed/mismatched/repeated or partial imports
poison the saver. Native graph fixtures exercise this method, but new-child
restore, consent and default worker/API recovery remain unverified and disabled.

The draft recovery work includes a restricted JSON checkpoint codec, not an
enabled web resume feature. It removes messages from state/start/pending writes,
preserves native channel versions/routing and rejects unknown fields, incompatible
formats or oversized input without truncation. Local synthetic tests restore
into a fresh saver, including completed pending writes, without repeating model
calls. Full fingerprint construction, owner/lease-fenced durable storage and
explicit continuation consent remain unfinished; a caller-supplied digest alone
is not recovery authorization. See the
[recovery implementation contract](docs/platform/research-recovery-contract.md).
An internal recovery-fingerprint builder now validates original run/request and
snapshot identities, hashes verified source manifests, full portfolio/policy
content, effective graph configuration/options, supplied resolved-client bindings,
package source bytes and installed dependency versions. It returns only a digest;
it does not authenticate the caller, attest supplied SDK bindings, save a
checkpoint or authorize paid continuation. Worker integration remains unfinished.
An internal initialized-client adapter reads actual endpoint, timeout/retry and
model options from reviewed OpenAI-compatible classes (including MiniMax), without
invoking models or reading SDK authentication headers. It rejects declared custom
headers/query/transports and unreviewed classes. This is not a complete transport
attestation: worker-controlled construction, SDK mutation protection, other SDK
adapters and durable recovery remain unverified and are not enabled.
An internal initialized-identity preflight now constructs the original graph
and reviewed SDKs in a separate spawned process. LangChain default HTTP pools
can be shared between fresh SDK roots, so it never closes clients in the worker
or clears its transport caches. It uses bounded JSON inputs/replies, the original
observer's wall-time/cancellation/lease checks, a separate 45-second preparation
ceiling and child reaping. Only a sanitized fingerprint/node list is returned
after SDK cleanup and clean child exit; no model call or continuation permission
is granted. Parent credentials are not serialized and no supplied client/factory
is accepted. Default per-run recording, owner continuation and live acceptance
remain unfinished. The draft default local worker now attempts per-run recording
for snapshot jobs: reload original owner-scoped Decimal book/policy/risk bytes,
retain the entered-attempt uncertainty fence and same observer, prepare actual
identity, then construct a fresh supervisor with original parent-fenced commits.
No shared template mutation, recording fallback, automatic retry/resume or new
approval authority. Legacy tools/CLI stay unchanged; explicit engine injection
is a testing seam, not production recording authority. Current integration QA
has two preparation-deadline errors; default graph/owner journey and a new full
baseline remain unverified. Do not infer acceptance from the prior preflight gate.
Private checkpoint persistence now has an internal append-only database store
and migration `0011_research_checkpoints`, separate from report artifacts. It
validates restricted JSON, binds owner/run/job, commits under the existing
publication lease/cancellation transaction, and returns an ACK only after
commit. Fixture reopen/rollback/fencing checks do not establish native saver,
child bridge, crash recovery, explicit consent or live acceptance; none is
enabled. No existing owner database was migrated during this checkpoint.
An internal native saver now commits filtered JSON for checkpoint/pending-write
updates and refuses reuse after a failed or mismatched ACK. It requires native
LangGraph `durability="sync"` to wait before advancing; default async durability
is not a publication fence. Local synthetic tests restore committed SQLite
bytes into a fresh saver across all 17 interruption boundaries without changing
downstream prompts, model-call traces or validated results. This is not a
separate-process crash test or enabled worker resume; bridge integration,
trusted construction, consent/accounting and live acceptance remain open.
The supervisor now has an internal opt-in checkpoint RPC: only non-secret
identity reaches the child; codec validation, private commit callback and lease
remain parent-owned, with cancellation/deadline checked before ACK. Incomplete
setup or an engine without an explicit recording capability is rejected.
The default AnalysisEngine/worker does not enable recording or resume. Native
fixture graphs exercise this RPC, including parent crashes before/after commit
while the child waits; production construction, restore/accounting/consent and
bounded DB-lock behavior still require acceptance.
Checkpoint transactions now use a local lock-wait budget (default five seconds,
optionally shorter): SQLite busy_timeout is restored before pool reuse;
PostgreSQL uses transaction-local lock_timeout/statement_timeout but remains
unverified live. Real SQLite writer/commit contention fails without ACK or a
second unbounded lease query. This is a per-operation lock/statement bound, not
a hard whole-transaction, pool/connect/network or disk-stall deadline; defaults
for other database sessions and model timeouts are unchanged.
The original snapshot graph now exposes an internal paired saver/canonical
run-thread hook. It compiles a local invocation graph and explicitly uses sync
durability without replacing the instance/CLI graph, including on failure.
Native spawn fixtures use this hook rather than replacing graph.invoke. It is
not selected by default AnalysisEngine/worker, does not restore saved state,
and does not supply fingerprint trust, consent or retained accounting.
An internal initialized-graph guard now derives the full original recovery
fingerprint from this graph's actual reviewed sync SDK clients, checking exact
effective config, selected roles, declared model names and the construction-time
digest of snapshot readers. Mismatches fail before invocation without printing
inputs. Real graph/SDK tests use synthetic credentials and forbid network/model
calls. This is still not complete transport/closure-mutation attestation or an
enabled worker/owner continuation path.
AnalysisEngine now accepts an internal opt-in SnapshotRecorder with the original
run context, expected full fingerprint and trusted fenced commit callback. It
requires the original ResearchObserver/allowance, recomputes identity from its
newly initialized actual graph and refuses mismatch before invocation. It then
passes a restricted committed saver/run thread to the native sync snapshot hook.
Arbitrary recorder types/graph factories and non-snapshot requests are rejected;
default engine/worker and CLI behavior is unchanged. This direct engine wiring
does not enable supervised worker recovery, restore history or grant consent.
Native fixtures now exercise this actual engine/recorder path with initialized
SDK identity and synthetic responses: all four analysts, two debate/risk rounds,
EN/VI/bilingual and invalid VI preserve baseline prompt/call/stage traces and
non-message results. Private SQLite bytes reopen with original owner/run/hash
and no raw messages/reasoning. Synthetic methods do not prove SDK callback usage,
billing, live financial quality or supervised worker recording/recovery.
Recorder allowance validation can now use the exact internal checkpoint-enabled
child bridge: parent matches original limits/fingerprint/thread and checks its
existing clock/cancellation/lease before ACK. Child creates no new allowance or
clock. Wrong setup or non-True ACK fails closed. This is internal RPC groundwork,
not original-context transfer, worker activation, continuation consent or resume.

The analysis handler durably marks entry into the research engine. Caught
engine/publication failures do not automatically replay the whole paid run;
expired leases with execution evidence require review, even if attempts remain.
Provider charges may be unknown. Pre-engine preparation retries and bounded
SDK/schema repairs are separate and unchanged. Storage-only finalization of an
already committed report/decision pair may retry without a model call; missing,
partial or corrupt saved outputs fail closed instead of re-entering the engine.
This is not automatic resume. Snapshot-run API callers can explicitly select
immutable `execution_limits` (`wall_seconds`, `model_calls`); these bind to the
run/config hash/job and worker observer. Omitted limits preserve the legacy
30-minute/128-call defaults without rewriting history. `/analysis-configuration`
discloses those defaults and `cooperative_boundaries`: already-running requests
can overrun the allowance. SDK timeout/retries are unchanged. The web form offers
30 minutes (default) or 60 minutes, resets paid-call consent when changed, and
binds the selection to each new snapshot run. Processing displays recorded
limits without inventing them for legacy runs. The default web worker now runs
snapshot research in a spawned process; the parent monitors the same allowance,
cancellation and lease checks while SDK requests block, then terminates/joins
the child before returning or publishing. SDK retry/backoff and slow response
reads cannot leave a detached local call after that termination. Safe graph
resume remains unfinished; accepting a larger
allowance does not shorten or skip graph roles or cap provider charges.
The model-call cap counts logical LangChain invocations, not SDK-internal
retries. Receipts explicitly leave provider attempt counts unknown; returned
usage is preserved even after the allowance expires. Concurrent model starts
share atomic admission. The CLI, legacy live-tool runs and explicitly injected
engines retain their existing contracts. Reports record actual supervision mode;
configuration disclosure describes the default worker, not proof that a running
worker was upgraded. Stopping local processing does not stop or refund remote
provider work. Process startup/cleanup and scheduler latency are not zero.

Model observers now emit cumulative `model.usage` counters before a logical call
as well as after completion/error. The worker's existing lease-fenced event
transaction commits the reservation before provider admission; failed emission
or deadline/cancellation during that commit stops admission. New events include
original execution limits and observed monotonic elapsed seconds. An unfinished
reservation remains `incomplete`, even if earlier calls supplied usage. No
prompts, raw errors, provider reasoning or keys are included. Elapsed observations
are lower bounds at event time, not exact crash duration or provider billing.
This does not enable recovery, recreate missing history or reset any allowance;
cross-attempt accounting/consent and live financial acceptance remain unfinished.

An internal read-only accounting reader now validates an owner-scoped bounded
event prefix, takes the latest cumulative counters per attempt, and aggregates
reported tokens/reservations without double-counting earlier receipts. Missing
or legacy attempt evidence yields unavailable totals, not zero usage. Invalid
limits, counters, sequence gaps and unknown fields fail closed.
Token growth without an additional usage-bearing completion and nonfinite
aggregate elapsed also fail closed. Its high-water
sequence is an observation, not a transaction fence; elapsed stays a lower bound.
The reader is not wired to browser consent, worker continuation or budget
admission and cannot authorize resume or infer actual provider cost.
Observations now retain original owner/run/config/allowance identity. An internal
recheck compares the full observation against freshly loaded evidence and rejects
changes; it is not a database lock, consent token or check-then-dispatch fence.
The supervised parent can append a final usage observation only after child
reaping and reader shutdown. When every observed attempt has that boundary, the
reader retains an upper bound on local supervised elapsed time. Missing stop
evidence remains unknown, not inferred from run status. This does not bound
remote provider duration/billing or authorize continuation; old rows are untouched.
A read-only allowance observation subtracts all durable logical starts and the
local elapsed upper bound from the original run limits. Missing time remains
unknown; already exhausted limits remain blocked. A positive arithmetic result
is not consent or admission and cannot reset caps or waive unreported usage.
An internal retained-observer builder reloads and compares original accounting,
refuses stale/unknown/exhausted observations, and debits prior time/calls at
admission while emitting only current-attempt usage. It is not wired to worker
or browser continuation and does not authenticate consent or restore a graph.
The opt-in supervised restore path now requires that builder's original
owner/run/config-bound, unused observer. Fresh/copied observers, reset prior
debits, changed caps/clock/callbacks and already-used attempts are rejected
before spawning. Its original clock still governs the remaining deadline.
This local construction binding is not an authenticated consent token, a DB
writer fence or authority to continue a terminal historical run; default
worker/API recovery remains disabled.

An internal continuation consent store now records a separate immutable
research execution identity after locked owner-session/CSRF authentication,
explicit confirmation and transactional reloading of the latest checkpoint,
original terminal job/run and complete accounting prefix. Unknown/exhausted
allowance, changed evidence, duplicate reservations and corrupt receipts fail
closed. Disposable SQLite and PostgreSQL stopped-run/idempotency and writer-race
fixtures are covered by dated exact-source receipts; these are not browser consent
or private-runtime rollout evidence.
Migration `0012_research_continuations` is additive and has only been applied
to disposable tests. No old run/job/error/checkpoint is changed, no token/email
is copied into the consent record and no model is invoked. This is NOT an API
resume endpoint, queued execution, final source/client attestation or financial
approval. The separate linked worker/default dispatch and browser journey still
need implementation and verification; an execution ID is not a bearer
permission or a fresh budget. Do not apply migrations to private history
without the documented backup/owner rollout procedure.

The internal linked-execution store additionally allocates that consent identity
once into a separate private `0013_research_executions` lease record, not a new
run or a default worker job. It rechecks authenticated owner/CSRF and the full
original checkpoint/accounting observation before allocation and claim. One
worker receives a hashed-token fence after commit; competing/expired/lost-ACK
claims cannot reset the attempt. Renewal retains its original claim-time deadline
minus all previously observed elapsed time. Cancellation of an unclaimed
allocation is terminal; cancellation of a leased allocation stays requested
until supervised termination is actually established. Expiration requires review,
never automatic requeue or an invented zero-cost stop. No new research event,
checkpoint, report, decision or model call is produced by these methods.
Default API/worker/CLI do not consume this table. An internal
`LinkedPublicationContext.prepare` now constructs a retained observer and
transactionally rechecks consent before recording one parent entry. Linked
usage/stage events and private checkpoints are lease-fenced in their own
commit transaction, including a final expiry check. Additive `0014` actor links
preserve the original job/run and old event/checkpoint bytes; new checkpoints
use the linked attempt, not the terminal job's attempt. Prior and current
logical starts share the original cap; elapsed includes claim/prepare time and
unknown provider cost stays unknown. A lost entry ACK cannot re-enter. The
trusted stop hook is accepted only from that bound observer under a valid lease;
cancelled/expired late stop remains unknown, never a refund.

The internal terminal-original-context loader now preserves the complete failed/
cancelled manifest, including completion and errors, while the ordinary recording
context continues to reject terminal manifests. It reloads owner-readable source
bytes, source-row/manifest integrity, the original portfolio/policy and pinned
checkpoint under the linked parent fence, again before dispatch. No live source
fallback, new observer, budget reset or original-thread relabeling is allowed.
Additive `0015_linked_dispatch` records one consumed dispatch before constructing
the child; a lost committed ACK cannot respawn it. The private child receives JSON
and checkpoint bytes, never a DB/lease nonce/session/callback. Synthetic native
spawn fixtures compare interrupted prefix + restored suffix to the original
uninterrupted EN/VI/bilingual flow, including invalid-VI handling. These are local
mechanical proofs, not live provider/cost or financial/editorial acceptance.
An opt-in parent `LinkedResultPublisher` now retains allowlisted stage reader
artifacts with execution actor links and, only after a returned result, clean
child exit/reaping and durable local stop accounting, atomically appends the
ordinary report/evidence/risk candidate plus a separate `0016` completion receipt.
The ordinary handler and linked publisher share the same report projection and
decision pipeline; no financial/translation/risk gate is removed. The returned
linked child must exit cleanly within the retained deadline; slow cleanup is
polled with cancellation/lease checks, not terminated after a fixed one second.
No new budget or model call is granted. The original
FAILED/CANCELLED run/job remains immutable. Missing/invalid structured research
still becomes REVIEW; an existing owner risk input still determines weights.
An owner-scoped integrity reader can recover a committed receipt after lost ACK
without models or a live lease. Completion blocks later linked publication,
checkpoint writes, heartbeat or cancellation; automatic expiry maintenance does
not rewrite a committed output marker. It is not an approval or cost/refund claim.
Default continuation dispatch stays disabled. The existing authenticated owner
transition route now accepts an integrity-verified linked completion as proof of
completed research while preserving the original FAILED/CANCELLED run. Approval
still requires the exact human owner, source bytes/evidence, deterministic risk
replay, policy version and append-only lifecycle; a receipt alone grants no
approval. Candidate payload/hash remains immutable, with current status projected
from lifecycle events. Missing/corrupt approval receipt is refused. Every linked
lifecycle event, including review/reject/expire, is rejected before writing if
its timestamp precedes completion; a refusal does not poison readable history.
Ordinary successful-run approval is unchanged. An internal `0017` local-stop
receipt separately records a real joined child and closed pipe reader, including
cancel/expiry when normal publication is refused. Private original dispatch
identity and accounting bindings are verified; no checkpoint/report/decision
write is allowed through this path. It does not change original allowance or
unknown provider cost, claim remote work stopped, authorize another call or
rewrite old root/job/event history. Lost committed stop ACK can be resolved by
an owner-scoped integrity reader without a model or live lease. Default dispatch
remains off; missing/corrupt stop facts remain unknown. Multi-continuation,
all late-stop/crash/expiry boundaries and the default continuation API/UI journey
remain unfinished; local API tests are not live/browser acceptance.

Install with `pip install ".[platform]"`. After applying the documented
migrations, `tradingagents-worker` processes durable research jobs using the
same private database and artifact root as the API. See
[analysis engine and worker setup](docs/platform/analysis-engine.md).

An immutable owner-scoped ledger can replay recorded cash/position events and
value holdings from verified price snapshots. Historical evaluation can persist
and verify decision-level returns against calendar-aligned benchmark snapshots.
This is reproducibility of recorded inputs/results, not proof of historical
model knowledge or portfolio performance. See [ledger](docs/platform/portfolio-ledger.md),
[risk](docs/platform/risk-engine.md), [approval](docs/platform/decision-lifecycle.md),
and [historical evaluation](docs/platform/historical-evaluation-v2.md).

The UI supports saved watchlists, price/benchmark charts, screening history,
queued research, reports and evidence, persisted portfolio valuations, and
explicit decision review. Reloading data does not ingest new prices or call a
model. A completed research run is not a valid or approved investment conclusion.
No portfolio simulator, broker connection, order execution,
or autonomous trading path is included. See `docs/platform/api.md` and
the contracts under `docs/platform/` for the current runtime and data
boundaries.

## Contributing

Contributions are welcome: bug fixes, documentation, and feature ideas; past contributions are credited per release in [`CHANGELOG.md`](CHANGELOG.md).

## Citation

Please reference our work if you find *TradingAgents* provides you with some help :)

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```
