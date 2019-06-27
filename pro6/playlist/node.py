
from .cues import DocumentCue

from ..document import MediaCue, AudioCue
from ..util.xmlhelp import XmlBackedObject, RV_XML_VARNAME, create_array

from datetime import datetime
from os import path


NODE_ROOT = "0"         # Root node of a playlist document, not generally used externally.
NODE_FOLDER = "2"       # Node containing child nodes which can be either folders or playlists.
NODE_PLAYLIST = "3"     # Node containing cues to documents and media files.


class PlaylistNode(XmlBackedObject):
    def __init__(self, name, node_type=NODE_PLAYLIST, **extra):
        defaults = {
            "smartDirectoryURL": None,
            "hotFolderType": 2
        }
        defaults.update(extra)
        super().__init__("RVPlaylistNode", defaults)

        self.name = name
        self.type = node_type
        self.expanded = False
        self.modified = datetime.now()

        self.children = []
        self.events = []
        self.parent = None

    @property
    def is_folder(self):
        return self.type in [NODE_ROOT, NODE_FOLDER]

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def add_path(self, fp):
        """ Adds a file to the playlist. """
        if self.type != NODE_PLAYLIST:
            raise Exception("Can't add file to playlist folder.")

        ext = path.splitext(fp)[1].lower()
        if ext == ".pro6":
            self.children.append(DocumentCue(fp))
        else:
            self.children.append(MediaCue.create(fp))
        self.modified = datetime.now()

    def find(self, item):
        """
            Finds a playlist with the given name or path.
                If path is str, returns the first playlist with a matching name.
                If path is a list, attempts to navigate through each item as a child node.
        """
        for child in self.children:
            is_list = isinstance(item, list)
            target = item[0] if is_list else item

            if hasattr(child, "name") and child.name.lower() == target.lower():
                # If it's a list and we're not on the last item, only return matching nodes.
                if is_list and len(item) > 1 and isinstance(child, PlaylistNode):
                    return child.find(path[1:] if len(item) > 2 else item[1])
                else:
                    return child
        return None

    def clear(self):
        """ Removes all children from this element. """
        self.children.clear()
        self.modified = datetime.now()

    def write(self):
        attrib = {
            "displayName": self.name,
            "modifiedDate": self.modified,
            "type": self.type,
            "isExpanded": self.expanded
        }
        if self.type == NODE_ROOT:
            attrib[RV_XML_VARNAME] = "rootNode"
        super().update(attrib)
        super().set_uuid()

        e = super().write()
        e.append(create_array("children", self.children))
        e.append(create_array("events", self.events))
        return e

    def read(self, element):
        super().read(element)

        self.name = element.get("displayName", self.name)
        self.type = element.get("type", self.type)
        self.expanded = element.get("isExpanded") in ["true", "1"]

        mod_date = element.get("modifiedDate")
        self.modified = datetime.fromisoformat(mod_date) if len(mod_date) > 0 else None

        self.children = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='children']"):
            if e.tag == "RVPlaylistNode":
                child = PlaylistNode(e.get("displayName")).read(e)
                child.parent = self
                self.children.append(child)
            elif e.tag == "RVMediaCue":
                self.children.append(MediaCue(e.get("source")).read(e))
            elif e.tag == "RVAudioCue":
                self.children.append(AudioCue(e.get("source")).read(e))
            elif e.tag == "RVDocumentCue":
                self.children.append(DocumentCue(e.get("filePath")).read(e))
            else:
                self.children.append(e)

        # TODO: Figure out what 'events' are and read them
        self.events = []
        for e in element.find("array[@" + RV_XML_VARNAME + "='events']"):
            self.events.append(e)

        return self
