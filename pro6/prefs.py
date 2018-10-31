
from pro6.constants import *
import pro6.util as util

import os
from os import path
from xml.etree import ElementTree


RV_GENERAL_SETTINGS = "RVGeneralSettings"
RV_DISPLAY_SETTINGS = "RVDisplaySettings"

# Windows namespaces
ns = {
    "pref": "http://schemas.datacontract.org/2004/07/ProPresenter.BO.Common.Preferences",
    "i": "http://www.w3.org/2001/XMLSchema-instance",
    "a": "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
}

# Windows scale behavior strings
scaling = {
    SCALE_FIT: "ScaleToFit",
    SCALE_FILL: "ScaleToFill",
    SCALE_STRETCH: "StretchToFill"
}

found_preferences = {}


def get_pref_path():
    this_os = util.get_os()
    if this_os == OS_WINDOWS:
        return path.join(os.getenv("APPDATA"), "RenewedVision", "ProPresenter6", "Preferences")
    elif this_os == OS_MACOSX:
        return path.join(os.path.expanduser("~"), "Preferences", "com.renewedvision.ProPresenter6")


def try_get_text(element, default=""):
    if element is None:
        return default
    if not isinstance(element, ElementTree.Element):
        raise TypeError("element must be an XML element.")
    return element.text


def get_system_preferences():
    pp = get_pref_path()
    if pp in found_preferences:
        return found_preferences.get(pp)
    else:
        if not path.isdir(pp):
            # ProPresenter 6 isn't installed, hasn't been run, or we couldn't find the settings.
            print("ProPresenter's configuration files could not be found. Using default settings.")
            pp = None

        prefs = ProPresenter6Preferences(pp)
        found_preferences[pp] = prefs
        return prefs


class ProPresenter6Preferences:
    def __init__(self, source):
        self.exists = True
        self.general = None
        self.display = None
        self.labels = []
        self.groups = []

        if source is None:
            self.exists = False
            self.path = None
            self.general = GeneralSettings()
            self.display = DisplaySettings()
            return

        self.path = source if path.isdir(source) else path.dirname(source)

        adv = None
        for file in os.listdir(self.path):
            fpath = path.join(self.path, file)
            if path.isfile(fpath):
                _, ext = os.path.splitext(file)

                data = ElementTree.parse(fpath)
                root = data.getroot()
                tag = root.tag

                if ext.lower() == ".xml":
                    if tag == RV_GENERAL_SETTINGS:
                        self.general = GeneralSettings(data)
                    elif tag == RV_DISPLAY_SETTINGS:
                        self.display = DisplaySettings(data)
                    elif tag == "dictionary" and file == "LabelSettings.xml":
                        dic = util.from_xml_dictionary(root)
                        self.labels = dic.get("labels")
                        self.groups = dic.get("groups")

                elif ext.lower() == ".pro6pref":
                    if tag.endswith("}RVPreferencesGeneral"):
                        self.general = GeneralSettings(data)
                    elif tag.endswith("}RVPreferencesDisplay"):
                        self.display = DisplaySettings(data)
                    elif tag.endswith("}RVPreferencesLabels"):
                        continue    # Not supported yet
                    elif tag.endswith("}RVPreferencesAdvanced"):
                        adv = root  # This has to be handled at the end

        if adv is not None and self.general is not None:
            bg = adv.find("pref:BackgroundScaleBehavior", ns).text.lower()
            fg = adv.find("pref:ForegroundScaleBehavior", ns).text.lower()

            for k, v in scaling.items():
                mode = v.lower()
                if bg == mode:
                    self.general.background_scaling = k
                if fg == mode:
                    self.general.foreground_scaling = k


class GeneralSettings:
    def __init__(self, document=None):
        self.logo_path = ""
        self.logo_preserve_aspect = False
        self.user_data_path = os.curdir
        self.user_data_type = 0
        self.media_path = os.curdir
        self.media_type = 0
        self.library_name = "Current Directory"
        self.library_path = os.curdir
        self.background_scaling = 3
        self.foreground_scaling = 0

        if document is None:
            return

        root = document.getroot()
        if root.tag == RV_GENERAL_SETTINGS:
            self.logo_path = root.get("logoFilePath", self.logo_path)
            self.logo_preserve_aspect = util.to_bool(root.get("preserveLogoAspectRatio", str(self.logo_preserve_aspect)))
            self.user_data_path = root.get("userDataPath", self.user_data_path)
            self.user_data_type = int(root.get("userDataType", str(self.user_data_type)))
            self.media_path = root.get("mediaRepositoryPath", self.media_path)
            self.media_type = int(root.get("mediaRepositoryType", str(self.media_type)))
            self.library_name = root.get("selectedLibraryName", self.library_name)
            self.library_path = root.get("selectedLibraryPath", self.library_name)
            self.background_scaling = int(root.get("backgroundScaleBehavior", str(self.background_scaling)))
            self.foreground_scaling = int(root.get("foregroundScaleBehavior", str(self.foreground_scaling)))

            self.libraries = {}
            self.search_paths = []

            for e in root.findall("array"):
                var_name = e.get(util.ATTRIB_VARNAME)

                if var_name == "libraries":
                    for se in e.findall("RVLibrary"):
                        name = se.get("name")
                        lib_path = se.get("path")
                        sync_name = se.get("syncLibraryName", "")
                        lib = DocumentLibrary(name, lib_path, sync_name)

                        self.libraries[lib.name] = lib
                elif var_name == "searchPaths":
                    self.search_paths.extend(e.itertext())

        elif root.tag.endswith("}RVPreferencesGeneral"):
            self.logo_path = try_get_text(root.find("pref:LogoPath", ns))
            self.logo_preserve_aspect = util.to_bool(try_get_text(root.find("pref:LogoPreserveAspectRatio", ns)))
            self.user_data_path = try_get_text(root.find("pref:AppDataPath", ns))
            self.user_data_type = try_get_text(root.find("pref:AppDataType", ns))
            self.media_path = try_get_text(root.find("pref:MediaRepositoryPath", ns))
            self.media_type = try_get_text(root.find("pref:MediaRepositoryType", ns))

            library = root.find("pref:SelectedLibraryFolder", ns)
            self.library_name = try_get_text(library.find("pref:Name", ns))
            self.library_path = try_get_text(library.find("pref:Location", ns))

            self.background_scaling = 3
            self.foreground_scaling = 0

            self.libraries = {}
            self.search_paths = []

            for e in root.findall("./pref:LibraryFolders/pref:RVLibraryFolder", ns):
                name = try_get_text(e.find("pref:Name", ns))
                lib_path = try_get_text(e.find("pref:Location", ns))
                sync_name = try_get_text(e.find("pref:CloudLibraryName", ns))
                lib = DocumentLibrary(name, lib_path, sync_name)

                self.libraries[lib.name] = lib

            for e in root.findall("./pref:MediaFileSearchPaths/a:string", ns):
                self.search_paths.append(e.text)

        else:
            raise ValueError("General settings document format not supported: %s" % root.tag)


class DocumentLibrary:
    def __init__(self, name, lib_path, sync=None):
        self.name = name
        self.path = lib_path
        self.sync_name = sync or ""


class DisplaySettings:
    def __init__(self, document=None):
        self.output_width = 1280
        self.output_height = 1024
        self.scale_to_fit = False

        if document is None:
            return

        root = document.getroot()
        if root.tag == RV_DISPLAY_SETTINGS:
            self.output_width = int(root.get("outputWidth", str(self.output_width)))
            self.output_height = int(root.get("outputHeight", str(self.output_height)))
            self.scale_to_fit = util.to_bool(root.get("scaleToFit", str(self.scale_to_fit)))
        elif root.tag.endswith("}RVPreferencesDisplay"):
            self.output_width = int(try_get_text(root.find("pref:ScreenWidth", ns), str(self.output_width)))
            self.output_height = int(try_get_text(root.find("pref:ScreenHeight", ns), str(self.output_height)))
            self.scale_to_fit = util.to_bool(try_get_text(root.find("pref:ScalePresentationToOutput", ns),
                                                          str(self.scale_to_fit)))
        else:
            raise ValueError("Display settings document format not supported: %s" % root.tag)
