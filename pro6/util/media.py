
import hachoir.parser
import hachoir.metadata

from os import path


MEDIA_FORMATS = {
    "jpg": "JPEG image",
    "jpeg": "JPEG image",
    "png": "Portable Network Graphics image",
    "gif": "GIF image"
}


class InvalidMediaFileError(BaseException):
    def __init__(self, file):
        self.file = file


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

            self._extract_failed = (self.metadata is None)

        return self.metadata or {}

    def frame_size(self, default=None):
        """ Returns a tuple containing (width, height) of the media content. """
        default = default or (0, 0)
        if not isinstance(default, tuple) or len(default) != 2 \
                or not isinstance(default[0], int) or not isinstance(default[1], int):
            raise ValueError("Invalid frame size default value. Must be (width, height).")

        self.get_metadata()
        try:
            width = self.metadata.get("width")
            height = self.metadata.get("height")
            return width, height
        except ValueError:
            return default

    def duration(self):
        """ Returns the length of a media file, in seconds. """
        if not self.get_metadata():
            return 0
        try:
            dur = self.metadata.get("duration")
            return dur.total_seconds()
        except ValueError:
            return 0
