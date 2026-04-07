# Deploy to VPS

## Target layout
- Repo path on server: `/srv/apps/dn-ms-demo/dn-ms-demo`
- Systemd unit path: `/etc/systemd/system/dn-ms-demo.service`
- Nginx vhost path: `/etc/nginx/sites-available/demo.datanetica.cloud`
- Internal app port: `3131`
- Public hostname: `demo.datanetica.cloud`

## Shared-server approach
- The Python app listens on `127.0.0.1:3131` only.
- Nginx proxies `demo.datanetica.cloud` to that local port.
- This avoids exposing port `3131` publicly and reduces the risk of affecting other apps on the server.

## Service setup
1. Copy `dn-ms-demo.service` to `/etc/systemd/system/dn-ms-demo.service`.
2. Run:
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable --now dn-ms-demo`
   - `sudo systemctl status dn-ms-demo`
3. Verify locally:
   - `curl -I http://127.0.0.1:3131`

## Nginx setup
1. Copy `demo.datanetica.cloud.nginx.conf` to `/etc/nginx/sites-available/demo.datanetica.cloud`.
2. Enable it:
   - `sudo ln -s /etc/nginx/sites-available/demo.datanetica.cloud /etc/nginx/sites-enabled/demo.datanetica.cloud`
3. Validate and reload:
   - `sudo nginx -t`
   - `sudo systemctl reload nginx`

## SSL
After DNS for `demo.datanetica.cloud` points to the VPS:
- `sudo certbot --nginx -d demo.datanetica.cloud`

## Notes
- Static assets are served by `main.py`.
- If you later add a dedicated deploy user, update `User` and `Group` in `dn-ms-demo.service`.
- Before reloading Nginx on a shared server, inspect current enabled vhosts:
  - `ls -la /etc/nginx/sites-enabled`
  - `grep -R "server_name" /etc/nginx/sites-enabled /etc/nginx/conf.d`
