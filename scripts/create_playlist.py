
from pro6.library import DocumentLibrary
from pro6.playlist import PlaylistDocument, PlaylistNode, NODE_FOLDER
from pro6.preferences import active as pro6_install

from argparse import ArgumentParser
from os import path
from sys import exit


def main():
    parser = ArgumentParser(description="Creates a new ProPresenter playlist.")
    parser.add_argument("title", type=str, help="The title/path of the playlist. Use '\\n' to specify sub-folders.")
    parser.add_argument("items", type=str, nargs='+', help="Paths or names of items to add to the playlist.")
    parser.add_argument("--library", type=str, help="The name or path to the library where items should be found.")
    parser.add_argument("--parent", type=str, nargs='*', help="The tree path to where the playlist should be created.")
    parser.add_argument("--create-folders", action='store_true', help="If parent playlist folders should be created.")
    parser.add_argument("--overwrite", action='store_true', help="If the target playlist should be overwritten.")
    parser.add_argument("--document", type=str, help="The name or path of the playlist document to add the new list to.")
    args = parser.parse_args()

    library = None
    document = None

    # Set the document library source. Default is the active system library.
    if args.library:
        if not pro6_install:
            print("ERROR: A ProPresenter 6 installation could not be found on this system.")
            exit(1)

        title = {k.lower(): k for k in pro6_install.libraries.keys()}.get(args.library.lower())
        if not title:
            print("ERROR: The library '%s' could not be found." % args.library)
            exit(1)

        library = DocumentLibrary(pro6_install.libraries.get(title), title)
        if not args.document:
            document = PlaylistDocument.load(path.join(pro6_install.playlist_path, title + ".pro6pl"))
    elif pro6_install:
        library = DocumentLibrary(pro6_install.get_library(), pro6_install.active_library)
        if not args.document:
            default_path = path.join(pro6_install.playlist_path, pro6_install.active_library + ".pro6pl")
            document = PlaylistDocument.load(default_path)

    if library:
        print("Using library:", library.path)

    # Set the destination document file for the playlist. This defaults to the document associated with the library.
    #   If no library is specified or an install is not found, this parameter is required.
    if args.document:
        document = PlaylistDocument.load(path.normpath(path.expanduser(path.expandvars(args.document))))
    elif not document:
        print("ERROR: A ProPresenter 6 installation could not be found on this system and no playlist document "
              "was specified. Use --document='path/to/document.pro6pl' to target one.")
        exit(1)

    parent = document.root
    if args.parent:
        # Navigate to where the new playlist should be made.
        for item in args.parent:
            result = parent.find(item)
            if result:
                parent = result
            elif args.create_folders:
                node = PlaylistNode(item, NODE_FOLDER)
                parent.children.append(node)
                print("Created playlist node:", item)
                parent = node
            else:
                print("ERROR: The specified parent playlist could not be found. "
                      "Set the --create-folders option to create it.")
                exit(1)

    # Check if the playlist already exists.
    playlist = parent.find(args.title)
    if playlist:
        if args.overwrite:
            parent.children.remove(playlist)
            print("Removed existing playlist:", playlist.name)
        else:
            print("ERROR: A playlist with the name '%s' already exists. Use --overwrite to replace it." % playlist.name)
            exit(1)

    # Create the new playlist and add it.
    playlist = PlaylistNode(args.title)
    parent.children.append(playlist)

    # Add items to the playlist
    for item in args.items:
        item_path = path.normpath(path.expanduser(path.expandvars(item)))
        if not path.isfile(item_path) and path.basename(path.splitext(item_path)[0]) == item_path:
            # It's not a file so check the library.
            if library:
                print("Searching library for '%s' ..." % item_path)
                results = library.search(item_path)
                if len(results) > 0:
                    for meta in results:
                        playlist.add_path(meta.path)
                        print("Added library document:", meta.name)
                else:
                    print("ERROR: No results found for '%s' in the library." % item)
                    exit(1)
            else:
                print("ERROR: No library is available to search for documents.")
                exit(1)
        else:
            playlist.add_path(item_path)
            print("Added file:", item)

    document.write()
    print("Playlist saved to document:", path.basename(document.path))


if __name__ == "__main__":
    main()
