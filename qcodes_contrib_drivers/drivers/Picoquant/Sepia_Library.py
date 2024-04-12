import os
import ctypes


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


class PicoquantSepia2Lib:
    _DLL_PATH = r"C:\Program Files\Picoquant\GenericLaserDriver\Sepia2_Lib.dll"

    def __init__(self, dll_path: str = None):
        self.dll = ctypes.CDLL(dll_path or self._DLL_PATH)

    def check_error(self, exit_code: int, function_name: str = None) -> None:
        if exit_code == 0:
            return

        try:
            error_msg = self.decode_error(exit_code)
        except PicoquantSepia2LibError:
            error_msg = None

        raise PicoquantSepia2LibError(exit_code, error_msg, function_name)

    @handle_errors
    def decode_error(self, error_code: int) -> str:
        error_string = ctypes.create_string_buffer(256)

        error_code = self.dll.SEPIA2_LIB_DecodeError(ctypes.c_int(error_code), error_string)
        if error_code != 0:
            raise PicoquantSepia2LibError(error_code, None, "SEPIA2_LIB_DecodeError")

        return error_string.value.decode("utf-8")

    @handle_errors
    def get_version(self) -> str:
        version_string = ctypes.create_string_buffer(256)

        error_code = self.dll.SEPIA2_LIB_GetVersion(version_string)
        self.check_error(error_code, "SEPIA2_LIB_GetVersion")

        return version_string.value.decode("utf-8")

    @handle_errors
    def is_running_on_wine(self) -> bool:
        is_running_on_wine = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_LIB_IsRunningOnWine(ctypes.byref(is_running_on_wine))
        self.check_error(error_code, "SEPIA2_LIB_IsRunningOnWine")

        return bool(is_running_on_wine.value)
