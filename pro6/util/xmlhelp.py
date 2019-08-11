
from .general import create_uuid, format_date

from abc import ABC, abstractmethod
from datetime import datetime
import math
import xml.etree.ElementTree as Xml


# XML document constants
RV_XML_VARNAME = "rvXMLIvarName"
RV_XML_DICTKEY = "rvXMLDictionaryKey"


def create_array(name, items=None):
    e = Xml.Element("array", {RV_XML_VARNAME: name})
    if items:
        if not isinstance(items, list):
            raise TypeError("Array items must be a list of XML objects.")
        for item in items:
            if isinstance(item, XmlBackedObject):
                e.append(item.write())
            elif isinstance(item, Xml.Element):
                e.append(item)
            else:
                raise TypeError("Array items must be XML objects, got '%s'." % type(item).__name__)
    return e


def to_nums(value):
    value = value or 0
    i = int(value)
    return str(i) if i == value else str(value)


def normalize_tree(tree):
    # Normalizes values for attributes of all elements in an XML tree to strings.
    converters = {
        bool: lambda x: str(x).lower()
    }

    for element in tree.findall("//"):
        for k, v in element.items():
            if v is None:
                element.attrib[k] = ""
            else:
                element.attrib[k] = converters.get(type(v), lambda x: str(x))(v)
    return tree


class XmlBackedObject(ABC):
    def __init__(self, tag, attrib=None):
        self._tag = tag
        if attrib and not isinstance(attrib, dict):
            raise TypeError("XML object attributes must be a dictionary.")
        self._attrib = attrib or {}

    def get_uuid(self):
        """ Returns a UUID representing this object. """
        return self._attrib.get("UUID")

    def set_uuid(self):
        """ Generates a new UUID to represent this object, if one is not already set. """
        if "UUID" not in self._attrib:
            self._attrib["UUID"] = create_uuid()

    def update(self, attrib):
        """ Updates this object's XML attributes with new values from a dictionary. """
        self._attrib.update(attrib)
        return self._attrib

    @abstractmethod
    def write(self):
        """ Returns an XML Element representing this object. """
        # Serialize values to str.
        attrib = dict(self._attrib)
        for k, v in attrib.items():
            if v is None:
                attrib[k] = ""
            elif isinstance(v, bool):
                attrib[k] = str(v).lower()
            elif isinstance(v, datetime):
                attrib[k] = format_date(v)
            elif not isinstance(v, str):
                attrib[k] = str(v)

        return Xml.Element(self._tag, attrib)

    @abstractmethod
    def read(self, element):
        """ Updates this object to represent the given XML Element. """
        if element.tag != self._tag:
            raise TypeError("'%s' element could not be converted to a %s object." % (element.tag, self._tag))
        self._attrib = element.attrib

        # Convert empty strings to 'None' values.
        for k, v in self._attrib.items():
            if v == "":
                self._attrib[k] = None
        return self


class ColorString:
    def __init__(self, r, g, b, a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __str__(self):
        return ' '.join(to_nums(v) for v in [self.r, self.g, self.b, self.a])

    @classmethod
    def parse(cls, s):
        r, g, b, a = 0.0, 0.0, 0.0, 1.0

        # No values -> default values
        if s is None or len(s) == 0:
            return None

        # Check for valid type
        if not isinstance(s, str):
            raise TypeError("Cannot parse type '%s' to ColorString (needs str)" % type(s).__name__)

        parts = s.split(' ')
        if len(parts) in [3, 4]:
            r = float(parts[0])
            g = float(parts[1])
            b = float(parts[2])
            if len(parts) > 3:
                a = float(parts[3])
            return cls(r, g, b, a)
        else:
            raise ValueError("Cannot parse string '%s' to ColorString. Expected 3-4 values, got %i." % (s, len(parts)))


class PointXY:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return '{' + to_nums(self.x) + ', ' + to_nums(self.y) + '}'

    @classmethod
    def parse(cls, s):
        if s is None or len(s) == 0:
            return cls()

        if not isinstance(s, str):
            raise TypeError("Cannot parse type '%s' to PointXY (needs str)" % type(s).__name__)

        if len(s) < 6 or (',' not in s):
            raise ValueError("String does not contain a recognized X,Y pair.")

        parts = [p.strip() for p in s[1:-1].split(',')]
        return cls(float(parts[0]), float(parts[1]))


class Rect3D(XmlBackedObject):
    def __init__(self, width=0.0, height=0.0, rotation=0.0, x=0.0, y=0.0):
        super().__init__("RVRect3D")

        self.width = width
        self.height = height
        self.rotation = rotation
        self.x = x
        self.y = y

    def write(self, name=None):
        e = super().write()
        if name:
            e.attrib[RV_XML_VARNAME] = name
        e.text = '{' + ' '.join(to_nums(v) for v in [self.x, self.y, self.rotation, self.width, self.height]) + '}'
        return e

    def read(self, element):
        super().read(element)

        parts = element.text[1:-1].split(' ')
        if len(parts) != 5:
            raise ValueError("Rectangle object has unrecognized value: '%s'" % element.text)

        self.x = float(parts[0])
        self.y = float(parts[1])
        self.rotation = float(parts[2])
        self.width = float(parts[3])
        self.height = float(parts[4])
        return self


class Shadow(XmlBackedObject):
    def __init__(self, radius=4.0, color=None):
        super().__init__("shadow")
        self.enabled = False     # Not actually part of the object but used to set an attribute on the parent.
        self.radius = radius
        self.color = color or ColorString(0, 0, 0, 1)
        self.source = PointXY(2.82843, -2.82843)

    def get_angle(self):
        x, y = self.source.x, self.source.y

        z = math.hypot(x, y)
        cx = ((y*y + z*z - x*x) / (2 * y * z))
        value = math.degrees(math.acos(cx))

        # Translate angle from quadrant
        if x > 0 and y > 0:
            angle = 90 - value
        elif x < 0 and y < 0:
            angle = 90 + value
        elif x < 0 < y:
            angle = 360 - value
        else:
            angle = value

        return int(round(angle, 0))

    def get_length(self):
        return int(round(math.hypot(self.source.x, self.source.y), 0))

    @staticmethod
    def _angle_to_point(angle, distance):
        value = math.radians(angle)
        x = distance * math.cos(value)
        y = distance * math.sin(value)

        return y, x if (180 > angle > 90) or (360 > angle > 260) else x, y

    def set_angle(self, angle):
        self.source = PointXY(*Shadow._angle_to_point(angle, self.get_length()))

    def set_length(self, length):
        self.source = PointXY(*Shadow._angle_to_point(self.get_angle(), length))

    def write(self, name=None):
        e = super().write()
        if name:
            e.attrib[RV_XML_VARNAME] = name
        e.text = "%f|%s|%s" % (self.radius, str(self.color), str(self.source))
        return e

    def read(self, element):
        super().read(element)

        parts = element.text.split('|')
        if len(parts) != 3:
            raise ValueError("shadow object has an unrecognized value: '%s'" % element.text)

        self.radius = float(parts[0])
        self.color = ColorString.parse(parts[1])
        self.source = PointXY.parse(parts[2])
        return self


class Stroke(XmlBackedObject):
    def __init__(self, width=0.0, color=None):
        super().__init__("dictionary", {RV_XML_VARNAME: "stroke"})
        self.enabled = False     # Not part of the object just used to set a parent attribute.
        self.width = width
        self.color = color or ColorString(0, 0, 0, 1)

    def write(self):
        e = super().write()

        color = Xml.Element("NSColor", {RV_XML_DICTKEY: "RVShapeElementStrokeColorKey"})
        color.text = str(self.color)
        e.append(color)

        width = Xml.Element("NSNumber", {RV_XML_DICTKEY: "RVShapeElementStrokeWidthKey"}, hint="double")
        width.text = str(self.width)
        e.append(width)

        return e

    def read(self, element):
        super().read(element)
        if element.get(RV_XML_VARNAME) != "stroke":
            raise ValueError("Dictionary element is not ID'd as a stroke object.")

        e = element.find("NSNumber")
        self.width = float(e.text) if e else self.width

        e = element.find("NSColor")
        self.color = ColorString.parse(e.text) if e else self.color
        return self

