
from pro6.constants import *

from uuid import uuid4
from datetime import datetime
from xml.etree.ElementTree import Element, ElementTree, SubElement
from urllib.parse import quote as url_quote
import os.path
import pathlib
import platform
import math


ATTRIB_VARNAME = "rvXMLIvarName"
ATTRIB_DICT_KEY = "rvXMLDictionaryKey"

RV_PLAYLIST_NODE = "RVPlaylistNode"
RV_RECT_3D = "RVRect3D"
RV_SHAPE_ELEMENT_STROKE_COLOR_KEY = "RVShapeElementStrokeColorKey"
RV_SHAPE_ELEMENT_STROKE_WIDTH_KEY = "RVShapeElementStrokeWidthKey"

NS_COLOR = "NSColor"
NS_NUMBER = "NSNumber"
NS_STRING = "NSString"

VIDEO_EXTENSIONS = ["mov", "mp4", "m4v", "avi", "mpg", "flv"]
IMAGE_EXTENSIONS = {
    "jpg": "JPEG image",
    "jpeg": "JPEG image",
    "png": "Portable Network Graphics image",
    "gif": "GIF image"
}


# Use for dict-to-xml. This object will be created as a raw text value rather than an attribute.
class XmlTextElement:
    def __init__(self, text, varname=None, vartype=None, **extra):
        self.text = text
        self.varname = varname
        self.vartype = vartype or ATTRIB_VARNAME
        self.extra = extra

    def get_xml(self, tag):
        e = Element(tag, { self.vartype: self.varname }, **self.extra)
        e.text = self.text
        return e


class Color:
    def __init__(self, r, g, b, a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def from_string(cls, s):
        r, g, b, a = 0.0, 0.0, 0.0, 1.0

        if s is None or len(s) == 0:
            return cls(r, g, b, a)

        if not isinstance(s, str):
            raise TypeError("Color expected string, got %s" % type(s).__name__)

        t = s.split(" ")
        if len(t) == 3 or len(t) == 4:
            r = float(t[0])
            g = float(t[1])
            b = float(t[2])
            if len(t) > 4:
                a = float(t[3])
            return cls(r, g, b, a)
        else:
            raise ValueError("Unable to convert string '%s' to color object. "
                             "Expected 3-4 values, got %i." % (s, len(t)))

    def get_value_string(self):
        parts = [self.r, self.g, self.b, self.a]
        s = []
        for val in parts:
            s.append(to_nums(val))

        return ' '.join(s)


class PointXY:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return "{%s, %s}" % (to_nums(self.x), to_nums(self.y))

    @classmethod
    def from_string(cls, s):
        if s is None or len(s) == 0:
            return PointXY()

        if not isinstance(s, str):
            raise TypeError("PointXY expected string, got %s" % type(s).__name__)

        if len(s) < 6 or (', ' not in s):
            raise ValueError("String does not contain a recognized X,Y pair.")

        parts = s[1:-1].split(', ')
        return cls(float(parts[0]), float(parts[1]))


class Rect3D:
    def __init__(self, width=0.0, height=0.0, rotation=0.0):
        self.width = width
        self.height = height
        self.rotation = rotation
        self.x = 0.0
        self.y = 0.0

    def set_xy(self, x, y):
        self.x, self.y = x, y

    def get_xml(self, name):
        parts = [self.x, self.y, self.rotation, self.width, self.height]
        s = []
        for val in parts:
            s.append(to_nums(val))
        return XmlTextElement("{%s}" % ' '.join(s), name).get_xml(RV_RECT_3D)

    @classmethod
    def from_xml(cls, element):
        if element is None:
            return None

        if not isinstance(element, Element):
            raise TypeError("Element must be an XML element.")
        if element.tag != RV_RECT_3D:
            raise ValueError("XML element does not represent a 3D rectangle.")

        items = element.text[1:-1].split()
        if len(items) != 5:
            raise ValueError("Rectangle object contains an unrecognized value.")

        rect = Rect3D(float(items[3]), float(items[4]), float(items[2]))
        rect.x = float(items[0])
        rect.y = float(items[1])
        return rect


class Shadow:
    def __init__(self, radius=4.0, color=None):
        self.enabled = True
        self.radius = radius
        self.color = color or Color(0, 0, 0, 1)
        self.source = PointXY(2.82843, -2.82843)

    def get_angle(self):
        return int(round(xy_to_angle(self.source.x, self.source.y), 0))

    def set_angle(self, angle):
        self.source = PointXY(*angle_to_xy(angle, self.get_length()))

    def get_length(self):
        return int(round(math.hypot(self.source.x, self.source.y), 0))

    def set_length(self, length):
        self.source = PointXY(*angle_to_xy(self.get_angle(), length))

    def get_xml(self):
        text = to_nums(self.radius) + "|%s|%s"
        text = text % (self.color.get_value_string(), str(self.source))
        return XmlTextElement(text, "shadow").get_xml("shadow")

    @classmethod
    def from_xml(cls, element):
        if element is None:
            return None

        if not isinstance(element, Element):
            raise TypeError("Element must be an XML element.")
        if element.tag != "shadow":
            raise ValueError("XML element does not represent a shadow.")

        items = element.text.split("|")
        if len(items) != 3:
            raise ValueError("shadow object contains an unrecognized value.")

        point = items[2][1:-1].split(', ')
        if len(point) != 2:
            raise ValueError("shadow object point format unrecognized.")

        shadow = Shadow(float(items[0]), Color.from_string(items[1]))
        shadow.x = float(point[0])
        shadow.y = float(point[1])
        return shadow


class Stroke:
    def __init__(self, width=0, color=None):
        self.enabled = True
        self.width = width
        self.color = color or Color(0, 0, 0, 1)

    def get_xml(self):
        d = {
            RV_SHAPE_ELEMENT_STROKE_COLOR_KEY: self.color.get_value_string(),
            RV_SHAPE_ELEMENT_STROKE_WIDTH_KEY: self.width
        }
        return to_xml_dictionary(d, "stroke")

    @classmethod
    def from_xml(cls, element):
        if element is None:
            return None

        if not isinstance(element, Element):
            raise TypeError("Element must be an XML element.")
        if element.tag != "dictionary" or element.get(ATTRIB_VARNAME) != "stroke":
            raise ValueError("XML element does not represent a stroke.")

        d = from_xml_dictionary(element)
        return Stroke(d.get(RV_SHAPE_ELEMENT_STROKE_WIDTH_KEY), d.get(RV_SHAPE_ELEMENT_STROKE_COLOR_KEY))


def dict_to_xml(d, key=None):
    if not isinstance(d, dict):
        raise TypeError("Expected dictionary, got %s" % type(d).__name__)

    if key is None:
        if len(d) > 1:
            raise ValueError("If no key is specified, the dictionary must be in tree format "
                             "starting with the root node.")

        key = next(iter(d.keys()))
        d = d[key]

    attributes = {}     # Items which should be added as attributes to the XML node. (strings)
    elements = []       # Items which should be added as sub-elements. (dictionaries)

    node = Element(key, attributes)

    for k, v in d.items():
        if isinstance(v, dict):
            elements.append(dict_to_xml(v, k))
        elif isinstance(v, list):
            top = Element("array", { ATTRIB_VARNAME: k })
            for item in v:
                top.append(dict_to_xml(item))
            elements.append(top)
        elif isinstance(v, XmlTextElement):
            elements.append(v.get_xml(k))
        else:
            attributes[k] = str(v)

    node.extend(elements)

    return node


def from_xml_dictionary(element):
    if not isinstance(element, (ElementTree, Element)):
        raise TypeError("Element must be an XML type.")

    if not element.tag == "dictionary":
        raise ValueError("XML element must be a dictionary")

    dic = {}
    for sub in element:
        key = sub.get(ATTRIB_DICT_KEY, sub.tag)

        if sub.tag == "array":
            value = [from_xml_dictionary(x) for x in sub.findall("dictionary")]
        elif sub.tag == NS_STRING:
            value = sub.text
        elif sub.tag == NS_NUMBER:
            hint = sub.get("hint").lower()
            if hint == "integer":
                value = int(sub.text)
            elif hint == "float":
                value = float(sub.text)
            else:
                raise ValueError("Unrecognized XML dictionary number hint: %s" % hint)
        elif sub.tag == NS_COLOR:
            value = Color.from_string(sub.text)
        else:
            raise ValueError("Unrecognized XML dictionary item: %s" % sub.tag)

        dic[key] = value

    return dic


def to_xml_dictionary(d, name=None):
    if not isinstance(d, dict):
        raise TypeError("Expected dictionary, got %s" % type(d).__name__)

    node = Element("dictionary")
    if name is not None:
        node.set(ATTRIB_VARNAME, name)

    for k, v in d.items():
        if isinstance(v, list):
            sub = Element("array")
            for x in v:
                sub.append(to_xml_dictionary(x))
        elif isinstance(v, str):
            sub = Element(NS_STRING)
            sub.text = v
        elif isinstance(v, int):
            sub = Element(NS_NUMBER, hint="integer")
            sub.text = str(v)
        elif isinstance(v, float):
            sub = Element(NS_NUMBER, hint="float")
            sub.text = str(v)
        elif isinstance(v, Color):
            sub = Element(NS_COLOR)
            sub.text = v.get_value_string()
        else:
            raise ValueError("Unsupported XML dictionary type: %s" % type(v).__name__)

        sub.set(ATTRIB_DICT_KEY, k)
        node.append(sub)

    return node


class XmlBackedObject:
    def __init__(self, element, parent=None):
        self.parent = None

        self._element = None
        self._children = []
        self._uuid = None

        if isinstance(element, Element):
            self._element = element
        else:
            raise TypeError("Element must be an XML element.")

        if parent is not None:
            if not isinstance(parent, XmlBackedObject):
                raise TypeError("Parent must be an XML backed object.")

            parent.append(self)
            self.parent = parent

    def save(self):
        """Saves all changes to the object and its children to the underlying XML elements."""
        for child in self._children:
            child.save()

    def append(self, obj):
        """Adds the specified object as a child to the current object.

            If obj is a list then all items in the list will be appended.
        """
        if not isinstance(obj, XmlBackedObject):
            raise TypeError("Invalid child type. Must be XmlBackedObject.")

        obj.parent = self
        self._children.append(obj)

    def remove(self, obj):
        """Removes the specified object from the children of the current object.

            Returns TRUE on success, FALSE on failure.
        """
        if obj in self._children:
            obj.parent = None
            self._children.remove(obj)
            return True
        else:
            return False

    def removeall(self):
        """Removes all the children from the current object."""
        self._children.clear()

    def get(self, key, default=None):
        """Returns the value of the attribute with the specified key."""
        return self._element.get(key, default)

    def set(self, key, value):
        """Sets the value of the attribute with the specified key."""
        self._element.set(key, value)

    def get_uuid(self):
        """Returns the UUID for the current object."""
        if self._uuid is None:
            self._uuid = self.get("UUID", self.get("uuid"))
            if self._uuid is None:
                self._uuid = get_uuid()
        return self._uuid

    def get_element(self):
        return self._element

    def _deep_search(self, value, name=None, tag=None):
        item = self._find_by(value, name, tag)
        if item is None:
            for child in self._children:
                item = child._deep_search(value, name, tag)
                if item is not None:
                    break
        return item

    def __iter__(self):
        return iter(self._children)

    def _save_uuid(self):
        self.set("UUID", self.get_uuid())

    def _find_by(self, value, name=None, tag=None, force=False):
        name = name or ATTRIB_VARNAME

        for e in self._element.findall(tag):
            for k, v in e.items():
                if name.lower() == k.lower():
                    if value == v:
                        return e

        if force and tag is not None:
            return SubElement(self._element, tag, { name: value })
        elif force:
            raise Exception("Unable to force create XML object with '%s=%s' "
                            "because no tag was specified." % (name, value))
        else:
            return None

    def _remove_by(self, value, name=None, tag=None):
        name = name or ATTRIB_VARNAME

        for e in self._element.findall(tag):
            to_remove = None
            for k, v in e.items():
                if name.lower() == k.lower():
                    if value == v:
                        to_remove = k
                        break
            if to_remove is not None:
                del e.attrib[to_remove]

    def _find_root(self):
        parent = self.parent
        while parent is not None:
            if hasattr(parent, "parent"):
                parent = parent.parent
            else:
                break
        return parent


def get_os():
    switch = {
        "windows": OS_WINDOWS,
        "darwin": OS_MACOSX
    }
    return switch.get(platform.system().lower(), 0)


def get_uuid():
    return str(uuid4())


def get_timestamp(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.isoformat("T")


def to_bool(s):
    return str(s).lower() in ["true", "1"]


def to_nums(value):
    value = value or 0
    i = int(value)
    return str(i) if i == value else str(value)


def normalize_path(file_path):
    plib = pathlib.Path(file_path)
    return url_quote(plib.as_posix() if get_os() == OS_WINDOWS else plib.as_uri()).replace("/", "%5C")


def find_abs_path(file_path, root, extension):
    if not os.path.isabs(file_path):
        file_path = os.path.join(root, file_path)
    if not file_path.endswith(extension):
        file_path += extension
    return file_path


def xy_to_angle(x, y):
    z = math.hypot(x, y)

    cx = ((y*y + z*z - x*x) / (2 * y * z))
    value = math.degrees(math.acos(cx))

    if x > 0 and y > 0:
        angle = 90 - value      # Quadrant 1
    elif x < 0 and y < 0:
        angle = 90 + value      # Quadrant 3
    elif x < 0 < y:
        angle = 360 - value     # Quadrant 4
    else:
        angle = value           # Quadrant 2

    return angle


def angle_to_xy(angle, distance):
    value = math.radians(angle)
    x = distance * math.cos(value)
    y = distance * math.sin(value)

    if (180 > angle > 90) or (360 > angle > 270):
        return y, x
    else:
        return x, y
