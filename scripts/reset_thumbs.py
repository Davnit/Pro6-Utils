
from pro6.document import PresentationDocument
from pro6.preferences import install as pro6_install

from argparse import ArgumentParser
from os import path
from sys import exit


def main():
    parser = ArgumentParser(description="Resets thumbnails for media associated with a document.")
    parser.add_argument("document", type=str, help="The path to or name of the document to reset.")
    args = parser.parse_args()

    # Check if a document name was given instead of a path and resolve it.
    if not args.document.endswith(".pro6"):
        if not pro6_install:
            print("ERROR: No ProPresenter installation found.")
            exit(1)
        library = pro6_install.get_library()
        if not path.isdir(library):
            print("ERROR: ProPresenter library not found.")
            exit(1)
        args.document = path.join(library, args.document + ".pro6")
    else:
        args.document = path.expanduser(path.normpath(args.document))

    document = PresentationDocument.load(args.document)
    for slide in [s for s in document.slides() if s.background]:
        print("Resetting '%s' (%s)..." % (slide.background.display_name, slide.background.get_uuid()))
        slide.background.element.reset_thumbnail()


if __name__ == "__main__":
    main()
