
from pro6.document import PresentationDocument, MediaCue
from pro6.preferences import active as pro6_install
from pro6.util.constants import *

from argparse import ArgumentParser
from os import curdir, listdir, path
import sys


SCALE_MODES = {
    "fit": SCALE_FIT,
    "fill": SCALE_FILL,
    "stretch": SCALE_STRETCH
}

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".mov", ".mp4", ".avi"]


def import_file(document, file_path):
    if path.isdir(file_path):
        for file in listdir(file_path):
            import_file(document, path.join(file_path, file))
    elif path.isfile(file_path):
        if path.splitext(file_path)[1].lower() in SUPPORTED_EXTENSIONS:
            print("Importing file: %s" % file_path)
            try:
                document.append(MediaCue(file_path))
            except PermissionError:
                print("Error: Permission denied for file '%s'" % file_path)
        else:
            print("Skipping file '%s' (unsupported extension)" % file_path)

    else:
        print("Notice: '%s' is not a valid file or directory." % file_path)


def main():
    # Look for a ProPresenter installation to use default values from.
    library = None
    try:
        default_size = (pro6_install.output_width, pro6_install.output_height)
        scaling = {v: k for k, v in SCALE_MODES.items()}.get(pro6_install.foreground_scaling)
        library = pro6_install.get_library()
    except FileNotFoundError:
        default_size = (1280, 720)
        scaling = "fit"
        print("Notice: ProPresenter 6 installation not found. Default values will be used.")
    except ValueError as ve:
        print("Error: A problem was found with your ProPresenter installation:", ve)
        sys.exit(1)

    parser = ArgumentParser(description="Loads a directory or list of images into a ProPresenter document.")
    parser.add_argument("files", type=str, nargs='+', help="Path(s) of files or directories to import.")
    parser.add_argument("--title", type=str, help="The title of the document.")
    parser.add_argument("--category", type=str, default="Presentation", help="The type of document being created.")
    parser.add_argument("--width", type=int, default=default_size[0], help="The width of the created document.")
    parser.add_argument("--height", type=int, default=default_size[1], help="The height of the created document.")
    parser.add_argument("--interval", type=int, help="Seconds between each slide on the timeline.")
    parser.add_argument("--loop", type=bool, default=False, help="If the timeline should loop.")
    parser.add_argument("--scaling", type=str.lower, choices=list(SCALE_MODES.keys()), default=scaling,
                        help="How the image should be scaled to the document.")
    parser.add_argument("--outdir", type=str, help="The directory where the document should be saved.")
    args = parser.parse_args()

    # Validate some arguments
    if args.width <= 0:
        print("Invalid image width: %i - must be a positive integer." % args.width)
    if args.height <= 0:
        print("Invalid image height: %i - must be a positive integer." % args.height)

    # Create a new document with the given settings.
    print("Creating '%s' document with resolution %i x %i..." % (args.category, args.width, args.height))
    doc = PresentationDocument(args.category, args.height, args.width)

    # Import files to the document.
    for item in args.files:
        import_file(doc, item)
    print("DONE! Imported %i files to document." % len(doc.slides()))

    # Setup the optional timeline.
    if args.interval:
        print("Setting timeline interval to %i seconds (loop: %s)." % (args.interval, args.loop))
        doc.create_slideshow(args.interval, args.loop)

    # Determine a title for the document if none specified.
    title = args.title
    if not title:
        if len(args.files) == 1:
            title = path.basename(path.splitext(args.files[0])[0])
        else:
            title = "Imported files"

    # Save the document to disk (prefers: --outdir, active library, current directory)
    doc.path = path.join(args.outdir or (library.path if library else curdir()), title + ".pro6")
    doc.write()
    if library and not args.outdir:
        print("Document saved to library: %s" % title)
    else:
        print("Document saved: %s" % doc.path)


if __name__ == "__main__":
    main()
