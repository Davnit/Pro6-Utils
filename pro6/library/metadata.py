
from ..document import PresentationDocument

from os import path


class DocumentMetadata:
    def __init__(self, doc_path):
        self.path = doc_path
        self.name = path.basename(path.splitext(doc_path)[0])
        self.category = None
        self.last_used = None
        self.height = 0
        self.width = 0
        self.used_count = 0
        self.slide_count = 0
        self.uuid = None
        self.media = []

    def update(self, document=None):
        """ Reads metadata from the document file. """
        doc = document or PresentationDocument.load(self.path)
        self.category = doc.category
        self.last_used = doc.last_used
        self.height = doc.height
        self.width = doc.width
        self.used_count = doc.used_count
        self.slide_count = len(doc.slides())
        self.uuid = doc.get_uuid()
        self.media = [s.background.element.source for s in doc.slides() if s.background]
