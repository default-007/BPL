#!/usr/bin/env bash
# Run on the server from the project root, with the cPanel virtualenv active:
#   source ~/virtualenv/<app-root>/<python-version>/bin/activate
#   ./scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -d .git ]; then
    git pull --ff-only
fi

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy

# Tell Passenger to reload the app.
mkdir -p tmp
touch tmp/restart.txt

echo "Deployed."
