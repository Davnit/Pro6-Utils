
from ..util.general import prepare_path, unprepare_path
from ..util.xmlhelp import XmlBackedObject, ColorString

import os


DEFAULT_HEADER_COLOR = 0.894117647058824


class DocumentCue(XmlBackedObject):
    def __init__(self, document_path, **extra):
        defaults = {
            "selectedArrangementID": None
        }
        defaults.update(extra)
        super().__init__("RVDocumentCue", defaults)

        self.file_path = document_path
        self.display_name = os.path.splitext(os.path.basename(document_path))[0]
        self.action = "0"
        self.enabled = True
        self.timestamp = 0.0
        self.delay = 0.0

    def write(self):
        attrib = {
            "displayName": self.display_name,
            "filePath": prepare_path(self.file_path),
            "actionType": self.action,
            "enabled": self.enabled,
            "timeStamp": self.timestamp,
            "delayTime": self.delay
        }
        super().update(attrib)
        super().set_uuid()
        return super().write()

    def read(self, element):
        super().read(element)

        self.file_path = unprepare_path(element.get("filePath", self.file_path))
        self.display_name = element.get("displayName", self.display_name)
        self.action = element.get("actionType", self.action)
        self.enabled = element.get("enabled") == "true" or element.get("enabled") == "1"
        self.timestamp = float(element.get("timeStamp", str(self.timestamp)))
        self.delay = float(element.get("delayTime", str(self.delay)))
        return self


class HeaderCue(XmlBackedObject):
    def __init__(self, name=None, **extra):
        defaults = {
            "actionType": 0,
            "enabled": 1,
            "timeStamp": 0,
            "delayTime": 0,
            "duration": "00:00:00",
            "endTime": "No Limit",
            "timerType": 0,
            "countDownToTimeFormat": 0,
            "allowOverrune": False,
            "timerUUID": None
        }
        defaults.update(extra)
        super().__init__("RVHeaderCue", defaults)

        self.display_name = name or "New Header"
        self.color = ColorString(DEFAULT_HEADER_COLOR, DEFAULT_HEADER_COLOR, DEFAULT_HEADER_COLOR, 1)

    def write(self):
        attrib = {
            "displayName": self.display_name,
            "color": self.color or "0 0 0 1"
        }
        super().update(attrib)
        super().set_uuid()
        return super().write()

    def read(self, element):
        super().read(element)

        self.display_name = element.get("displayName", self.display_name)
        self.color = ColorString.parse(element.get("color"))
        return self
