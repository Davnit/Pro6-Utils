
from .cues import TimeBasedCue
from ..util.xmlhelp import XmlBackedObject, create_array, RV_XML_VARNAME


class TimelineCue(TimeBasedCue):
    def __init__(self, obj, **extra):
        super().__init__("RVTimelineCue", extra)
        self.object = obj
        self.slide_index = 0

    def write(self):
        attrib = {
            "slideIndex": self.slide_index,
            "representedObjectUUID": self.object.get_uuid() if isinstance(self.object, XmlBackedObject) else self.object
        }
        super().update(attrib)
        return super().write()

    def read(self, element):
        super().read(element)
        self.slide_index = int(element.get("slideIndex", str(self.slide_index)))
        self.object = element.get("representedObjectUUID", self.object)
        return self


class Timeline(XmlBackedObject):
    def __init__(self, **extra):
        defaults = {
            RV_XML_VARNAME: "timeline"
        }
        defaults.update(extra)
        super().__init__("RVTimeline", defaults)

        self.offset = 0
        self.duration = 0
        self.selected_track = -1
        self.loop = False
        self.cues = []
        self.tracks = []

    def write(self):
        attrib = {
            "timeOffset": self.offset,
            "duration": self.duration,
            "selectedMediaTrackIndex": self.selected_track,
            "loop": self.loop,
        }
        super().update(attrib)

        e = super().write()
        e.append(create_array("timeCues", self.cues))
        e.append(create_array("mediaTracks"))       # TODO: Handle media tracks
        return e

    def read(self, element):
        super().read(element)

        self.offset = int(element.get("timeOffset", str(self.offset)))
        self.duration = int(element.get("duration", str(self.duration)))
        self.selected_track = int(element.get("selectedMediaTrackIndex", str(self.selected_track)))
        self.loop = (element.get("loop") == "true")

        self.cues = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='timeCues']").findall("RVTimelineCue"):
            self.cues.append(TimelineCue(None).read(e))

        self.tracks = []
        return self

    @classmethod
    def create_slideshow(cls, slides, interval, loop=False):
        tl = Timeline()
        tl.loop = loop
        tl.duration = (len(slides) * interval)

        for index in range(len(slides)):
            cue = TimelineCue(slides[index])
            cue.slide_index = index
            cue.display_name = " %i" % (index + 1)
            cue.timestamp = (index * interval)
            cue.enabled = True

            tl.cues.append(cue)
        return tl

