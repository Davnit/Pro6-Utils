
from .base import Pro6Preferences

try:
    active = Pro6Preferences.load()
except (FileNotFoundError, ValueError):
    active = None
