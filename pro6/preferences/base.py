
from ..library import DocumentLibrary
from .error import InstallNotFoundError, InvalidInstallError
from ..util.compat import *
from ..util.constants import SCALE_FIT, SCALE_FILL, SCALE_STRETCH
from ..util.xmlhelp import RV_XML_VARNAME

import os
import xml.etree.ElementTree as Xml


def _get_prefs_path():
    this_os = get_os()
    if this_os == OS_WINDOWS:
        return os.path.join(os.getenv("APPDATA"), "RenewedVision", "ProPresenter6", "Preferences")
    elif this_os == OS_MACOSX:
        return os.path.join(os.path.expanduser("~"), "Library", "Preferences", "com.renewedvision.ProPresenter6")
    else:
        return None


def _win_scaling_to_int(value):
    switch = {
        "scaletofit": SCALE_FIT,
        "scaletofill": SCALE_FILL,
        "stretchtofill": SCALE_STRETCH
    }
    return switch.get(value.lower())


class Pro6Preferences:
    def __init__(self):
        self.location = None
        self.data_path = None
        self.thumbnail_cache = None

        self.libraries = {
            "Default": os.path.join(os.path.expanduser("~"), "Documents", "ProPresenter6")
        }
        self._library = None

        self.logo_path = None
        self.foreground_scaling = SCALE_FIT         # Scale to fit
        self.background_scaling = SCALE_STRETCH     # Stretch to fill
        self.output_width = 1280
        self.output_height = 720

        # Set the default user data path.
        this_os = get_os()
        if this_os == OS_WINDOWS:
            self.data_path = os.path.join(os.getenv("APPDATA"), "RenewedVision", "ProPresenter6")
            self.thumbnail_cache = os.path.join(self.data_path, "Thumbnails", "Images")
        elif this_os == OS_MACOSX:
            self.data_path = os.path.join(os.path.expanduser("~"),
                                          "Library", "Application Support", "RenewedVision", "ProPresenter6")
            self.thumbnail_cache = os.path.join(self.data_path, "cache")

    def change_library(self, new_library):
        """ Changes the active library in this context (does not change it on the system). """
        for title, lib_path in self.libraries.items():
            if title.lower() == new_library.lower():
                self._library = DocumentLibrary(title, lib_path)
                return self.get_library()
        return None

    def get_library(self):
        """ Returns the active library. """
        return self._library

    @classmethod
    def load(cls, file=None):
        """
            Loads preferences from the specified directory.

            If no directory is given, the default for the system will be used.
            Saving is not supported so values are effectively read-only.
        """

        obj = cls()
        obj.location = file or _get_prefs_path()

        if not (obj.location and os.path.isdir(obj.location)):
            raise InstallNotFoundError()

        # Check for general preferences file
        if os.path.isfile(os.path.join(obj.location, "GeneralSettings.xml")):
            obj._load_mac_prefs()
        elif os.path.isfile(os.path.join(obj.location, "GeneralPreferences.pro6pref")):
            obj._load_win_prefs()
        else:
            raise InstallNotFoundError()

        return obj

    def _load_mac_prefs(self):
        general = Xml.parse(os.path.join(self.location, "GeneralSettings.xml"))
        if general.getroot().tag != "RVGeneralSettings":
            raise InvalidInstallError("Unrecognized format in GeneralSettings.xml.")

        # Load the list of available document libraries.
        self.libraries = {}
        for array in general.findall("array"):
            if array.get(RV_XML_VARNAME, "").lower() == "libraries":
                for library in array.findall("RVLibrary"):
                    self.libraries[library.get("name")] = os.path.expanduser(library.get("path"))
                break

        root = general.getroot()
        self.logo_path = root.get("logoFilePath")
        self.data_path = root.get("userDataPath", self.data_path)
        self.foreground_scaling = root.get("foregroundScaleBehavior", self.foreground_scaling)
        self.background_scaling = root.get("backgroundScaleBehavior", self.background_scaling)

        default_library = list(self.libraries.keys())[0]
        self.change_library(root.get("selectedLibraryName", default_library))

        # Display settings in a different file
        display_path = os.path.join(self.location, "DisplaySettings.xml")
        if not os.path.isfile(display_path):
            raise InstallNotFoundError()

        display = Xml.parse(display_path)
        if display.getroot().tag != "RVDisplaySettings":
            raise InvalidInstallError("Unrecognized format in DisplaySettings.xml.")

        root = display.getroot()
        self.output_width = int(root.get("outputWidth", self.output_width))
        self.output_height = int(root.get("outputHeight", self.output_height))

    def _load_win_prefs(self):
        general = Xml.parse(os.path.join(self.location, "GeneralPreferences.pro6pref"))
        if general.getroot().tag != "{" + win_ns["pref"] + "}RVPreferencesGeneral":
            raise InvalidInstallError("Unrecognized format in GeneralPreferences.pro6pref.")

        # Load list of available document libraries.
        self.libraries = {}
        for library in general.findall("pref:LibraryFolders/pref:RVLibraryFolder", win_ns):
            self.libraries[library.findtext("pref:Name", None, win_ns)] = library.findtext("pref:Location", None, win_ns)

        self.logo_path = general.findtext("pref:LogoPath", None, win_ns)
        self.data_path = general.findtext("pref:AppDataPath", self.data_path, win_ns)

        default_library = list(self.libraries.keys())[0]
        self.change_library(general.findtext("pref:SelectedLibraryFolder/pref:Name", default_library, win_ns))

        # For some reason with windows the scaling settings are in a separate, small file.
        adv_path = os.path.join(self.location, "AdvancedPreferences.pro6pref")
        if not os.path.isfile(adv_path):
            raise InstallNotFoundError()

        advanced = Xml.parse(adv_path)
        self.foreground_scaling = _win_scaling_to_int(
            advanced.findtext("pref:ForegroundScaleBehavior", self.foreground_scaling, win_ns))
        self.background_scaling = _win_scaling_to_int(
            advanced.findtext("pref:BackgroundScaleBehavior", self.background_scaling, win_ns))

        # Display settings still in a separate file
        display_path = os.path.join(self.location, "DisplayPreferences.pro6pref")
        if not os.path.isfile(display_path):
            raise InstallNotFoundError()

        display = Xml.parse(display_path)
        if display.getroot().tag != "{" + win_ns["pref"] + "}RVPreferencesDisplay":
            raise InvalidInstallError("Unrecognized format in DisplayPreferences.pro6pref.")

        self.output_width = int(display.findtext("pref:ScreenWidth", self.output_width, win_ns))
        self.output_height = int(display.findtext("pref:ScreenHeight", self.output_height, win_ns))
