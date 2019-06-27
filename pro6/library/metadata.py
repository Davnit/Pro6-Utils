
from ..util.general import parse_date
from ..util.xmlhelp import RV_XML_VARNAME

from os import path
import xml.etree.ElementTree as Xml


class CCLI:
    def __init__(self, values):
        self.number = values.get("CCLISongNumber")
        self.artist = values.get("CCLIArtistCredits")
        self.author = values.get("CCLIAuthor")
        self.year = values.get("CCLICopyrightYear")
        if self.year and len(self.year) > 0:
            self.year = int(self.year)
        self.display = values.get("CCLIDisplay", "false").lower() in ["true", "1"]
        self.title = values.get("CCLISongTitle")
        self.publisher = values.get("CCLIPublisher")


class DocumentMetadata:
    def __init__(self, doc_path):
        self.path = doc_path
        self.name = path.basename(path.splitext(doc_path)[0])
        self.category = None
        self.last_used = None
        self.height = 0
        self.width = 0
        self.used_count = 0
        self.slide_count = 0
        self.uuid = None
        self.copyright = None
        self.media = []

    def update(self):
        """ Reads metadata from the document file. """
        root = Xml.parse(self.path).getroot()

        self.category = root.get("category", self.category)
        self.last_used = parse_date(root.get("lastDateUsed", self.last_used))
        self.height = int(root.get("height", self.height))
        self.width = int(root.get("width", self.width))
        self.used_count = int(root.get("usedCount", self.used_count))
        self.uuid = root.get("uuid", self.uuid)
        self.copyright = CCLI(root)

        slides = root.findall(".//RVDisplaySlide")
        self.slide_count = len(slides)

        self.media = []
        for slide in slides:
            background = slide.find("./RVMediaCue[@" + RV_XML_VARNAME + "='backgroundMediaCue']")
            if background:
                source = list(background)[0].get("source")
                if source:
                    self.media.append(source)
