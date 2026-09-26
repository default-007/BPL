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
- **403 CSRF failure on admin login**: add `https://yourdomain` to
  `CSRF_TRUSTED_ORIGINS`.
- **Unstyled pages**: run `collectstatic` and restart.
- Temporarily setting `DEBUG=True` shows full error pages. Turn it off again
  immediately afterwards.
