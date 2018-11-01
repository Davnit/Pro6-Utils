
from pro6.document import DOCUMENT_EXTENSION, MediaCue
from pro6.playlist import PlaylistDocument, PlaylistNode, DocumentCue
from pro6.util import find_abs_path
from pro6.prefs import get_system_preferences
from pro6.constants import *

from os import listdir
from os.path import basename, splitext, isdir, join, isabs
from sys import argv, exit


prefs = get_system_preferences()


def import_file(playlist, file_path):
    print("Importing '%s' ..." % basename(file_path), end=" ")
    try:
        ext = splitext(file_path)[1]
        if len(ext) == 0 or ext.lower() == DOCUMENT_EXTENSION:
            if not isabs(file_path):
                file_path = find_abs_path(file_path, prefs.general.library_path, DOCUMENT_EXTENSION)
            item = DocumentCue(file_path)
        else:
            item = MediaCue(file_path)
        playlist.append(item)
        print("success!")
    except Exception as ex:
        print("failed: %s" % ex)


if len(argv) < 2:
    print("Invalid arguments, format: <playlist name> [files...]")
    exit(1)

list_name = argv[1]
files = [] if len(argv) == 2 else argv[2:]

# Find the currently active playlist
doc = PlaylistDocument.get_current()
print("Using playlist: %s" % doc.path)

# Find the location where the new playlist should go
play = doc
while "/" in list_name:
    s = list_name.split("/", maxsplit=1)
    sub = play.find(s[0])
    if sub is None:
        print("Adding node: %s" % s[0])
        sub = PlaylistNode(s[0], NODE_TYPE_FOLDER)
        play.append(sub)
    play = sub
    list_name = s[1]

# If the playlist already exists, overwrite it.
pl = play.find(list_name)
if pl is not None:
    pl.clear()
else:
    playlist = PlaylistNode(list_name, NODE_TYPE_PLAYLIST)
    play.append(pl)

# Import the specified files
if len(files) > 0:
    for file in files:
        if isdir(file):
            for sf in listdir(file):
                import_file(pl, join(file, sf))
        else:
            import_file(pl, file)

# Save the playlist
doc.save()
print("Playlist saved to '%s'." % argv[1])
