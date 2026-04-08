# Formspree Setup

This landing page is prepared to send the hero form directly to Formspree.

## Files
- `formspree-config.js`
- `index.html`

## What to do in Formspree
1. Create an account at `https://formspree.io/`
2. Create a new form in the dashboard
3. Copy the form endpoint from the Integration section

Formspree's HTML form guide:
- `https://help.formspree.io/hc/en-us/articles/27638977431699-Building-an-HTML-Form`

## What to edit locally
Open `formspree-config.js` and replace the placeholder values.

### 1. Replace the endpoint
Find:

```js
endpoint: "https://formspree.io/f/YOUR_FORM_ID"
```

Replace `YOUR_FORM_ID` with the real Formspree form ID.

### 2. Adjust the metadata if needed
These values are optional but useful:

```js
subject: "Нова регистрация за Алгоритъм за успеха",
source: "demo.datanetica.cloud",
tags: "landing-page-demo,algoritam-za-uspeha"
```

You can keep them as-is or customize them for the real domain/event.

## Current fields sent by the form
- `name`
- `email`
- `phone`
- `_gotcha`
- `_subject`
- `source`
- `tags`

## Recommended Formspree setup
- Set the target email in the Formspree form settings
- Turn on email notifications
- Optionally connect Google Sheets or another workflow later

## Suggested flow
1. User submits the form on the landing page
2. Formspree stores the lead and emails you
3. You review the leads in Formspree
4. When tickets are ready, send Stripe Payment Links manually

## Deploy after setup
```bash
cd /srv/apps/dn-ms-demo/dn-ms-demo
git pull origin main
sudo systemctl restart dn-ms-demo
```
