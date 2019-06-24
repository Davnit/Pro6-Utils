
from pro6.library import DocumentLibrary
from pro6.preferences import active as pro6_install

from argparse import ArgumentParser
from os import path
from sys import exit


def main():
    parser = ArgumentParser(description="Returns information on a ProPresenter library.")
    parser.add_argument("--library", type=str, help="The path to the library.")
    args = parser.parse_args()

    library = None
    if not args.library:
        if not pro6_install:
            print("ERROR: No library specified and a ProPresenter installation could not be found.")
            exit(1)
        else:
            library = DocumentLibrary(pro6_install.active_library, pro6_install.get_library())
    else:
        title = path.basename(args.library[:-1] if args.library[-1] in ['/', '\\'] else args.library)
        library = DocumentLibrary(title, args.library)

    print("Loading library '%s'..." % library.title)
    library.load_metadata()

    categories = {}
    not_used = []
    for name, doc in library.documents.items():
        if doc.category not in categories:
            categories[doc.category] = []
        categories[doc.category].append(doc)

        if not doc.last_used:
            not_used.append(doc)

    print("Scanned %i documents." % len(library.documents))
    print("Categories:", ', '.join(["%s (%i)" % (k, len(v)) for k,v in categories.items()]))
    print("Documents not used: %i" % len(not_used))
    for doc in not_used:
        print("\t%s" % doc.name)


if __name__ == "__main__":
    main()
