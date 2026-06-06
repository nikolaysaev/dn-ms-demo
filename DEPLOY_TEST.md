# Deploy `test.cartassist.shop`

## DNS

Create this DNS record at the DNS provider for `cartassist.shop`:

```text
Type: A
Name: test
Value: <VPS_PUBLIC_IPV4>
TTL: 300
```

Wait until it resolves:

```bash
dig +short test.cartassist.shop
```

## VPS Deploy

Assumes the app is checked out at `/srv/apps/dn-html-demo` and runs as user `devops`.

```bash
cd /srv/apps/dn-html-demo
python3 -m py_compile main.py

sudo cp deploy/systemd/dn-html-demo.service /etc/systemd/system/dn-html-demo.service
sudo systemctl daemon-reload
sudo systemctl enable --now dn-html-demo
sudo systemctl status dn-html-demo

sudo cp deploy/nginx/test.cartassist.shop.conf /etc/nginx/sites-available/test.cartassist.shop.conf
sudo ln -sf /etc/nginx/sites-available/test.cartassist.shop.conf /etc/nginx/sites-enabled/test.cartassist.shop.conf
sudo nginx -t
sudo systemctl reload nginx
```

## SSL

Run after DNS resolves to the VPS:

```bash
sudo certbot --nginx -d test.cartassist.shop
sudo certbot renew --dry-run
```

## Checks

```bash
curl -I http://127.0.0.1:8090/
curl -I https://test.cartassist.shop/
```

## Chatbot Integration

For production widget mode, use:

```text
Widget script URL: https://dashboard.cartassist.shop/v1/widget/dn-chatbot.min.js
Dashboard public API base: https://dashboard.cartassist.shop/v1
```

The dashboard proxies chat to core through `CHATBOT_API_URL=https://api.cartassist.shop` or `http://127.0.0.1:8001` on the VPS.
