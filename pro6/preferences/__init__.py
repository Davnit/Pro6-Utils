
from .base import Pro6Preferences
from .error import InstallNotFoundError, InvalidInstallError

try:
    active = Pro6Preferences.load()
except (InstallNotFoundError, InvalidInstallError):
    active = None
