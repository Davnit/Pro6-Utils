
from .elements import MEDIA_ELEMENTS, MediaElement, AudioElement

from ..preferences import install as pro6_install

from ..util.constants import *
from ..util.general import unprepare_path
from ..util.xmlhelp import XmlBackedObject, RV_XML_VARNAME

from os import path, listdir, remove


class MediaCue(XmlBackedObject):
    def __init__(self, source, element=None, **extra):
        super().__init__("RVMediaCue", extra)
        self.source = source

        self.display_name = path.basename(source) if source else None
        self.alignment = ALIGN_CENTER
        self.layer = LAYER_FOREGROUND
        self.action = "0"               # TODO: Figure out what this is.
        self.added = None
        self.delay = 0.0
        self.enabled = True
        self.tags = None
        self.timestamp = 0.0

        self.element = element or (MediaElement.create(self.source) if source else None)
        self.next_cue = None            # UUID of linked cue object

    def reset_thumbnail(self):
        """ Resets the cached thumbnail for this element. """
        if not pro6_install:
            raise Exception("ProPresenter installation not found.")

        # This file name seems to vary between upper(), lower() and .png/.jpg so just iterate and compare base.lower()
        for file in listdir(pro6_install.thumbnail_cache):
            if path.basename(path.splitext(file)[0]).lower() == self.get_uuid().lower():
                remove(path.join(pro6_install.thumbnail_cache, file))
                return True

    def write(self):
        attrib = {
            "displayName": self.display_name,
            "alignment": self.alignment,
            "behavior": self.layer,         # "behavior" refers to the layering, not playback in this context
            "actionType": self.action,
            "dateAdded": self.added,
            "delayTime": self.delay,
            "enabled": self.enabled,
            "tags": self.tags,
            "timeStamp": self.timestamp,
            "nextCueUUID": self.next_cue.get_uuid() if isinstance(self.next_cue, XmlBackedObject) else self.next_cue
        }

        super().update(attrib)
        e = super().write()
        if isinstance(self.element, XmlBackedObject):
            media = self.element.write()
            media.set(RV_XML_VARNAME, "element")
            e.append(media)
            if self.element.get_uuid():
                e.set("UUID", self.element.get_uuid())
            else:
                super().set_uuid()
        else:
            if not self.element:
                raise TypeError("Cue media must not be NoneType.")
            e.append(self.element)
        return e

    def read(self, element):
        super().read(element)

        self.display_name = element.get("displayName", self.display_name)
        self.alignment = element.get("alignment", self.alignment)
        self.layer = element.get("behavior", self.layer)
        self.action = element.get("actionType", self.action)
        self.added = element.get("dateAdded", self.added)
        self.delay = float(element.get("delayTime", str(self.delay)))
        self.enabled = (element.get("enabled") == "true")
        self.tags = element.get("tags", self.tags)
        self.timestamp = float(element.get("timeStamp", str(self.timestamp)))
        self.next_cue = element.get("nextCueUUID")

        # The child media element could be a few different types.
        children = list(element)
        if len(children) > 1:
            raise ValueError("Ambiguous MediaCue child elements. Found %i." % len(children))

        source = unprepare_path(children[0].get("source"))
        if children[0].tag in MEDIA_ELEMENTS:
            self.element = MEDIA_ELEMENTS[children[0].tag](source).read(children[0])
            self.source = source
        else:
            print("Unsupported media element found in cue '%s': %s" % (self.display_name, children[0].tag))
            self.element = children[0]
            self.source = source
        return self

    @classmethod
    def create(cls, source, **extra):
        element = MediaElement.create(source, **extra)
        if isinstance(element, AudioElement):
            return AudioCue(source, element, **extra)
        else:
            return MediaCue(source, element, **extra)


class AudioCue(MediaCue):
    def __init__(self, source, element=None, **extra):
        super().__init__(source, element, **extra)
        self._tag = "RVAudioCue"


class TimeBasedCue(XmlBackedObject):
    def __init__(self, tag, attrib):
        super().__init__(tag, attrib)
        self.action = "0"
        self.delay = 0.0
        self.display_name = None
        self.enabled = False
        self.timestamp = 0.0

    def write(self):
        attrib = {
            "actionType": self.action,
            "delayTime": self.delay,
            "displayName": self.display_name,
            "enabled": self.enabled,
            "timeStamp": self.timestamp
        }
        super().update(attrib)
        super().set_uuid()
        return super().write()

    def read(self, element):
        super().read(element)

        self.action = element.get("actionType", self.action)
        self.delay = float(element.get("delayTime", str(self.delay)))
        self.display_name = element.get("displayName", self.display_name)
        self.enabled = element.get("enabled") == "true"
        self.timestamp = float(element.get("timeStamp", str(self.timestamp)))
        return self
