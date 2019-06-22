
from .slide import DisplaySlide
from ..util.xmlhelp import XmlBackedObject, create_array, RV_XML_VARNAME


class SlideGroup(XmlBackedObject):
    def __init__(self, name=None, color=None, **extra):
        super().__init__("RVSlideGrouping", extra)

        self.name = name or ""
        self.color = color or "1 1 1 0"
        self.slides = []

    def write(self):
        attrib = {
            "name": self.name,
            "color": self.color
        }
        super().update(attrib)
        super().set_uuid()

        e = super().write()
        e.append(create_array("slides", self.slides))
        return e

    def read(self, element):
        super().read(element)

        self.name = element.get("name")
        self.color = element.get("color", self.color)

        self.slides = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='slides']").findall("RVDisplaySlide"):
            self.slides.append(DisplaySlide().read(e))
        return self
