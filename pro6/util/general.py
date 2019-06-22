
from pro6.util.compat import *

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
    return quote(pth.as_posix().replace('/', '\\') if enviro == OS_WINDOWS else pth.as_uri())


def unprepare_path(path_str):
    pth = urlparse(path_str)           # Break the path down into components (specifically for Windows where it's a URL)
    if pth.scheme == "file":
        path_str = pth.path            # If the path is to a file get rid of the extra markers

    path_str = unquote(path_str)       # Remove Windows/HTML character encoding (%20 == ' ', etc)
    return os.path.expanduser(os.path.expandvars(path_str))     # Expand OS variables
