import enum

__all__ = ["PicoquantSepia2LibError", "handle_errors", "PicoquantSepia2SupportRequestOptions",
           "PicoquantSepia2Preset", "PicoquantSepia2SPMStates", "PicoquantSepia2SWSStates"]


class PicoquantSepia2LibError(Exception):
    def __init__(self, error_code: int = None, error_message: str = None,
                 function_name: str = None):
        self.error_code = error_code
        self.error_message = error_message
        self.function_name = function_name

        # Create exception message based on available information
        if self.function_name:
            msg = f"Library function '{self.function_name}' "
        else:
            msg = "A library function "
        if self.error_code:
            msg += f"failed with {self.error_code}"
        else:
            msg += "failed unexpectedly"
        if self.error_message:
            msg += f": {self.error_message}"

        super().__init__(msg)


def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PicoquantSepia2LibError:
            raise  # We don't want to modify PicoquantSepia2LibError
        except Exception as exc:
            raise PicoquantSepia2LibError() from exc
    return wrapper


class PicoquantSepia2SupportRequestOptions(enum.IntFlag):
    NO_PREAMBLE = 0x1  # No preamble text processing (if given, it is ignored)
    NO_TITLE = 0x2  # No title created
    NO_CALLING_SOFTWARE_INDENT = 0x4  # Lines on calling software are not indented
    NO_SYSTEM_INFO = 0x8  # No system info is processed


class PicoquantSepia2Preset(enum.IntEnum):
    FACTORY_DEFAULTS = -1
    CURRENT_SETTINGS = 0
    PRESET_1 = 1
    PRESET_2 = 2


class PicoquantSepia2SPMStates(enum.IntFlag):
    READY = 0x00  # Module ready
    INIT = 0x01  # Module initialising
    HARDWAREERROR = 0x10  # Error code pending
    FWUPDATERUNNING = 0x20  # Firmware update running
    FRAM_WRITEPROTECTED = 0x40  # FRAM write protected: set, write enabled: cleared


class PicoquantSepia2SWSStates(enum.IntFlag):
    READY = 0x000  # Module ready
    INIT = 0x001  # Module initialising
    BUSY = 0x002  # Motors running or calculating on update data
    WAVELENGTH = 0x004  # Wavelength received, waiting for bandwidth
    BANDWIDTH = 0x008  # Bandwidth received, waiting for wavelength
    HARDWAREERROR = 0x010  # Error code pending
    FWUPDATERUNNING = 0x020  # Firmware update running
    FRAM_WRITEPROTECTED = 0x040  # FRAM write protected: set, write enabled: cleared
    CALIBRATING = 0x080  # Calibration mode: set, normal operation: cleared
    GUIRANGES = 0x100  # GUI Ranges known: set, unknown: cleared
