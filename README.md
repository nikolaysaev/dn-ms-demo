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

For dashboard `/v1/sync`, map at minimum:

- `Id` -> `external_id`
- `Name` -> `name`
- `Description` -> `description`
- `CategoryId` -> `categories` or category metadata
- `Appliances` -> compatibility/category metadata where relevant

Add `price`, `quantity`, `currency`, `image_url`, and `url` if those fields become available.

## Product Sync

`sync_products.py` converts `json/ProductsDetailsExport.json` into the dashboard
`POST /v1/sync` payload and uploads it in batches. It maps `Id -> external_id`,
`Name -> name` (≤320 chars), `Description -> description` (≤2500 chars),
`CategoryId -> categories`, and `Appliances -> compatibility` (capped at 80 rows
per product). The store **secret** key is read from `--key` or
`DN_DEMO_SECRET_KEY` and must never be committed or used in frontend code.

```bash
export DN_DEMO_SECRET_KEY='...secret...'
python3 sync_products.py --limit 3 --batch-size 3   # smoke test
python3 sync_products.py --batch-size 10            # full sync
```

`--batch-size 100` can fail with nginx `413 Request Entity Too Large`; use
`--batch-size 10` for the full catalog.
