#!/usr/bin/env python3

from pro6.document import Pro6Document, MediaCue

from os import listdir
from os.path import basename, splitext, isdir, isfile, join
from sys import argv, exit


def import_file(document, file_path):
    print("Importing '%s' ..." % basename(file_path), end=" ")
    try:
        document.append(MediaCue(file_path))
        print("success!")
    except Exception as ex:
        print("failed: %s" % ex)


if len(argv) < 2:
    print("Invalid arguments, format: <document name> [files...]")
    exit(1)

doc_name = argv[1]
files = [] if len(argv) == 2 else argv[2:]

# Create the new document
print("Creating document: %s" % splitext(basename(doc_name))[0])
doc = Pro6Document(doc_name)

# Import the specified files
if len(files) > 0:
    for file in files:
        if isdir(file):
            for sf in listdir(file):
                import_file(doc, join(file, sf))
        elif isfile(file):
            import_file(doc, file)
        else:
            print("The specified file '%s' could not be found." % file)

# Save the document
doc.save()
print("Document saved to '%s'." % doc.path)
