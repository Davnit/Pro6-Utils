
from ..util.xmlhelp import RV_XML_VARNAME

import base64
from os import path, listdir
from os import remove as fs_delete
import re
import xml.etree.ElementTree as Xml


class DocumentLibrary:
    def __init__(self, title, library_path=None):
        self.title = title
        self.path = library_path
        self.documents = []

        for file in listdir(self.path):
            parts = path.splitext(file)
            if parts[1].lower() == ".pro6":
                self.documents.append(path.basename(parts[0]))

    def exists(self, title):
        """ Checks if a document with the given title is in the library. Case-insensitive. """
        return title.lower() in [d.lower() for d in self.documents]

    def delete(self, title):
        """ Deletes the document with the specified title. Case-insensitive. """
        if not self.exists(title):
            raise Exception("A document with that title could not be found.")

        # Find the proper case of the title.
        title = {t.lower(): t for t in self.documents}.get(title.lower())

        # Remove the file
        self.documents.remove(title)
        fs_delete(path.join(self.path, title + ".pro6"))

    def search(self, s, include_content=False, flags=re.IGNORECASE):
        """ Searches document titles and optionally content for given string. Supports regex. """

        results = []
        query = re.compile(s, flags)

        # Search titles first (quick)
        for title in self.documents:
            if query.search(title):
                results.append(title)

        # Optionally search "plain text" content, if available (slow)
        if include_content:
            # Only search documents that haven't already matched by title
            for title in [d for d in self.documents if d not in results]:
                # Directly read the XML for this to hopefully improve performance.
                tree = Xml.parse(path.join(self.path, title + ".pro6"))

                found_match = False
                # Search each slide
                for slide in tree.findall("RVDisplaySlide"):
                    # Check slide notes
                    notes = slide.get("notes")
                    if notes and query.search(notes):
                        found_match = True
                        break
                    else:
                        # Check 'PlainText' of slides (may not cover all the text)
                        subs = slide.findall("NSString[@" + RV_XML_VARNAME + "='PlainText']")
                        for encoded_text in [sub.text for sub in subs]:
                            text = base64.b64decode(encoded_text).decode()  # Base64 -> Bytes -> String
                            if query.search(text):
                                found_match = True
                                break

                if found_match:
                    results.append(title)

        return results
