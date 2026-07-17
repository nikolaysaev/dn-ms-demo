# CartAssist Chatbot Demo Page

Minimal white static page for demonstrating the chatbot against the supplied product database.

## Files

- `index.html` - demo storefront with platform widget embed and direct API test mode.
- `main.py` - static server, default port `8090`.
- `json/ProductsDetailsExport.json` - full product database for import/sync.
- `json/products-demo-summary.json` - small generated summary used by the page only.

## Run

```bash
python3 main.py
```

Open `http://127.0.0.1:8090`.

## Deploy

Use the VPS templates in `deploy/`:

- `deploy/systemd/dn-html-demo.service` runs the static page on `127.0.0.1:8090`.
- `deploy/nginx/test.cartassist.shop.conf` proxies `test.cartassist.shop` to the local service.
- `DEPLOY_TEST.md` has the DNS, systemd, nginx, SSL, and verification commands.

## Product Mapping

The export schema is `Id`, `Name`, `Description`, `Appliances`, `CategoryId`.

For dashboard `POST /v1/ingest`, map at minimum:

- `Id` -> `external_id`
- `Name` -> `name`
- `Description` -> `description`
- `CategoryId` -> `categories` or category metadata

Add `price`, `quantity`, `currency`, `image_url`, and `url` if those fields become available.

`Appliances` (compatibility/fitment) is **not pushed** — see the note under Product Sync.

## Product Sync

`sync_products.py` converts `json/ProductsDetailsExport.json` into the dashboard
`POST /v1/ingest` payload and uploads it in batches. It maps `Id -> external_id`,
`Name -> name` (≤320 chars), `Description -> description` (≤2500 chars), and
`CategoryId -> categories`. The store **secret** key is read from `--key` or
`DN_DEMO_SECRET_KEY` and must never be committed or used in frontend code (the
widget itself carries no secret — this is a server-to-server, bearer-authed call).

**Compatibility/fitment is parked and deliberately not synced.** The old
dashboard had a second phase (`POST /v1/sync/compatibility`) that streamed the
export's ~2.08M appliance rows. The rebuilt dashboard has no such endpoint —
compatibility ingestion is an open design question (the parser/mapping +
retrieval layer is a documented scaffold). `POST /v1/ingest` tolerates inline
`compatibility` on a product but only counts it, reporting `skipped_compatibility`
back; the rows are never indexed. The old phase-2 streamer is in this repo's git
history if/when compatibility is unparked.

```bash
export DN_DEMO_SECRET_KEY='...secret...'
# local dev (dashboard on :8002)
python3 sync_products.py --api-base http://127.0.0.1:8002 --limit 3 --batch-size 3
python3 sync_products.py --batch-size 10            # full sync (prod default base)
```

`--batch-size 100` can fail with nginx `413 Request Entity Too Large`; use
`--batch-size 10` for the full catalog.
