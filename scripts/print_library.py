
from pro6.prefs import get_system_preferences
from pro6.document import Pro6Document

from sys import exit
from os import listdir
from os.path import isdir, splitext, join

# This script retrieves the active library path and parses+prints all of the documents in it.

prefs = get_system_preferences()
if not prefs.exists:
    print("Unable to find ProPresenter 6's configuration files.")
    exit(1)

dir_exists = isdir(prefs.general.library_path)

print("Current library: %s" % prefs.general.library_name)
print("\tPath: %s" % prefs.general.library_path)
print("\tExists: %s" % dir_exists)

if not dir_exists:
    exit(1)

for file in listdir(prefs.general.library_path):
    x = splitext(file)
    if x[1] == ".pro6":
        print("Loading '%s' ..." % x[0], end=" ")
        try:
            doc = Pro6Document.load(join(prefs.general.library_path, file))
        except:
            print("failed")
            raise
        print("success: %i slides." % len(doc.slides()))

print("Operation complete.")
