
from pro6.constants import *
import pro6.util as util
from pro6.document import Pro6Document, RV_MEDIA_CUE, MediaCue
from pro6.prefs import get_system_preferences

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element
import os.path
import sys


RV_PLAYLIST_DOCUMENT = "RVPlaylistDocument"
RV_PLAYLIST_NODE = "RVPlaylistNode"
RV_DOCUMENT_CUE = "RVDocumentCue"


prefs = get_system_preferences()
DEFAULT_PLAYLIST_LOCATION = os.path.join(prefs.general.user_data_path, "PlaylistData")
PLAYLIST_EXTENSION = ".pro6pl"


class DocumentCue(util.XmlBackedObject):
    def __init__(self, file, element=None, **extra):
        self._document = None

        if element is None:
            if isinstance(file, Pro6Document):
                if file.path is not None:
                    self._document = file
                    file = file.path
                else:
                    raise ValueError("Document must be saved to create a cue.")
            elif not isinstance(file, str):
                raise TypeError("File must be a Pro6Document or the path to one.")

            default = {
                "UUID": util.get_uuid(),
                "displayName": os.path.basename(file),
                "filePath": util.prepare_path(file),
                "selectedArrangementID": "00000000-0000-0000-0000-000000000000",
                "actionType": "0",
                "enabled": "true",
                "timeStamp": "0",
                "delayTime": "0"
            }
            element = Element(RV_DOCUMENT_CUE, default, **extra)
        else:
            self._document = None

        super().__init__(element)

    def append(self, obj):
        raise Exception("DocumentCue cannot have children.")

    def get_document(self):
        if self._document is None:
            self._document = Pro6Document.load(self.get("filePath"))
        return self._document


SUPPORTED_CUES = (DocumentCue, MediaCue)


class PlaylistNode(util.XmlBackedObject):
    def __init__(self, name, node_type=None, element=None, **extra):
        if element is None:
            default = {
                "displayName": str(name or "Untitled"),
                "UUID": util.get_uuid(),
                "smartDirectoryURL": "",
                "modifiedDate": util.get_timestamp(),
                "type": str(node_type or 3),
                "isExpanded": "false",
                "hotFolderType": "2"
            }
            element = Element(RV_PLAYLIST_NODE, default, **extra)

        super().__init__(element)

        self._child_node = self._find_by("children", tag="array", force=True)
        for child in self._child_node:
            if child.tag == RV_PLAYLIST_NODE:
                super().append(PlaylistNode(None, None, child))
            elif child.tag == RV_DOCUMENT_CUE:
                super().append(DocumentCue(None, child))
            elif child.tag == RV_MEDIA_CUE:
                super().append(MediaCue(None, child))

        self._find_by("events", tag="array", force=True)

        self.modified = False

    def is_root(self):
        return self.get("type") == NODE_TYPE_ROOT and self.get(util.ATTRIB_VARNAME) == "rootNode"

    def children(self):
        if self.get("type") == NODE_TYPE_PLAYLIST:
            return [cue for cue in self._children if isinstance(cue, SUPPORTED_CUES)]
        else:
            return [node for node in self._children if isinstance(node, PlaylistNode)]

    def find(self, node_path):
        s = node_path.split("/", maxsplit=1)
        for node in self.children():
            name = node.get("displayName").lower()
            if s[0].lower() == name or (s[0].lower() + ".pro6") == name:
                if isinstance(node, PlaylistNode) and len(s) > 1:
                    return node.find(s[1])
                elif len(s) == 1:
                    return node
        return None

    def save(self):
        self.set("modifiedDate", util.get_timestamp())
        super().save()

    def append(self, obj):
        if self.get("type") == NODE_TYPE_PLAYLIST:
            if not isinstance(obj, SUPPORTED_CUES):
                raise TypeError("Unsupported item type: %s" % type(obj).__name__)
        elif not isinstance(obj, PlaylistNode):
            raise ValueError("Only PlaylistNode objects can be added here.")

        super().append(obj)
        self._child_node.append(obj.get_element())
        self.modified = True

    def remove(self, obj):
        if super().remove(obj):
            self._child_node.remove(obj.get_element())
            self.modified = True

    def clear(self):
        for child in self.children():
            self.remove(child)


class PlaylistDocument(util.XmlBackedObject):
    def __init__(self, name, tree=None, **extra):
        if tree is None:
            osi = util.get_os()
            default = {
                "versionNumber": VERSION_NUMBER,
                "buildNumber": BUILD_NUMBER_WIN if osi == OS_WINDOWS else BUILD_NUMBER_OSX,
                "os": osi
            }
            tree = ElementTree(Element(RV_PLAYLIST_DOCUMENT, default, **extra))

        if not isinstance(tree, ElementTree):
            raise TypeError("Document tree must be an XML tree.")
        else:
            super().__init__(tree.getroot())

        self.path = name
        self._tree = tree
        self._root = self._find_by("rootNode", tag=RV_PLAYLIST_NODE)
        if self._root is None:
            root = PlaylistNode("root", NODE_TYPE_ROOT)
            root.set(util.ATTRIB_VARNAME, "rootNode")
            self._root = root.get_element()
            tree.getroot().append(self._root)
            super().append(root)
        else:
            super().append(PlaylistNode(None, element=self._root))

        self._find_by("deletions", tag="array", force=True)

    def root(self):
        child = [c for c in self._children if isinstance(c, PlaylistNode) and c.get("type") == NODE_TYPE_ROOT]
        return child[0] if len(child) > 0 else None

    def children(self):
        return self.root().children()

    def find(self, node_path):
        if node_path.startswith("/") or node_path.startswith("root/"):
            node_path = node_path.split("/")[1]
        return self.root().find(node_path)

    def append(self, obj):
        self.root().append(obj)

    def remove(self, obj):
        self.root().remove(obj)

    def save(self, path=None):
        super().save()

        # Save as ... new path
        if path is not None:
            self.path = path

        # Use the absolute path if available otherwise assume the default playlist location.
        self.path = util.find_abs_path(self.path, DEFAULT_PLAYLIST_LOCATION, PLAYLIST_EXTENSION)

        # Write the tree to file
        self._tree.write(self.path)

    def print_outline(self, node=None, tab=0):
        node = node or self.root()
        if not isinstance(node, PlaylistNode):
            raise TypeError("Can only print outline of PlaylistNode objects.")

        print("%s- %s" % ("\t" * tab, node.get("displayName", "[unnamed]")))
        for child in node.children():
            if isinstance(child, PlaylistNode):
                self.print_outline(child, tab+1)
            else:
                print("%s-> %s" % ("\t" * (tab+1), child.get("displayName", "[unnamed]")))

    @staticmethod
    def load(path):
        path = util.find_abs_path(path, DEFAULT_PLAYLIST_LOCATION, PLAYLIST_EXTENSION)

        document = PlaylistDocument(path, ET.parse(path))
        document.path = path
        return document

    @staticmethod
    def get_current():
        path = util.find_abs_path(prefs.general.library_name, DEFAULT_PLAYLIST_LOCATION, PLAYLIST_EXTENSION)
        if os.path.isfile(path):
            return PlaylistDocument.load(path)
        else:
            return PlaylistDocument(path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No source file specified.")
        sys.exit(1)

    doc = PlaylistDocument.load(sys.argv[1])
    doc.print_outline()
