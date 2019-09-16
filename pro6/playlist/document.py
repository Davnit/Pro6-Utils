
from .node import PlaylistNode

from ..preferences import install as pro6_install
from ..util.compat import *
from ..util.constants import RV_VERSION_NUMBER
from ..util.xmlhelp import XmlBackedObject, RV_XML_VARNAME, create_array

from os import path
from xml.etree import ElementTree as Xml


class PlaylistDocument(XmlBackedObject):
    active = None

    def __init__(self, **extra):
        defaults = {
            "versionNumber": RV_VERSION_NUMBER,
            "os": get_os(),
            "buildNumber": builds[get_os()]
        }
        defaults.update(extra)
        super().__init__("RVPlaylistDocument", defaults)
        self.path = None

        self.root = PlaylistNode("root")
        self.deletions = []

    def items(self):
        """ Returns the top-level playlist nodes in this document. """
        return list(self.root.children)

    def write(self, file_path=None):
        e = super().write()
        e.append(self.root.write())
        e.append(create_array("deletions", self.deletions))

        self.path = file_path or self.path
        if self.path:
            Xml.ElementTree(e).write(self.path, encoding="utf-8", xml_declaration=True)
        return e

    def read(self, element):
        super().read(element)

        self.root = PlaylistNode(None).read(element.find("RVPlaylistNode[@" + RV_XML_VARNAME + "='rootNode']"))
        return self

    @classmethod
    def load(cls, file_path):
        # Verify file extension
        if path.splitext(file_path)[1].lower() != ".pro6pl":
            raise Exception("The specified file is not a recognized ProPresenter 6 playlist document.")

        # Read the document into an XML structure
        tree = Xml.parse(file_path)

        # Interpret XML objects to ProPresenter context.
        document = cls().read(tree.getroot())
        document.path = file_path

        return document


if pro6_install:
    PlaylistDocument.active = \
        PlaylistDocument.load(path.join(pro6_install.playlist_path, pro6_install.active_library + ".pro6pl"))
