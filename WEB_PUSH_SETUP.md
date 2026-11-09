# CodeRed Web Push Notifications

This adds browser Web Push (including Android notification tray delivery) to the existing in-app notifications. WhatsApp is not required.

## Vercel environment variables

Set these for Production (and Preview if needed):

- `VAPID_PUBLIC_KEY` — public VAPID key
- `VAPID_PRIVATE_KEY` — private VAPID key (keep secret)
- `VAPID_SUBJECT` — e.g. `mailto:admin@coderedinvention.vercel.app`

Generate a key pair locally after installing pywebpush:

```bash
python -m pip install pywebpush
python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print('PUBLIC:', v.public_key); print('PRIVATE:', v.private_key)"
```

Use a VAPID key generator compatible with `pywebpush` if your installed version does not expose those attributes. Never commit the private key.

## Deploy steps

1. Add the three VAPID variables in Vercel Project → Settings → Environment Variables.
2. Redeploy.
3. Run `python manage.py migrate` against the production database.
4. Sign in to CodeRed on Android Chrome, open the site, and tap **Enable push**. Allow notifications.
5. For the best Android experience, use Chrome menu → Install app / Add to Home screen.

The browser must support Push API and notifications. On iPhone, web push generally requires iOS/iPadOS 16.4+ and the site to be added to the Home Screen. Push delivery depends on browser/OS connectivity and permission.
