# Mailchimp Setup

This landing page is prepared for Mailchimp form submission from the hero form.

## What you need from Mailchimp
From the Mailchimp embedded form code for your audience, copy:

1. The `form action` URL
2. The hidden anti-bot field name
3. The correct phone merge tag if it is not `PHONE`

## Where to place them
Open `index.html` and update the hero form:

### 1. Replace the form action
Find:

```html
action="https://YOUR_DC.list-manage.com/subscribe/post?u=YOUR_U&amp;id=YOUR_ID&amp;f_id=YOUR_FORM_ID"
```

Replace it with the real Mailchimp action URL from the embed code.

### 2. Replace the hidden anti-bot field name
Find:

```html
<input type="text" name="b_YOUR_U_YOUR_ID" tabindex="-1" value="" />
```

Replace `b_YOUR_U_YOUR_ID` with the exact hidden field name from Mailchimp.

### 3. Verify phone field name
Current form uses:

```html
name="PHONE"
```

If your Mailchimp audience uses another merge tag for phone, replace it.

## Current mapped fields
- Name: `FNAME`
- Email: `EMAIL`
- Phone: `PHONE`
- Tags: `landing-page-demo,algoritam-za-uspeha`

## Optional improvements in Mailchimp
Recommended audience fields:
- First name
- Email
- Phone

Recommended tags:
- `landing-page-demo`
- `algoritam-za-uspeha`

## Suggested flow
1. User submits form on the VPS landing page
2. Mailchimp stores the contact in the selected audience
3. You filter by tag
4. You send follow-up details or payment links later

## Important note
The current form opens submission in a new tab because it uses:

```html
target="_blank"
```

If you want a smoother UX later, replace raw Mailchimp post with:
- a custom backend endpoint on your VPS, or
- JavaScript/AJAX + your own submit handler

That would allow inline success/error messages without leaving the page.
