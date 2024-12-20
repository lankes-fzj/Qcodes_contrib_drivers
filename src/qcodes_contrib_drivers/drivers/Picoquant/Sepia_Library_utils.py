import enum

__all__ = ["PicoquantSepia2Error", "PicoquantSepia2LibError", "handle_errors",
           "PicoquantSepia2WorkingMode", "PicoquantSepia2SupportRequestOptions",
           "PicoquantSepia2Preset", "PicoquantSepia2SOMDState", "PicoquantSepia2SPMStates",
           "PicoquantSepia2SWSStates"]


class PicoquantSepia2Error(Exception):
    pass


class PicoquantSepia2LibError(PicoquantSepia2Error):
    """Exceptions occurring in `PicoquantSepia2Lib`.
    
    Args:
        error_code (optional): Return code of library function
        error_message (optional): Error message belonging to `error_code`
        function_name (optional): Function causing the error
    """

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
    """Function decorator, to handle exceptions in `PicoquantSepia2Lib`.
    
    This converts all exceptions into `PicoquantSepia2LibError`s
    
    Args:
        func (callable): Function to decorate
    
    Returns:
        callable: Decorated function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PicoquantSepia2LibError:
            raise  # We don't want to modify PicoquantSepia2LibError
        except Exception as exc:
            raise PicoquantSepia2LibError() from exc
    return wrapper


class PicoquantSepia2WorkingMode(enum.IntEnum):
    STAY_PERMANENT = 0  # Default mode: Commands & full protective data are written immediately
    VOLATILE = 1  # Volatile mode: Commands sent immediately, protective data retarded


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


class PicoquantSepia2SOMDState(enum.IntFlag):
    READY = 0x00  # Module ready
    INIT = 0x01  # Module initialising
    BUSY = 0x02  # Busy until (re-)locking PLL or update data processed
    HARDWARE_ERROR = 0x10  # Error code pending
    FW_UPDATE_RUNNING = 0x20  # Firmware update running
    FRAM_WRITE_PROTECTED = 0x40  # FRAM write protected: set, write enabled: cleared
    PLL_UNSTABLE = 0x80  # PLL not stable after changing base osc. or trigger mode


class PicoquantSepia2SWSStates(enum.IntFlag):
    READY = 0x000  # Module ready
    INIT = 0x001  # Module initialising
    BUSY = 0x002  # Motors running or calculating on update data
    WAVELENGTH = 0x004  # Wavelength received, waiting for bandwidth
    BANDWIDTH = 0x008  # Bandwidth received, waiting for wavelength
    HARDWARE_ERROR = 0x010  # Error code pending
    FW_UPDATE_RUNNING = 0x020  # Firmware update running
    FRAM_WRITE_PROTECTED = 0x040  # FRAM write protected: set, write enabled: cleared
    CALIBRATING = 0x080  # Calibration mode: set, normal operation: cleared
    GUIRANGES = 0x100  # GUI Ranges known: set, unknown: cleared


class PicoquantSepia2SPMStates(enum.IntFlag):
    READY = 0x00  # Module ready
    INIT = 0x01  # Module initialising
    HARDWARE_ERROR = 0x10  # Error code pending
    FW_UPDATE_RUNNING = 0x20  # Firmware update running
    FRAM_WRITE_PROTECTED = 0x40  # FRAM write protected: set, write enabled: cleared
