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
