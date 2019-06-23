
from .cues import MediaCue, AudioCue
from .group import SlideGroup
from .slide import DisplaySlide
from .timeline import Timeline

from ..preferences import active as pro6_install

from ..util.compat import *
from ..util.constants import RV_VERSION_NUMBER
from ..util.xmlhelp import XmlBackedObject, create_array, RV_XML_VARNAME

from os import path
from xml.etree import ElementTree as Xml


class PresentationDocument(XmlBackedObject):
    def __init__(self, category, height=None, width=None, **extra):
        defaults = {
            "docType": 0,
            "versionNumber": RV_VERSION_NUMBER,
            "selectedArrangementID": None,
            "resourcesDirectory": None,
            "CCLISongTitle": None,
            "chordChartPath": None,
            "os": get_os(),
            "buildNumber": builds[get_os()]
        }
        defaults.update(extra)
        super().__init__("RVPresentationDocument", defaults)
        self.path = None

        self.category = category

        # System settings will be used for some default values if not specified.
        self.height = height or (pro6_install.output_height if pro6_install else 720)
        self.width = width or (pro6_install.output_width if pro6_install else 1280)

        self.used_count = 0
        self.last_used = None
        self.notes = None
        self.background_color = None

        # Create the default group.
        group = SlideGroup()
        group.slides.append(DisplaySlide())

        self.groups = [group]
        self.arrangements = []
        self.timeline = Timeline()

    def slides(self):
        """ Returns all of the slide objects in the document. """
        return [s for group in self.groups for s in group.slides]

    def append(self, item):
        """ Adds an item to the end of the document. """
        if isinstance(item, SlideGroup):
            self.groups.append(item)
        elif isinstance(item, DisplaySlide):
            # If the document contains no groups, add one.
            if len(self.groups) == 0:
                self.groups.append(SlideGroup())

            self.groups[-1].slides.append(item)
        elif isinstance(item, AudioCue):
            slide = DisplaySlide()
            slide.cues.append(item)
            self.append(slide)
        elif isinstance(item, MediaCue):
            slide = DisplaySlide()
            slide.background = item
            self.append(slide)
        elif isinstance(item, str) and path.isfile(item):
            cue = MediaCue.create(item)
            self.append(cue)
        else:
            raise TypeError("Can't append item to document - type not supported: %s" % type(item).__name__)

    def remove(self, item):
        """ Removes an item or the item at the given index from the document. """
        if isinstance(item, SlideGroup):
            if item not in self.groups:
                raise ValueError("Group '%s' not found in document." % item.name)
            self.groups.remove(item)
        elif isinstance(item, DisplaySlide):
            for group in self.groups:
                if item in group.slides:
                    group.slides.remove(item)
                    return
            raise ValueError("Slide '%s' not found in document." % item.label)
        elif isinstance(item, int):
            slides = self.slides()
            if item < 0 or item > (len(slides) - 1):
                raise ValueError("Slide index out of range: %i (%i slides)" % (item, len(slides)))
            self.remove(slides[item])
        else:
            raise TypeError("Invalid slide object type: %s" % type(item).__name__)

    def clear(self):
        """ Removes all slides and groups from the document and resets the timeline. """
        self.groups.clear()
        self.timeline = Timeline()

    def create_slideshow(self, interval, loop=False):
        """ Creates a slideshow from the document with the specified interval and looping behavior. """
        self.timeline = Timeline.create_slideshow(self.slides(), interval, loop)

    def write(self, file_path=None):
        attrib = {
            "height": self.height,
            "width": self.width,
            "usedCount": self.used_count,
            "lastDateUsed": self.last_used,
            "category": self.category,
            "notes": self.notes,
            "drawingBackgroundColor": (self.background_color is not None)
        }

        # Set the background color if it's used - otherwise leave it alone.
        if self.background_color is not None:
            attrib["backgroundColor"] = self.background_color
        super().update(attrib)

        # Start writing the element
        e = super().write()
        e.append((self.timeline or Timeline()).write())     # A timeline is required so use default if None
        e.append(create_array("groups", self.groups))
        e.append(create_array("arrangements", self.arrangements))

        # Save the document to disk.
        self.path = file_path or self.path
        if self.path:
            Xml.ElementTree(e).write(self.path, encoding="utf-8", xml_declaration=True)
        return e

    def read(self, element):
        super().read(element)

        self.height = int(element.get("height", str(self.height)))
        self.width = int(element.get("width", str(self.width)))
        self.category = element.get("category", str(self.category))
        self.used_count = int(element.get("usedCount", str(self.used_count)))
        self.last_used = element.get("lastDateUsed", self.last_used)
        self.notes = element.get("notes", self.notes)
        self.background_color = element.get("backgroundColor") \
            if element.get("drawingBackgroundColor") == "true" else None

        self.groups = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='groups']").findall("RVSlideGrouping"):
            self.groups.append(SlideGroup().read(e))
        self.timeline = Timeline().read(element.find("RVTimeline"))

        self.arrangements = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='arrangements']"):
            self.arrangements.append(e)
        return self

    @classmethod
    def load(cls, file_path):
        # Verify file extension
        if path.splitext(file_path)[1].lower() != ".pro6":
            raise Exception("The specified file is not a recognized ProPresenter 6 document.")

        # Read the document into an XML structure
        tree = Xml.parse(file_path)

        # Kick off the chain to interpret the XML objects in a ProPresenter context.
        document = cls(None).read(tree.getroot())
        document.path = file_path

        return document
