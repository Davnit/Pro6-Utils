
import hachoir.parser
import hachoir.metadata

from os import path


MEDIA_FORMATS = {
    "jpg": "JPEG image",
    "jpeg": "JPEG image",
    "png": "Portable Network Graphics image",
    "gif": "GIF image"
}


class MediaFile:
    def __init__(self, source):
        self.path = source or ""
        self.metadata = None
        self._extract_failed = False

    @property
    def name(self):
        return path.basename(self.path)

    @property
    def format(self):
        return MEDIA_FORMATS.get(path.splitext(self.path)[1][1:].lower())

    def exists(self):
        return path.isfile(self.path)

    def get_metadata(self, reload=False):
        """ Parses and returns file metadata. Invalid media files return None. """
        if (self._extract_failed is False and self.metadata is None) or reload:
            if self.exists():
                parser = hachoir.parser.createParser(self.path)
                if parser:
                    with parser:
                        self.metadata = hachoir.metadata.extractMetadata(parser)

            if not self.metadata:
                self._extract_failed = True

        return self.metadata

    def frame_size(self, default=None):
        """ Returns a tuple containing (width, height) of the media content. """
        default = default or (0, 0)
        if not isinstance(default, tuple) or len(default) != 2 \
                or not isinstance(default[0], int) or not isinstance(default[1], int):
            raise ValueError("Invalid frame size default value. Must be (width, height).")

        self.get_metadata()
        if "width" not in self.metadata or "height" not in self.metadata:
            return default
        else:
            width = self.metadata.get("width")
            height = self.metadata.get("height")
            if len(width) == 0 or len(height) == 0:
                return default
            else:
                return int(width), int(height)

    def duration(self):
        """ Returns the length of a media file, in seconds. """
        self.get_metadata()
        return self.metadata.get("duration").total_seconds() if "duration" in self.metadata else 0
