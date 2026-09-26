# Deploying to HostPinnacle (cPanel)

HostPinnacle's shared and reseller hosting uses cPanel. Python apps run through
**Setup Python App** (CloudLinux Python Selector + Phusion Passenger). The
project ships a `passenger_wsgi.py` entry point for that setup.

Replace `cpaneluser` below with your cPanel username and `bakpagelabs.com`
with your domain.

## Requirements

- **Python 3.10 or newer** (Django 5.2). Pick the newest version the Python
  selector offers.
- **Database**: MySQL 8.0.11+ or MariaDB 10.5+ (check the version in
  phpMyAdmin). If the server only has an older MariaDB, use `DB_ENGINE=sqlite`,
  which is fine for a site this size.
- An SSL certificate on the domain (cPanel > SSL/TLS Status > Run AutoSSL).

## 1. Create the database

cPanel > **MySQL Databases**:

1. Create a database, e.g. `cpaneluser_bpl`.
2. Create a user, e.g. `cpaneluser_bpl`, with a strong password.
3. Add the user to the database with **All Privileges**.

## 2. Upload the code

Put the project **outside** `public_html`, e.g. `/home/cpaneluser/bpl`.

- **Git (recommended)**: cPanel > **Git Version Control** > Create, clone the
  repository into `/home/cpaneluser/bpl`. For a private repo, add a deploy key
  under cPanel > SSH Access first.
- **Or** upload a zip in File Manager and extract it there.

## 3. Create the Python app

cPanel > **Setup Python App** > **Create Application**:

| Field | Value |
|---|---|
| Python version | 3.11 or newer |
| Application root | `bpl` |
| Application URL | `bakpagelabs.com` (leave the path empty) |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |
| Passenger log file | `/home/cpaneluser/bpl/logs/passenger.log` |

Under **Environment variables**, add the values from `.env.example` (at least
`SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and the
`DB_*` settings). Alternatively, copy `.env.example` to `.env` in
`/home/cpaneluser/bpl` and fill it in. Either works; variables set in cPanel
take precedence.

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Click **Create**. At the top of the app's page, cPanel shows the command to
enter the virtualenv. Copy it.

## 4. Install and initialise

Open cPanel > **Terminal** (or SSH in) and run:

```bash
source /home/cpaneluser/virtualenv/bpl/3.11/bin/activate   # the command cPanel showed you
cd ~/bpl
mkdir -p logs

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# First deploy only: load the existing project/blog content and its images.
# The six services are created by the migrations.
python manage.py loaddata site_content
mkdir -p media && cp website/fixtures/media/* media/

python manage.py createsuperuser
python manage.py check --deploy
```

Then click **Restart** in Setup Python App. Visit the site and `/admin/`.

## 5. HTTPS

With `DEBUG=False`, Django redirects HTTP to HTTPS and marks cookies secure.

- **Redirect loop** after enabling SSL: set `SECURE_PROXY_SSL_HEADER=True`
  and restart. If that doesn't fix it, set `SECURE_SSL_REDIRECT=False` and use
  cPanel > Domains > **Force HTTPS Redirect** instead.
- Once HTTPS works everywhere, you can raise `SECURE_HSTS_SECONDS` to
  `31536000`.

## 6. Contact form email

The contact form emails each enquiry to `CONTACT_EMAIL`, with Reply-To set to
the visitor so you can answer straight from your inbox. Every enquiry is also
saved and listed under **Contact messages** in `/admin/`, so none are lost if
sending fails.

1. cPanel > **Email Accounts** > Create, e.g. `info@bakpagelabs.com`.
2. Click **Connect Devices** on that account and note the SMTP server and port
   (usually `mail.bakpagelabs.com`, port `465` with SSL).
3. Set these environment variables in Setup Python App (or `.env`), then restart:

   | Variable | Value |
   |---|---|
   | `EMAIL_HOST` | `mail.bakpagelabs.com` |
   | `EMAIL_PORT` | `465` (SSL) or `587` (STARTTLS) |
   | `EMAIL_HOST_USER` | `info@bakpagelabs.com` |
   | `EMAIL_HOST_PASSWORD` | the mailbox password |
   | `DEFAULT_FROM_EMAIL` | `info@bakpagelabs.com` (must be a mailbox on your domain) |
   | `CONTACT_EMAIL` | where enquiries should go |

4. Test it from the terminal:

   ```bash
   python manage.py sendtestemail info@bakpagelabs.com
   ```

If emails land in spam, check cPanel > **Email Deliverability** and fix any
SPF/DKIM issues it reports for the domain. Each IP address can send 5 messages
per hour (`CONTACT_RATE_LIMIT`), and a hidden honeypot field filters out
simple bots.

## Static and media files

- **Static files** (CSS/JS/fonts) are collected into `staticfiles/` and served
  by WhiteNoise with far-future cache headers. Re-run `collectstatic` whenever
  files under `static/` change.
- **Uploaded images** (admin uploads) go to `MEDIA_ROOT` (default `media/` in
  the project). With `SERVE_MEDIA=True`, Django serves them. For better
  performance, you can instead set
  `MEDIA_ROOT=/home/cpaneluser/public_html/media`, which Apache serves
  directly, and set `SERVE_MEDIA=False`.
- Back up `media/` and the database. Neither is in git.

## Updating the site

```bash
source /home/cpaneluser/virtualenv/bpl/3.11/bin/activate
cd ~/bpl
./scripts/deploy.sh
```

The script pulls the latest code, installs requirements, migrates, collects
static files, runs the deploy checks, and restarts Passenger.

## Troubleshooting

- **"Incomplete response received from application" / 500 errors**: check
  `logs/passenger.log`. The usual causes are a missing environment variable
  (e.g. `SECRET_KEY`), a wrong DB password, or requirements not installed in
  the app's virtualenv.
- **400 Bad Request**: the domain isn't in `ALLOWED_HOSTS`.
- **403 CSRF failure on admin login or the contact form**: add
  `https://yourdomain` to `CSRF_TRUSTED_ORIGINS`.
- **Contact form says thanks but no email arrives**: the enquiry is still in
  the admin with "Email sent" unticked. Check `logs/passenger.log` for the
  SMTP error, and run `python manage.py sendtestemail` to test the settings.
- **Unstyled pages**: run `collectstatic` and restart.
- Temporarily setting `DEBUG=True` shows full error pages. Turn it off again
  immediately afterwards.
