
from pro6.util.compat import *

from datetime import datetime
import os
import pathlib
from urllib.parse import quote, unquote, urlparse
import uuid


NULL_UUID = "00000000-0000-0000-0000-000000000000"


def create_uuid():
    return str(uuid.uuid4())


def prepare_path(path_str, enviro=None):
    enviro = enviro or get_os()
    pth = pathlib.Path(path_str)
    if enviro == OS_WINDOWS:
        return quote(os.path.normpath(pth.as_posix()))
    else:
        return pth.as_uri().replace("file:///", "file://localhost/")


def unprepare_path(path_str):
    if path_str is None:
        return ""
    
    pth = urlparse(path_str)           # Break the path down into components (specifically for Windows where it's a URL)
    if pth.scheme == "file":
        path_str = pth.path            # If the path is to a file get rid of the extra markers

    path_str = unquote(path_str)       # Remove Windows/HTML character encoding (%20 == ' ', etc)
    return os.path.expanduser(os.path.expandvars(path_str))     # Expand OS variables


def parse_date(s):
    if not s or len(s) == 0:
        return None
    elif len(s) == 25:
        # Remove the colon from the UTC offset specifier.
        s = s[:22] + s[23:]
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def format_date(dt):
    s = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return s if len(s) == 19 else s[:22] + ':' + s[22:]
