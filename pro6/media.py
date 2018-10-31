
import hachoir.parser
import hachoir.metadata
from sys import argv, exit


def get_metadata(source):
    parser = hachoir.parser.createParser(source)
    if not parser:
        return None

    with parser:
        try:
            return hachoir.metadata.extractMetadata(parser)
        except Exception as ex:
            print("Failed to get metadata for file '%s': %s" % (source, ex))

    return None


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
