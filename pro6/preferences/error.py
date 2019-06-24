
class InstallNotFoundError(FileNotFoundError):
    def __init__(self):
        super().__init__("Could not find a ProPresenter 6 installation on your system.")


class InvalidInstallError(BaseException):
    def __init__(self, sub):
        super().__init__("A problem was found with your ProPresenter 6 installation: %s" % sub)
