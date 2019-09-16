
from .base import Pro6Preferences
from .error import InstallNotFoundError, InvalidInstallError

try:
    install = Pro6Preferences.load()
except (InstallNotFoundError, InvalidInstallError):
    install = None
