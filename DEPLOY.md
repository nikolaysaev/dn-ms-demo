# Deploy to VPS

## Files
- App directory on server: `/opt/dn-html-demo`
- Service file: `/etc/systemd/system/dn-html-demo.service`
- Port: `3131`

## Steps
1. Copy this project to `/opt/dn-html-demo` on the VPS.
2. Copy `dn-html-demo.service` to `/etc/systemd/system/dn-html-demo.service`.
3. Run:
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable --now dn-html-demo`
   - `sudo systemctl status dn-html-demo`
4. Open port `3131` in the VPS firewall if needed.

## Notes
- The service binds to `0.0.0.0:3131`.
- If the server should stay private behind Nginx, change `HOST` to `127.0.0.1`.
- Static assets are served directly by `main.py`.
