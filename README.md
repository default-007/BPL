# Bakpage Labs website

Django site for Bakpage Labs: services, portfolio projects and blog, all
managed through the Django admin (Markdown content via django-markdownx,
tags via django-taggit).

## Local development

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# In .env set: DEBUG=True, DB_ENGINE=sqlite, SECURE_SSL_REDIRECT=False,
# and any SECRET_KEY value.

python manage.py migrate
python manage.py loaddata site_content          # sample project/blog content
mkdir -p media && cp website/fixtures/media/* media/
python manage.py createsuperuser
python manage.py runserver
```

Run the tests with `python manage.py test`.

## Layout

| Path | Contents |
|---|---|
| `bakpage/` | Project settings (env-driven), URLs, WSGI |
| `website/` | Models, views, URLs, admin, migrations, fixtures, tests |
| `templates/` | Page templates and partials |
| `static/` | CSS, JS, fonts, images |
| `passenger_wsgi.py` | Entry point for cPanel / Passenger hosting |
| `scripts/deploy.sh` | Update script for the server |

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for HostPinnacle (cPanel) instructions.
