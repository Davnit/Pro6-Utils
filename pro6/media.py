
import hachoir.parser
import hachoir.metadata

from sys import argv, exit


def get_metadata(source):
    parser = hachoir.parser.createParser(source)
    if not parser:
        return None
    with parser:
        return hachoir.metadata.extractMetadata(parser)


def get_frame_size(source, default=None):
    default = default or (0, 0)
    if not isinstance(default, tuple) or len(default) != 2:
        raise ValueError("Frame size default value not recognized. Must be (width, height).")

    meta = get_metadata(source) if isinstance(source, str) else source
    if meta is None:
        return default

    try:
        return int(meta.get("width")), int(meta.get("height"))
    except ValueError:
        return default


def get_length(source, scale=600):
    meta = get_metadata(source) if isinstance(source, str) else source
    if meta is None:
        return 0

    try:
        value = meta.get("duration").total_seconds()
        return int(value * int(scale))
    except ValueError:
        return 0


if __name__ == '__main__':
    if len(argv) < 2:
        print("No file specified.")
        exit(1)

    for i in range(1, len(argv)):
        print("Metadata for %s" % argv[i])
        meta = get_metadata(argv[i])
        for m in meta:
            for v in m.values:
                print("%s: %s" % (m.key, v.value))
        print("")
