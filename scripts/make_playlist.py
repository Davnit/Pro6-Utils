#!/usr/bin/env python3

from pro6.document import DOCUMENT_EXTENSION, MediaCue
from pro6.playlist import PlaylistDocument, PlaylistNode, DocumentCue
from pro6.util import find_abs_path
from pro6.prefs import get_system_preferences
from pro6.constants import *

from argparse import ArgumentParser
from os import listdir
from os.path import basename, splitext, isdir, join, isabs

prefs = get_system_preferences()

parser = ArgumentParser()
parser.add_argument('playlist_name', help='The name of the playlist.')
parser.add_argument('files', nargs='*', help='A list of files to add to the playlist as cues.')


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


args = parser.parse_args()
list_name = args.playlist_name

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
if args.files and len(args.files) > 0:
    for file in args.files:
        if isdir(file):
            for sf in listdir(file):
                import_file(pl, join(file, sf))
        else:
            import_file(pl, file)

# Save the playlist
doc.save()
print("Playlist saved to '%s'." % args.playlist_name)
