
from pro6 import get_system_preferences

from sys import argv, exit
from os import curdir
from os.path import isabs, isfile, join
from xml.etree import ElementTree


if len(argv) < 5:
    print("Missing arguments: <document> <element_path> <attribute_key> <new_value>")
    exit(1)

doc_name = argv[1]
e_path = argv[2]
a_key = argv[3]
new_value = argv[4]

# If a full path wasn't given for the document, check the library.
if not isabs(doc_name):
    # Check for .pro6 extension
    if not doc_name.endswith(".pro6"):
        doc_name += ".pro6"

    print("Relative path provided. Locating current library...")
    prefs = get_system_preferences()
    lib_path = prefs.general.library_path if prefs.exists else curdir
    doc_name = join(lib_path, doc_name)

    if not isfile(doc_name):
        print("Document not found. Aborting...")
        exit(1)
    else:
        print("Document located: %s" % doc_name)

# Load the document XML
print("Reading document...")
doc = ElementTree.parse(doc_name)

# Find all elements matching the given path and change them
matching = doc.findall(e_path)
print("Found %i elements matching path." % len(matching))
for element in matching:
    element.set(a_key, new_value)

# Save the document
print("Saving changes...")
doc.write()

print("Operation complete.")
