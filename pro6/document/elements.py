
from ..util.constants import *
from ..util.general import prepare_path, unprepare_path
from ..util.media import MediaFile, MEDIA_FORMATS
from ..util.xmlhelp import RV_XML_VARNAME, XmlBackedObject, ColorString, Rect3D, PointXY, Shadow, Stroke

import base64
import xml.etree.ElementTree as Xml


# This is the root object for all other slide elements. It shouldn't be created explicitly.
class DisplayElement(XmlBackedObject):
    def __init__(self, tag, attrib=None):
        defaults = {        # Values are required but not (yet?) supported by the interface
            "typeID": 0,
            "fromTemplate": False
        }
        defaults.update(attrib)
        super().__init__(tag, defaults)

        self.fill_color = None
        self.position = None
        self.shadow = None
        self.stroke = None

        self.display_name = "Default"
        self.locked = False
        self.persistent = False
        self.delay = 0.0
        self.bezel_radius = 0.0
        self.rotation = 0.0
        self.source = None

    def write(self):
        attrib = {
            "displayName": self.display_name,
            "displayDelay": self.delay or 0.0,
            "locked": self.locked,
            "source": prepare_path(self.source),
            "bezelRadius": self.bezel_radius or 0.0,
            "rotation": self.rotation or 0.0,
            "drawingFill": (self.fill_color is not None),
            "drawingShadow": (self.shadow and self.shadow.enabled),
            "drawingStroke": (self.stroke and self.stroke.enabled)
        }
        super().update(attrib)
        super().set_uuid()

        e = super().write()
        e.append((self.position or Rect3D()).write("position"))
        e.append((self.shadow or Shadow()).write("shadow"))
        e.append((self.stroke or Stroke()).write())
        return e

    def read(self, element):
        super().read(element)

        self.fill_color = ColorString.parse(element.get("fillColor")) if element.get("drawingFill") == "true" else None
        self.position = Rect3D().read(element.find("RVRect3D[@" + RV_XML_VARNAME + "='position']"))
        self.shadow = Shadow().read(element.find("shadow"))
        self.stroke = Stroke().read(element.find("dictionary[@" + RV_XML_VARNAME + "='stroke']"))
        self.display_name = element.get("displayName", self.display_name)
        self.locked = (element.get("locked") == "true")
        self.delay = float(element.get("displayDelay", str(self.delay)))
        self.bezel_radius = float(element.get("bezelRadius", str(self.bezel_radius)))
        self.rotation = float(element.get("rotation", str(self.rotation)))
        self.source = unprepare_path(element.get("source", self.source)) if "source" in element.attrib else None
        return self


class TextElement(DisplayElement):
    def __init__(self, **extra):
        super().__init__("RVTextElement", extra)
        self.text = ""
        self.rtf = ""

        self.adjust_to_fit = False
        self.vertical_align = 0
        self.reveal = 0
        self.flow_data = ""
        self.font_data = ""

    def write(self):
        attrib = {
            "adjustsHeightToFit": self.adjust_to_fit,
            "verticalAlignment": self.vertical_align,
            "revealType": self.reveal
        }
        super()._attrib.update(attrib)
        e = super().write()

        pairs = [
            ("RTFData", self.rtf),
            ("PlainText", self.text),
            ("WinFlowData", self.flow_data),
            ("WinFontData", self.font_data)
        ]
        for var, value in pairs:
            sub = Xml.Element("NSString", {RV_XML_VARNAME: var})
            sub.text = base64.b64encode(value).decode('ascii')
            e.append(sub)
        return e

    def read(self, element):
        super().read(element)

        self.adjust_to_fit = element.get("adjustsHeightToFit") == "true"
        self.vertical_align = int(element.get("verticalAlignment", str(self.vertical_align)))
        self.reveal = int(element.get("revealType", str(self.reveal)))

        data = {"RTFData": "", "PlainText": "", "WinFlowData": "", "WinFontData": ""}
        for key in data.keys():
            sub = element.find("NSString[@" + RV_XML_VARNAME + "='" + key + "']")
            if sub:
                data[key] = base64.b64decode(sub.text).decode('ascii')

        self.text = data["PlainText"]
        self.rtf = data["RTFData"]
        self.flow_data = data["WinFlowData"]
        self.font_data = data["WinFontData"]
        return self


# This is an intermediate class for media file based slide elements (images and videos)
class MediaElement(DisplayElement):
    def __init__(self, tag, source, attrib=None):
        defaults = {
            "flippedHorizontally": False,
            "flippedVertically": False,
            "manufactureName": None,
            "manufactureURL": None
        }
        defaults.update(attrib)
        super().__init__(tag, defaults)

        if isinstance(source, MediaFile):
            self.file = source
        elif isinstance(source, str):
            self.file = MediaFile(source)
        else:
            raise TypeError("Media source must be path or MediaFile object.")

        self.display_name = self.file.name
        self.format = self.file.format
        self.source = self.file.path

        self.scaling_type = SCALE_FIT
        self.scaling_size = PointXY(1, 1)
        self.offset = PointXY(0, 0)
        self.opacity = 1.0

    def write(self):
        attrib = {
            "scaleBehavior": self.scaling_type,
            "scaleSize": self.scaling_size,
            "imageOffset": self.offset,
            "opacity": self.opacity,
            "format": self.format,
            "source": self.file.path if self.file else None
        }
        super().update(attrib)
        super().set_uuid()
        return super().write()

    def read(self, element):
        super().read(element)

        self.scaling_type = element.get("scaleBehavior", self.scaling_type)
        self.scaling_size = PointXY.parse(element.get("scaleSize"))
        self.offset = PointXY.parse(element.get("imageOffset"))
        self.opacity = float(element.get("opacity", str(self.opacity)))
        self.format = element.get("format", self.format)
        self.file = MediaFile(element.get("source")) if "source" in element.attrib else None
        return self

    @classmethod
    def create(cls, source, **extra):
        if source is None or not isinstance(source, str):
            raise TypeError("Media element source must be a filename (str).")

        file = MediaFile(source)
        mime = file.get_metadata().get("mime_type")
        if mime.startswith("image/"):
            return ImageElement(file, **extra)
        elif mime.startswith("video/"):
            return VideoElement(file, **extra)
        elif mime.startswith("audio/"):
            return AudioElement(file, **extra)
        else:
            raise ValueError("Unsupported media type: %s" % mime)


class ImageElement(MediaElement):
    def __init__(self, source, **extra):
        super().__init__("RVImageElement", source, extra)
        self.format = self.file.format


class VideoElement(MediaElement):
    def __init__(self, source, **extra):
        defaults = {
            "fieldType": 0
        }
        defaults.update(extra)
        super().__init__("RVVideoElement", source, defaults)

        self.frame_rate = 0.0
        self.volume = 1.0
        self.in_point = 0
        self.out_point = 0
        self.end_point = 0
        self.play_rate = 1.0
        self.playback_mode = PLAYBACK_STOP
        self.time_scale = 600

        self.natural_size = PointXY(*self.file.frame_size())
        self.reset_inout_points()

    def reset_inout_points(self):
        self.in_point = 0
        self.out_point = self.end_point = (self.file.duration() * self.time_scale)

    def write(self):
        attrib = {
            "frameRate": self.frame_rate,
            "audioVolume": self.volume,
            "inPoint": self.in_point,
            "outPoint": self.out_point,
            "endPoint": self.end_point,
            "playRate": self.play_rate,
            "playbackBehavior": self.playback_mode,
            "naturalSize": self.natural_size,
            "timeScale": self.time_scale
        }
        super().update(attrib)
        return super().write()

    def read(self, element):
        super().read(element)

        self.frame_rate = float(element.get("frameRate", str(self.frame_rate)))
        self.volume = float(element.get("audioVolume", str(self.volume)))
        self.in_point = int(element.get("inPoint", str(self.in_point)))
        self.out_point = int(element.get("outPoint", str(self.out_point)))
        self.end_point = int(element.get("endPoint", str(self.end_point)))
        self.play_rate = float(element.get("playRate", str(self.play_rate)))
        self.playback_mode = element.get("playbackBehavior", self.playback_mode)
        self.natural_size = PointXY.parse(element.get("naturalSize"))
        return self


class AudioElement(XmlBackedObject):
    """
        AudioElement is weird because it logically exists as a subset of a MediaElement, but doesn't share any
            of the MediaElement properties (which more closely resemble what would be called a 'GraphicsElement')
            and instead is very similar to the properties associated with a VideoElement, with some small differences.

            The main deciding factor in having it completely separate is that it lives under an AudioCue in the XML
            structure, which does not exist separately on the slide object like MediaCue does, but instead goes in the
            'cues' array.
    """
    def __init__(self, source, **extra):
        super().__init__("RVAudioElement", **extra)
        self.file = source if isinstance(source, MediaFile) else MediaFile(source)
        self.display_name = self.file.name
        self.volume = 1.0
        self.in_point = 0
        self.out_point = 0
        self.play_rate = 1.0
        self.audio_type = 0     # TODO: Figure out what this is
        self.playback_mode = PLAYBACK_STOP

    def write(self):
        attrib = {
            "volume": self.volume,
            "inPoint": self.in_point,
            "outPoint": self.out_point,
            "playRate": self.play_rate,
            "audioType": self.audio_type,
            "loopBehavior": self.playback_mode,
            "displayName": self.display_name,
            "source": prepare_path(self.file.path),
        }
        super().update(attrib)
        return super().write()

    def read(self, element):
        super().read(element)

        self.file = MediaFile(unprepare_path(element.get("source")))
        self.volume = float(element.get("volume", str(self.volume)))
        self.in_point = int(element.get("inPoint", str(self.in_point)))
        self.out_point = int(element.get("outPoint", str(self.out_point)))
        self.play_rate = float(element.get("playRate", str(self.play_rate)))
        self.audio_type = int(element.get("audioType", str(self.audio_type)))
        self.playback_mode = element.get("loopBehavior", self.playback_mode)
        self.display_name = element.get("displayName", self.display_name)
        return self


DISPLAY_ELEMENTS = {
    "RVTextElement": TextElement,
    "RVImageElement": ImageElement,
    "RVVideoElement": VideoElement
}

MEDIA_ELEMENTS = {
    "RVImageElement": ImageElement,
    "RVVideoElement": VideoElement,
    "RVAudioElement": AudioElement
}
