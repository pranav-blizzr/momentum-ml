# momentum-ml

Strategy detectors (HOD break, VWAP break-retest-push, micro pullback) and a LightGBM setup-scoring model for `tradingbot`. Built and validated on the MacBook, then installed into `tradingbot` on the Windows bot computer as a wheel. **This repo never connects to a broker, never places orders and never streams live data.**

Plans: `docs/porting-plan.md` (roadmap in §0) and `docs/build-guide.md`.

## Setup

```bash
cd ~/dev/momentum-ml
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements/train.lock.txt
cp .env.example .env && chmod 600 .env      # then fill in values
pytest
```

## Project rules

### Accounts and machine

1. Nothing in this repo connects to Interactive Brokers (`ib_insync`, `ib_async`, `ibapi`, TWS, IB Gateway). Never log in to IB on this machine with the bot's username: it can disconnect the live bot.
2. Market data providers (Massive, Benzinga, others): historical REST endpoints only, never websocket/streaming. Bulk pulls outside 04:00–20:00 ET on US trading days.
3. Databento: check size and cost (`client.metadata.get_billable_size` / `get_cost`) before every download.

### Library purity — `src/momentum_ml/` *(enforced by `tests/test_library_rules.py`)*

4. No broker or data SDKs, `sqlite3`, network libraries, `dotenv`, `asyncio`, threads, or research packages (`pandas`, `polars`, `sklearn`…).
5. No file I/O, no reading the clock (`time.time()`, `datetime.now()`), no environment variables, no `print`. Time comes only from the data's `ts_ns`.
6. Synchronous and deterministic: the same input stream always produces the same output.
7. Runtime dependencies: `numpy` and `lightgbm` only.
8. `contracts.py` is the boundary with `tradingbot`. Any change bumps `CONTRACT_VERSION` and needs the bot's adapter updated in the same release.

### Porting from the bot

9. Tick filtering, bar building, volume, VWAP and ATR are **ported from `~/dev/tradingbot-reference/`, not redesigned**. Each ported function's docstring names its source file and function.
10. If the bot's logic looks wrong, note it and keep matching the bot. Fix it later in both places together.
11. `~/dev/tradingbot-reference/` is read-only: never modify it, run it or import from it.

### Data and validation integrity

12. Every feature must be computable at the setup's trigger timestamp. No look-ahead.
13. Split by date only (walk-forward with embargo). Never random splits.
14. Frozen test period: `<fill in when chosen>`. Do not look at it until the final evaluation.
15. Never loosen a golden-test tolerance, edit a fixture, or skip a test to make tests pass. Investigate the mismatch.
16. Promotion gates (build guide §8.2) are written down before results are seen and not changed afterwards.
17. Labels include slippage and commissions; ambiguous stop/target ordering resolves to the stop.

### Secrets and environment

18. API keys live only in `.env` (never committed). Research code reads settings through `training/paths.py`.
19. Python 3.12 in `.venv/`. `requirements/inference.txt` pins `numpy==2.4.4` (the bot's version) and `lightgbm`; change them only deliberately, alongside the bot.
20. After adding a research package: `pip freeze > requirements/train.lock.txt` and commit.
21. Run research scripts from the repo root as modules: `python -m training.<script>`.

## Layout

```
src/momentum_ml/   packaged library (rules 4–8)
training/          datasets, labelling, training, reports   (not packaged)
replay/            replay runner                            (not packaged)
tools/             utilities, e.g. snapshot_live_db.py      (not packaged)
tests/             pytest; tests/fixtures/ holds golden sessions
docs/              porting-plan.md, build-guide.md
data/, models/, dist/, mlruns/   git-ignored
```

## Commands

```bash
pytest                         # all tests, including the library rules check
ruff check . && ruff format .
python -m training.<script>    # research scripts
python -m build --wheel        # release builds only (porting plan §10)
```

## Before each commit

- `pytest` passes and `ruff check .` is clean
- `git status` shows no `.env`, data or model files
- Any change to `contracts.py`, pins, fixtures, tolerances or gates is intentional and noted in the commit message
