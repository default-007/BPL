"""Entry point for Phusion Passenger (cPanel "Setup Python App", HostPinnacle)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bakpage.settings")

from bakpage.wsgi import application  # noqa: E402,F401
