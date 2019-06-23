
from .cues import MediaCue, AudioCue

from .elements import DISPLAY_ELEMENTS

from ..util.xmlhelp import XmlBackedObject, ColorString, create_array, RV_XML_VARNAME


class DisplaySlide(XmlBackedObject):
    def __init__(self, **extra):
        super().__init__("RVDisplaySlide", extra)

        self.background_color = None
        self.highlight_color = None
        self.enabled = True
        self.hotkey = None
        self.label = None
        self.notes = None

        self.cues = []
        self.elements = []
        self.background = None      # This can be a background or a foreground, depending on it's behavior attribute.

    def get_display_name(self):
        if self.label and len(self.label) > 0:
            return self.label
        elif self.background:
            return self.background.display_name
        elif len(self.cues) > 0 and isinstance(self.cues[0], AudioCue):
            return self.cues[0].display_name

    def write(self):
        attrib = {
            "drawingBackgroundColor": (self.background_color is not None),
            "highlightColor": str(self.highlight_color) if self.highlight_color else "",
            "enabled": self.enabled,
            "hotKey": self.hotkey,
            "label": self.label,
            "notes": self.notes
        }

        if self.background_color is not None:
            attrib["backgroundColor"] = str(self.background_color)
        super().update(attrib)
        super().set_uuid()

        e = super().write()
        if self.background:
            if not isinstance(self.background, MediaCue):
                raise TypeError("Slide background must be a MediaCue.")
            self.background.update({RV_XML_VARNAME: "backgroundMediaCue"})
            e.append(self.background.write())

        e.append(create_array("cues", self.cues))
        e.append(create_array("displayElements", self.elements))
        return e

    def read(self, element):
        super().read(element)

        self.background_color = ColorString.parse(element.get("backgroundColor")) \
            if element.get("drawingBackgroundColor") == "true" else None

        self.highlight_color = ColorString.parse(element.get("highlightColor"))
        self.enabled = element.get("enabled") == "true"
        self.hotkey = element.get("hotKey", self.hotkey)
        self.label = element.get("label", self.label)
        self.notes = element.get("notes", self.notes)

        # Read cues
        self.cues = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='cues']"):
            if e.tag == "RVAudioCue":
                self.cues.append(AudioCue(None).read(e))
            else:
                self.cues.append(e)

        # Read child elements.
        self.elements = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='displayElements']"):
            if e.tag in DISPLAY_ELEMENTS:
                self.elements.append(DISPLAY_ELEMENTS[e.tag](source=e.get("source")).read(e))
            else:
                print("Unsupported display element found on slide '%s': %s" % (self.label, e.tag))

        # Read background
        e = element.find("RVMediaCue[@" + RV_XML_VARNAME + "='backgroundMediaCue']")
        if e:
            self.background = MediaCue(None).read(e)
        return self
