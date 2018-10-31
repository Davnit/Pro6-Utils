
from pro6 import Pro6Document, MediaCue, get_system_preferences

from os import curdir, listdir
from os.path import basename, splitext, isdir, isabs, join
from sys import argv, exit


def import_file(document, file_path):
    print("Importing '%s' ..." % basename(file_path), end=" ")
    try:
        document.append(MediaCue(file_path))
        print("success!")
    except ValueError as ex:
        print("failed: %s" % ex)


if len(argv) < 2:
    print("Invalid arguments, format: <document name> [media path]")
    exit(1)

doc_name = splitext(argv[1])[0]
if not doc_name.endswith(".pro6"):
    doc_name += ".pro6"

import_path = None if len(argv) < 3 else argv[2]

# Create the new document
print("Creating document: %s" % splitext(basename(doc_name))[0])
doc = Pro6Document()
if import_path is not None:
    # Are we importing a directory or just a single file?
    if isdir(import_path):
        for file in listdir(import_path):
            import_file(doc, join(import_path, file))
    else:
        import_file(doc, import_path)

print()
doc.print_outline()
print()

# Find the library or location to put the document.
if isabs(doc_name):
    # Document name specifies absolute path.
    doc.save(doc_name)
else:
    # Use the current library (if available) or current directory.
    pref = get_system_preferences()
    lib = pref.general.library_path if pref.exists else curdir
    doc.save(join(lib, doc_name))

print("Document saved as '%s'." % doc_name)
