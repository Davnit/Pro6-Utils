
from pro6.util.constants import OS_WINDOWS, OS_MACOSX

import platform

# Windows XML namespaces
win_ns = {
    "pref": "http://schemas.datacontract.org/2004/07/ProPresenter.BO.Common.Preferences",
    "i": "http://www.w3.org/2001/XMLSchema-instance",
    "a": "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
}

builds = {
    OS_WINDOWS: 6016,
    OS_MACOSX: 16245
}


def get_os():
    """Returns the OS value for the current system."""
    switch = {
        "windows": OS_WINDOWS,
        "darwin": OS_MACOSX
    }
    return switch.get(platform.system().lower(), 0)
