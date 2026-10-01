# Change Data Management Service

Prototype CDMS for inventory product changes, built with FastAPI and PostgreSQL.

## Architecture

The project uses a small Clean Architecture structure to keep inventory change
rules independent from FastAPI, HTTP, and PostgreSQL. `InventoryPort` and
`ChangeRepository` are application boundaries, so the scheduled use case can be
tested with an in-memory repository and later connected to other data sources.

The current flow is:

```text
Fake Inventory -> HttpInventoryClient -> SyncInventory -> InventoryChange -> PostgreSQL
```

Business logic is kept in the domain entity and application use case:

- `InventoryChange` computes a deterministic SHA-256 hash of product data.
- `SyncInventory` validates product identity and submits each state to the repository.
- PostgreSQL enforces `UNIQUE(product_id, data_hash)`; atomic
	`INSERT ... ON CONFLICT DO NOTHING RETURNING` prevents duplicate states under
	concurrent syncs and reports whether a row was actually inserted.

The assignment defines scheduled polling, webhooks, and Excel uploads as
independent ingestion mechanisms. Currently, only scheduled polling is
implemented.

### Webhook Idempotency Plan

Webhook delivery can be retried, so product-state deduplication alone is not
enough to identify a repeated callback. When webhook support is implemented, it
will record each callback's `event_id` in a separate `processed_events` table:

```text
processed_events
- event_id PRIMARY KEY
- processed_at
```

The handler will insert the event record and its product changes in one
transaction. A duplicate `event_id` will be acknowledged without processing the
event again; failures will roll back both the event record and its changes.
This table and webhook transaction are planned, not present in the current
source. The current `UNIQUE(product_id, data_hash)` constraint only prevents
storing the same product state twice during scheduled polling.

## How to Run

Requirements: Docker Compose. Configure `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD` in `.env`, then start the services:

```bash
docker compose up --build
```

The CDMS polls the fake inventory service every 10 seconds. Stop with
`Ctrl+C`; use `docker compose down` to stop and remove the containers.

## API Docs

FastAPI's interactive API documentation is available at
[`http://localhost:8000/docs`](http://localhost:8000/docs); ReDoc is at
[`http://localhost:8000/redoc`](http://localhost:8000/redoc).

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | CDMS health check |
| `GET` | `/changes` | Latest 50 stored changes, newest first |
| `GET` | `http://localhost:8001/products` | Fake inventory catalog and current states |

There are no webhook or Excel upload routes in the current source.

## Test Results

Run the spike and concurrent-sync tests:

```bash
poetry run pytest -q
```

Without a test database, the current result is `3 passed, 1 skipped`. The
PostgreSQL race test is opt-in and requires a dedicated database whose name ends
in `_test`; it cleans only rows created under a unique test namespace. For
example:

```bash
CDMS_SPIKE_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/cdms_test' \
poetry run pytest -q
```

With the dedicated test database configured, the verified result is `4 passed`.

## Implemented vs Not Implemented

**Implemented**
- Scheduled inventory polling from the local Faker-based emulator.
- Hash-based change history with database-enforced duplicate prevention.
- Health and recent-changes read APIs.
- Synthetic spike and concurrent scheduled-sync tests, including an opt-in PostgreSQL test.

**Not implemented**
- Receiving inventory changes through a webhook, including `event_id` deduplication.
- Excel upload API and parsing workflow.
- Production-scale load testing with webhook and Excel traffic.

## Lessons Learned

- Duplicate meaning depends on business semantics. This prototype stores each unique product state, not a full chronological audit log; a state that returns later is not stored twice.
- Scheduled polling, webhooks, and Excel should share change rules while keeping their ingestion paths separate.
- Webhook retries will need `event_id` deduplication and an atomic transaction with product changes; this remains planned work.
- `InventoryChange` still computes a deterministic data hash. A read-before-write hash check can race, so PostgreSQL's unique constraint and atomic `ON CONFLICT ... RETURNING` decide whether the state was inserted.
- Spike results depend on realistic data volume; the default emulator's 10 products are only a smoke-test dataset.

## AI Usage

GitHub Copilot was used to assist with implementation
and test drafts, debugging, and documentation. The candidate consider clean code architecture, reviewed and
modified generated suggestions, selected the final design, ran the tests, and is
responsible for the delivered code.

## Demo Guide

1. Start the stack with `docker compose up --build`.
2. Open `/docs` and call `GET /health`.
3. View the source states at `http://localhost:8001/products`.
4. After a scheduled poll, call `GET /changes` and show the stored state and hash.
5. Repeat after the fake inventory mutates products to show change history.
6. Run `poetry run pytest -q` to demonstrate spike and concurrent-sync coverage.
