
from pro6.constants import *
from pro6.prefs import get_system_preferences
import pro6.media as media
import pro6.util as util

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element
import os.path
import base64
import sys


RV_PRESENTATION_DOCUMENT = "RVPresentationDocument"
RV_SLIDE_GROUPING = "RVSlideGrouping"
RV_DISPLAY_SLIDE = "RVDisplaySlide"
RV_SLIDE_TIMER_CUE = "RVSlideTimerCue"
RV_TIMELINE = "RVTimeline"
RV_TIMELINE_CUE = "RVTimelineCue"
RV_TEXT_ELEMENT = "RVTextElement"
RV_IMAGE_ELEMENT = "RVImageElement"
RV_VIDEO_ELEMENT = "RVVideoElement"
RV_SHAPE_ELEMENT = "RVShapeElement"
RV_MEDIA_CUE = "RVMediaCue"

DOCUMENT_EXTENSION = ".pro6"


# Get base settings
prefs = get_system_preferences()
output_width = prefs.display.output_width
output_height = prefs.display.output_height
foreground_scale = prefs.general.foreground_scaling
background_scale = prefs.general.background_scaling


def _get_default_rtf():
    return "e1xydGYxXGFuc2lcYW5zaWNwZzEyNTJcY29jb2FydGYxNTA0XGNvY29hc3VicnRmODMwCntcZm9udHRibFxmMFx"\
           "mbmlsXGZjaGFyc2V0MCBUYWhvbWE7fQp7XGNvbG9ydGJsO1xyZWQyNTVcZ3JlZW4yNTVcYmx1ZTI1NTt9CntcKl"\
           "xleHBhbmRlZGNvbG9ydGJsOzt9ClxkZWZ0YWI3MjAKXHBhcmRccGFyZGVmdGFiNzIwXHBhcnRpZ2h0ZW5mYWN0b"\
           "3IwCgpcZjBcZnM5N1xmc21pbGxpNDg3NTAgXGNmMSBTYW1wbGUgdGV4dH0="


class TimeBasedCue(util.XmlBackedObject):
    def __init__(self, element):
        if element is None:
            raise ValueError("TimeBasedCue cannot be created directly.")
        super().__init__(element)

    @staticmethod
    def _get_defaults():
        return {
            "UUID": util.get_uuid(),
            "actionType": "0",
            "delayTime": "0.000000",
            "displayName": "",
            "enabled": "false",
            "timeStamp": "0.000000"
        }


class TimelineCue(TimeBasedCue):
    def __init__(self, obj, element=None, **extra):
        if element is None:
            default = TimeBasedCue._get_defaults()
            default.update({
                "slideIndex": "0",
                "enabled": "true"
            })
            element = Element(RV_TIMELINE_CUE, default, **extra)

        super().__init__(element)

        self._object = None
        if obj is not None:
            self.set_object(obj)

    def save(self):
        super().save()
        if self.get_object() is not None:
            self.set("representedObjectUUID", self._object.get("UUID"))

    def append(self, obj):
        raise Exception("TimelineCue cannot have any children.")

    def get_object(self):
        """Returns the object represented by the cue."""
        if self._object is None:
            root = self._find_root()
            if root is not None:
                uuid = self.get("representedObjectUUID")
                if uuid is not None:
                    self._object = root.find_object_by_uuid(uuid)
        return self._object

    def set_object(self, obj):
        """Sets the object represented by the cue.

            The object must have a UUID.
        """
        if not isinstance(obj, util.XmlBackedObject):
            raise TypeError("Timeline represented object must be XML backed.")

        self._object = obj


class Timeline(util.XmlBackedObject):
    def __init__(self, element=None, **extra):
        if element is None:
            default = {
                util.ATTRIB_VARNAME: "timeline",
                "loop": "false",
                "playBackRate": "1.000000",
                "duration": "0.000000",
                "timeOffset": "0.000000",
                "selectedMediaTrackIndex": "0"
            }
            element = Element(RV_TIMELINE, default, **extra)

        super().__init__(element)

        # Read all of the cues
        self._cues = self._find_by("timeCues", tag="array", force=True)
        for e in self._cues.findall(RV_TIMELINE_CUE):
            super().append(TimelineCue(None, e))

        # Part of the doc but we don't use it.
        self._find_by("mediaTracks", tag="array", force=True)

    def append(self, obj):
        """Adds a cue to the timeline."""
        if not isinstance(obj, TimelineCue):
            raise TypeError("Timeline can only contain TimelineCue children.")

        super().append(obj)
        self._cues.append(obj.get_element())

    def remove(self, obj):
        if super().remove(obj):
            self._cues.remove(obj.get_element())

    def cues(self):
        """Returns a list of cues from the timeline, in slide index order."""
        return sorted([cue for cue in self._children if isinstance(cue, TimelineCue)],
                      key=lambda cue: int(cue.get("slideIndex")))

    def clear(self):
        """Removes all of the cues from the timeline and resets the duration."""
        for cue in self.cues():
            self.remove(cue)
        self.set("duration", "0.000000")

    def set_interval(self, interval):
        """Sets the interval between cues, in seconds.

            The interval value is a float.
        """
        ts = 0.000000
        for cue in self.cues():
            cue.set("timeStamp", str(ts))
            ts += interval
        self.set("duration", str(ts))


class MediaCue(util.XmlBackedObject):
    def __init__(self, source, element=None, **extra):
        if element is None:
            if source is None:
                raise ValueError("Invalid media source.")

            default = {
                "UUID": util.get_uuid(),
                "displayName": os.path.basename(source),
                "alignment": ALIGN_CENTER,
                "behavior": "0",
                "actionType": "0",
                "dateAdded": "",
                "delayTime": "0.000000",
                "enabled": "true",
                "tags": "",
                "timeStamp": "0.000000"
            }
            element = Element(RV_MEDIA_CUE, default, **extra)
            super().__init__(element)
            self.append(MediaElement.from_source(source))
        else:
            super().__init__(element)

            # Set the child media element
            child = self._element.find("*")
            if child.tag == RV_IMAGE_ELEMENT:
                self.set_media(ImageElement(child))
            elif child.tag == RV_VIDEO_ELEMENT:
                self.set_media(VideoElement(child))
            else:
                raise Exception("Unexpected MediaCue child: %s" % child.tag)

        self.is_background = (self.get(util.ATTRIB_VARNAME) == "backgroundMediaCue")

        # Find the next cue object
        target = self.get("nextCueUUID")
        root = self._find_root()
        self.next_cue = None if root is None else root.find_object_by_uuid(target)

    def save(self):
        if self.is_background:
            self.set(util.ATTRIB_VARNAME, "backgroundMediaCue")
        elif util.ATTRIB_VARNAME in self._element.attrib:
            del self._element.attrib[util.ATTRIB_VARNAME]

        if self.next_cue is not None and isinstance(self.next_cue, util.XmlBackedObject):
            self.set("nextCueUUID", self.next_cue.get_uuid())
        else:
            self.set("nextCueUUID", "")
        super().save()

    def append(self, obj):
        if not isinstance(obj, MediaElement):
            raise TypeError("MediaCue can only contain a MediaElement child.")

        if len(self._children) > 0:
            raise Exception("A media cue can only have one child.")

        super().append(obj)
        obj.set(util.ATTRIB_VARNAME, "element")
        self.get_element().append(obj.get_element())

    def remove(self, obj):
        if super().remove(obj):
            self.get_element().remove(obj.get_element())
            if util.ATTRIB_VARNAME in obj.get_element().attrib:
                del obj.get_element().attrib[util.ATTRIB_VARNAME]

    def set_media(self, element):
        """Sets the media element that the cue is based on."""
        if not isinstance(element, MediaElement):
            raise TypeError("Media must be a ProPresenter ImageElement or VideoElement.")

        if len(self._children) > 0:
            self.remove(self._children[0])
        self.append(element)

    def get_media(self):
        """Returns the media element that the cue is based on."""
        if len(self._children) > 0 and isinstance(self._children[0], MediaElement):
            return self._children[0]
        return None


class DisplayElement(util.XmlBackedObject):
    def __init__(self, element):
        if element is None:
            raise TypeError("DisplayElement cannot be created directly.")

        super().__init__(element)

        self.fill_color = util.Color.from_string(self.get("fillColor"))
        self.position = util.Rect3D.from_xml(self._find_by("position", tag=util.RV_RECT_3D))
        self.shadow = util.Shadow.from_xml(self._find_by("shadow", tag="shadow"))
        self.stroke = util.Stroke.from_xml(self._find_by("stroke", tag="stroke"))

    @staticmethod
    def _get_defaults():
        # This should be called by any of the child elements when creating default values.
        return {
            "UUID": util.get_uuid(),
            "displayName": "Default",
            "typeID": "0",
            "displayDelay": "0.000000",
            "locked": "false",
            "persistent": "false",
            "fromTemplate": "false",
            "source": "",
            "bezelRadius": "0.000000",
            "rotation": "0.000000",
            "drawingFill": "false",
            "drawingShadow": "false",
            "drawingStroke": "false"
        }

    def save(self):
        # Set default values if no object is defined.
        self.position = self.position or util.Rect3D()
        self.shadow = self.shadow or util.Shadow()
        self.stroke = self.stroke or util.Stroke()
        self.fill_color = self.fill_color or util.Color(1, 1, 1, 1)

        # We don't track the actual elements for these as children so just replace them.
        self._remove_by("position", tag=util.RV_RECT_3D)
        self._element.append(self.position.get_xml("position"))
        self._remove_by("shadow", tag="shadow")
        self._element.append(self.shadow.get_xml())
        self._remove_by("stroke", tag="dictionary")
        self._element.append(self.stroke.get_xml())

        self.set("fillColor", self.fill_color.get_value_string())
        super()._save_uuid()
        super().save()


class ShapeElement(DisplayElement):
    def __init__(self, element=None, **extra):
        if element is None:
            default = {
                "opacity": "1.000000"
            }
            default.update(DisplayElement._get_defaults())
            element = Element(RV_SHAPE_ELEMENT, default, **extra)

        super().__init__(element)

    def save(self):
        super().save()


class TextElement(DisplayElement):
    def __init__(self, element=None, **extra):
        if element is None:
            default = super()._get_defaults()
            default.update({
                "adjustsHeightToFit": "false",
                "verticalAlignment": "0",
                "revealType": "0"
            })
            element = Element(RV_TEXT_ELEMENT, default, **extra)
            super().__init__(element)

            rtf = self._get_string_element("RTFData", True)
            if len(rtf.text) == 0:
                rtf.text = _get_default_rtf()
        else:
            super().__init__(element)

        e = self._get_string_element("RTFData", False)
        self.rtf = None if e is None else base64.b64decode(e.text).decode('ascii')
        e = self._get_string_element("PlainText", False)
        self.text = None if e is None else base64.b64decode(e.text).decode('ascii')
        e = self._get_string_element("WinFlowData", False)
        self.flow_data = None if e is None else base64.b64decode(e.text).decode('ascii')
        e = self._get_string_element("WinFontData", False)
        self.font_data = None if e is None else base64.b64decode(e.text).decode('ascii')

    def save(self):
        if self.rtf is not None:
            self._get_string_element("RTFData", True).text = base64.b64encode(self.rtf).decode('ascii')
        if self.text is not None:
            self._get_string_element("PlainText", True).text = base64.b64encode(self.text).decode('ascii')
        if self.flow_data is not None:
            self._get_string_element("WinFlowData", True).text = base64.b64encode(self.flow_data).decode('ascii')
        if self.font_data is not None:
            self._get_string_element("WinFontData", True).text = base64.b64encode(self.font_data).decode('ascii')

        super().save()

    def append(self, obj):
        raise Exception("TextElement cannot have children.")

    def _get_string_element(self, name, force=False):
        return self._find_by(name, tag=util.NS_STRING, force=force)


class MediaElement(DisplayElement):
    def __init__(self, element):
        if element is None:
            raise ValueError("MediaElement cannot be created directly.")

        super().__init__(element)

        self.offset = util.PointXY.from_string(self.get("imageOffset"))
        self.scale_size = util.PointXY.from_string(self.get("scaleSize"))

    @staticmethod
    def _get_defaults():
        dic = DisplayElement._get_defaults()
        dic.update({
            "scaleBehavior": SCALE_FIT,
            "flippedHorizontally": "false",
            "flippedVertically": "false",
            "imageOffset": "{0, 0}",
            "scaleSize": "{1, 1}",
            "opacity": "1.000000",
            "manufactureName": "",
            "manufactureURL": "",
            "format": ""
        })
        return dic

    def save(self):
        source = self.get("source")
        if source is not None:
            self.set("displayName", os.path.splitext(os.path.basename(source))[0])
        else:
            self.set("displayName", "Default")

        self.offset = self.offset or util.PointXY()
        self.scale_size = self.scale_size or util.PointXY()

        self.set("imageOffset", str(self.offset))
        self.set("scaleSize", str(self.scale_size))

        super().save()

    def append(self, obj):
        raise Exception("MediaElement cannot have children.")

    @classmethod
    def from_source(cls, source, **extra):
        if source is None or not isinstance(source, str):
            raise TypeError("Source must be the path to a media file.")

        parts = os.path.splitext(os.path.basename(source))

        meta = media.get_metadata(source)
        if not meta:
            raise ValueError("Source is not a recognized media file: %s" % os.path.basename(source))

        width, height = media.get_frame_size(meta)

        mime = meta.get("mime_type")
        if mime.startswith("image/"):
            e = ImageElement(None, **extra)
            e.set("format", util.IMAGE_EXTENSIONS.get(parts[1][1:]))
        elif mime.startswith("video/"):
            e = VideoElement(None, **extra)
            e.natural_size = util.PointXY(width, height)
            length = media.get_length(meta)
            e.set("outPoint", str(length))
            e.set("endPoint", str(length))
        else:
            raise ValueError("Unsupported media type: %s (%s)" % (mime, parts[1][1:]))

        # Set image size
        e.position = util.Rect3D(width, height)

        e.set("source", util.normalize_path(source))
        e.set("displayName", parts[0] + parts[1])
        return e


class ImageElement(MediaElement):
    def __init__(self, element=None, **extra):
        if element is None:
            element = Element(RV_IMAGE_ELEMENT, super()._get_defaults(), **extra)

        super().__init__(element)


class VideoElement(MediaElement):
    def __init__(self, element=None, **extra):
        if element is None:
            default = super()._get_defaults()
            default.update({
                "frameRate": "0.000000",
                "audioVolume": "1.000000",
                "inPoint": "0",
                "outPoint": "0",
                "endPoint": "0",
                "playRate": "1.000000",
                "playbackBehavior": PLAY_STOP,
                "timeScale": "600",
                "naturalSize": "{0, 0}",
                "fieldType": "0"
            })
            element = Element(RV_VIDEO_ELEMENT, default, **extra)

        super().__init__(element)

        self.natural_size = util.PointXY.from_string(self.get("naturalSize"))

    def save(self):
        self.natural_size = self.natural_size or util.PointXY()
        self.set("naturalSize", str(self.natural_size))
        super().save()


class SlideTimerCue(TimeBasedCue):
    def __init__(self, element=None, **extra):
        if element is None:
            default = super()._get_defaults()
            default.update({
                "duration": "6.000000",
                "loopToBeginning": "false"
            })
            element = Element(RV_SLIDE_TIMER_CUE, default, **extra)

        super().__init__(element)


class DisplaySlide(util.XmlBackedObject):
    def __init__(self, element=None, **extra):
        if element is None:
            default = {
                "backgroundColor": "0 0 0 1",
                "highlightColor": "0 0 0 0",
                "enabled": "true",
                "label": "",
                "hotKey": "",
                "notes": "",
                "drawingBackgroundColor": "false",
                "chordChartPath": "",
                "UUID": util.get_uuid(),
                "socialItemCount": "1"
            }
            element = Element(RV_DISPLAY_SLIDE, default, **extra)

        super().__init__(element)

        self.background_color = util.Color.from_string(self.get("backgroundColor"))
        self.highlight_color = util.Color.from_string(self.get("foregroundColor"))

        # Check for a background element
        back_media = self._find_by("backgroundMediaCue", tag=RV_MEDIA_CUE)
        if back_media is not None:
            super().append(MediaCue(None, back_media))

        # Load foreground elements
        self._display_elements = self._find_by("displayElements", tag="array", force=True)
        elements = {
            RV_TEXT_ELEMENT: TextElement,
            RV_IMAGE_ELEMENT: ImageElement,
            RV_VIDEO_ELEMENT: VideoElement,
            RV_SHAPE_ELEMENT: ShapeElement
        }
        for e in self._display_elements:
            if e.tag in elements:
                super().append(elements.get(e.tag)(e))
            else:
                print("Unsupported display element type: %s" % e.tag)

        # This is part of the doc that we don't use.
        self._cues = self._find_by("cues", tag="array", force=True)
        for e in self._cues:
            if e.tag == RV_SLIDE_TIMER_CUE:
                super().append(SlideTimerCue(e))

    def save(self):
        self.background_color = self.background_color or util.Color(0, 0, 0, 1)
        self.highlight_color = self.highlight_color or util.Color(0, 0, 0, 0)

        self.set("backgroundColor", self.background_color.get_value_string())
        self.set("highlightColor", self.highlight_color.get_value_string())

        super()._save_uuid()
        super().save()

    def append(self, obj):
        """Adds a text or media element to the slide."""
        if isinstance(obj, DisplayElement):
            parent = self._display_elements
        elif isinstance(obj, SlideTimerCue):
            parent = self._cues
        else:
            raise TypeError("Unsupported display element type: %s" % type(obj).__name__)

        super().append(obj)
        parent.append(obj.get_element())

    def remove(self, obj):
        if super().remove(obj):
            if isinstance(obj, DisplayElement):
                parent = self._display_elements
            elif isinstance(obj, SlideTimerCue):
                parent = self._cues
            else:
                raise TypeError("Something happened. Unsupported element was removed: %s" % type(obj).__name__)

            parent.remove(obj.get_element())

    def clear(self):
        """Removes all of the elements and media from the slide."""
        for child in self._children:
            self.remove(child)

    def elements(self):
        """Returns a list of slide elements on the slide."""
        return [element for element in self._children if isinstance(element, DisplayElement)]

    def cues(self):
        return [cue for cue in self._children if isinstance(cue, SlideTimerCue)]

    def get_background(self):
        """Returns the background media cue for the slide, or None."""
        cues = [cue for cue in self._children if isinstance(cue, MediaCue)]
        return None if len(cues) == 0 else cues[0]

    def set_background(self, background):
        """Sets the background media cue for the slide. Use None to remove the background."""
        if background is None:
            self.remove(self.get_background())
        else:
            if not isinstance(background, MediaCue):
                raise TypeError("Background must be a MediaCue or None.")
            self.remove(self.get_background())

            background.is_background = True
            super().append(background)
            self.get_element().append(background.get_element())


class SlideGroup(util.XmlBackedObject):
    def __init__(self, element=None, **extra):
        if element is None:
            default = {
                "color": "0.333333 0.333333 0.333333 1",
                "name": "Group",
                "uuid": util.get_uuid()
            }
            element = Element(RV_SLIDE_GROUPING, default, **extra)

        super().__init__(element)

        self.color = util.Color.from_string(self.get("color"))

        self._slides = self._find_by("slides", tag="array", force=True)
        for e in self._slides.findall(RV_DISPLAY_SLIDE):
            super().append(DisplaySlide(e))

    def save(self):
        self.color = self.color or util.Color(0.33, 0.33, 0.33, 1)

        self.set("color", self.color.get_value_string())
        super().save()

    def append(self, obj):
        """Appends a slide to the group.

            If a slide element is specified, a new slide will be created
                and that element will be added to it.
            If a media cue is specified, a new slide will be created with
                that cue as its background media.
        """
        if isinstance(obj, DisplaySlide):
            super().append(obj)
            return obj
        else:
            slide = DisplaySlide()
            if isinstance(obj, (TextElement, MediaElement)):
                slide.append(obj)
            elif isinstance(obj, MediaCue):
                slide.set_background(obj)
            else:
                raise TypeError("Unsupported document sub-type: %s" % type(obj).__name__)

            slide.set("label", obj.get("displayName"))
            super().append(slide)
            self._slides.append(slide.get_element())
            return slide

    def remove(self, obj):
        """Removes a slide from the group."""
        if super().remove(obj):
            self._slides.remove(obj.get_element())

    def slides(self):
        """Returns a list of slides in the group."""
        return [slide for slide in self._children if isinstance(slide, DisplaySlide)]

    def __len__(self):
        return len(self.slides())


class CopyrightInfo:
    def __init__(self, d=None):
        d = d or {}
        self.artist = d.get("CCLIArtistCredits")
        self.author = d.get("CCLIAuthor")
        self.year = d.get("CCLICopyrightYear")
        self.display = util.to_bool(d.get("CCLIDisplay"))
        self.publisher = d.get("CCLIPublisher")
        self.song_number = d.get("CCLISongNumber")
        self.song_title = d.get("CCLISongTitle")

    def save(self, d):
        d.set("CCLIArtistCredits", self.artist or "")
        d.set("CCLIAuthor", self.author or "")
        d.set("CCLICopyrightYear", self.year or "")
        d.set("CCLIDisplay", str(self.display or False).lower())
        d.set("CCLIPublisher", self.publisher or "")
        d.set("CCLISongNumber", self.song_number or "")
        d.set("CCLISongTitle", self.song_title or "")


class Pro6Document(util.XmlBackedObject):
    def __init__(self, name, tree=None, **extra):
        if tree is None:
            osi = util.get_os()
            default = {
                "height": str(output_height),
                "width": str(output_width),
                "category": "",
                "buildNumber": BUILD_NUMBER_WIN if osi == OS_WINDOWS else BUILD_NUMBER_OSX,
                "versionNumber": VERSION_NUMBER,
                "chordChartPath": "",
                "docType": "0",
                "drawingBackgroundColor": "false",
                "backgroundColor": "0 0 0 0",
                "lastDateUsed": "",
                "notes": "",
                "os": osi,
                "resourcesDirectory": "",
                "selectedArrangementID": "",
                "usedCount": "0",
                "UUID": util.get_uuid().upper()
            }
            tree = ElementTree(Element(RV_PRESENTATION_DOCUMENT, default, **extra))

        if not isinstance(tree, ElementTree):
            raise TypeError("Document tree must be an XML tree.")
        else:
            super().__init__(tree.getroot())

        self.path = name
        self._tree = tree

        self.copyright = CopyrightInfo(self.get_element())

        # Load the timeline
        timeline = self.get_element().find(RV_TIMELINE)
        if timeline is None:
            tl = Timeline()
            super().append(tl)
            tree.getroot().append(tl.get_element())
        else:
            super().append(Timeline(timeline))

        # Load the groups
        self._groups = self._find_by("groups", tag="array", force=True)
        for group in self._groups.findall(RV_SLIDE_GROUPING):
            super().append(SlideGroup(group))

        # Part of the doc but we don't use it .
        self._find_by("arrangements", tag="array", force=True)

    def save(self, path=None):
        """Saves changes to the document.

            If a path is specified, the changes will be written to that file.
        """
        self.copyright.save(self.get_element())
        if len(self.groups()) == 0:
            self.append(SlideGroup())

        super().save()

        # Save as... new path
        if path is not None:
            self.path = path

        # Use the absolute path if available otherwise assume the current library.
        self.path = util.find_abs_path(self.path, prefs.general.library_path, DOCUMENT_EXTENSION)

        # Write the tree to file
        self._tree.write(self.path)

    def append(self, obj):
        """Adds a group or slide to the end of the document.

            If a slide element is specified, a new slide will be created
                and that element will be added to it.
            If a media cue is specified, a new slide will be created with
                that cue as its background media.
        """
        if isinstance(obj, SlideGroup):
            super().append(obj)
            self._groups.append(obj.get_element())
            return obj
        else:
            # Get the last group, or create it if none exist.
            groups = self.groups()
            if len(groups) == 0:
                group = SlideGroup()
                self.append(group)
            else:
                group = groups[-1]

            # Append the item to the last group.
            group.append(obj)
            return group

    def remove(self, obj):
        """Removes a group or slide from the document."""
        if super().remove(obj):
            self._groups.remove(obj.get_element())
        else:
            for group in self.groups():
                group.remove(obj)

    def timeline(self):
        """Returns the document's timeline."""
        children = [c for c in self._children if isinstance(c, Timeline)]
        return None if len(children) < 1 else children[0]

    def groups(self):
        """Returns all of the slide groups from the document."""
        return [group for group in self._children if isinstance(group, SlideGroup)]

    def slides(self):
        """Returns all of the slides from the document."""
        return [s for slides in self.groups() for s in slides if isinstance(s, DisplaySlide)]

    def clear(self):
        """Clears all of the slides, groups, and arrangements from this document and resets the timeline."""
        for child in self._children:
            if not isinstance(child, Timeline):
                self.remove(child)
            else:
                child.clear()   # Reset the timeline

        # Reset arrangements
        arrange = self._find_by("arrangements", tag="array", force=True)
        arrange.clear()
        arrange.set(util.ATTRIB_VARNAME, "arrangements")

    def create_slideshow(self, interval, loop=False):
        if not isinstance(interval, (int, float)):
            raise TypeError("Interval must be numeric.")

        tl = self.timeline()    # Get the timeline
        tl.clear()              # Clear existing cues
        index = 0
        time = 0.0

        # Add a cue for each slide
        for slide in self.slides():
            cue = TimelineCue(slide)
            cue.set("slideIndex", str(index))
            cue.set("displayName", " %i" % (index + 1))
            cue.set("timeStamp", str(time))
            tl.append(cue)

            index += 1
            time += interval

        tl.set("duration", str(time))
        tl.set("loop", str(loop).lower())

    def find_object_by_uuid(self, uuid, tag=None):
        """Returns an object from the document represented by the given UUID."""
        return self._deep_search(uuid, "UUID", tag)

    def __len__(self):
        return len(self.slides())

    def print_outline(self):
        """Prints an outline of the document, it's groups, slides, and the elements on them."""
        print("New Document" if self.path is None else ("Document '%s':" % os.path.basename(self.path)))

        tl = self.timeline()
        if tl is not None:
            print("\tTimeline: %s sec (%s)" %
                  (tl.get("duration"), ("loop" if util.to_bool(tl.get("loop")) else "single")))

        slide_num = 1
        for group in self.groups():
            print("\tGroup '%s':" % group.get("name"))
            for slide in group.slides():
                label = slide.get("label")
                elems = slide.elements()

                bkgnd = slide.get_background()
                bkgnd_name = None
                header = False
                if bkgnd is not None:
                    bkgnd_name = os.path.basename(bkgnd.get_media().get("source"))
                    if len(label) == 0:
                        print("\t\tSlide #%i - background: %s" % (slide_num, bkgnd_name))
                        header = True

                if not header:
                    print("\t\tSlide #%i%s" % (slide_num, ((": '%s'" % label) if len(label) > 0 else ":")))
                    if bkgnd_name is not None:
                        print("\t\t\tBackground: %s" % bkgnd_name)

                for element in elems:
                    if isinstance(element, TextElement):
                        print("\t\t\tTextElement: %s" %
                              (element.text if element.text and len(element.text) > 0 else "[RTF]"))
                    elif isinstance(element, MediaElement):
                        print("\t\t\t%s: %s" % (type(element).__name__, os.path.basename(element.get("source"))))
                    elif isinstance(element, ShapeElement):
                        print("\t\t\tShapeElement: %s" %
                              element.get("displayName", "%ix%i" % (element.position.width, element.position.height)))

                slide_num += 1

    def print_elements(self):
        for e in self.get_element().iter():
            print("Element: %s" % ("None" if e is None else e.tag), end=" ")
            print(("'%s'" % e.get(util.ATTRIB_VARNAME)) if (util.ATTRIB_VARNAME in e.attrib.keys()) else "")

            for k, v in e.attrib.items():
                if k != util.ATTRIB_VARNAME:
                    print("\t%s = '%s'" % (k, "None" if v is None else v))

    @staticmethod
    def load(path):
        """Returns a Document object representing the document at the specified path."""
        path = util.find_abs_path(path, prefs.general.library_path, DOCUMENT_EXTENSION)

        document = Pro6Document(path, ET.parse(path))
        document.path = path
        return document


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No source file specified.")
        sys.exit(1)

    doc = Pro6Document.load(sys.argv[1])
    doc.print_outline()
