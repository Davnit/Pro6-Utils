
import hachoir.parser
import hachoir.metadata


MEDIA_FORMATS = {
    "jpg": "JPEG image",
    "jpeg": "JPEG image",
    "png": "Portable Network Graphics image",
    "gif": "GIF image"
}


class MediaFile:
    def __init__(self, source):
        self.source = source
        self.metadata = {}

        parser = hachoir.parser.createParser(source)
        if not parser:
            raise Exception("Unable to extract metadata from file '%s'" % source)

        with parser:
            self.metadata = hachoir.metadata.extractMetadata(parser)

    def frame_size(self, default=None):
        """ Returns a tuple containing (width, height) of the media content. """
        default = default or (0, 0)
        if not isinstance(default, tuple) or len(default) != 2 \
            or not isinstance(default[0], int) or not isinstance(default[1], int):
            raise ValueError("Invalid frame size default value. Must be (width, height).")

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
        return self.metadata.get("duration").total_seconds() if "duration" in self.metadata else 0
