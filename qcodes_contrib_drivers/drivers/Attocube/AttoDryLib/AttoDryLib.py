"""
Wrapper for the attoDRYLib64bit.dll which controls several attoDry instruments
by AttoCube (such as attoDRY800, attoDRY1100 and attoDRY2100).

The class ``AttoDryLib`` wraps the functions from the DLL and makes them
accessible via Python functions.

Authors:
    Lankes, Lukas (Forschungszentrum Jülich, IBI-TAE) <l.lankes@fz-juelich.de>
"""

import ctypes
import _ctypes
import ctypes.util
import enum
import functools as ft
import locale
import logging
import os

from .labview_exit_codes import get_labview_error_message


__all__ = ["AttoDryDevice", "AttoDryLibError",
           "AttoDryLibNonZeroExitCodeError", "AttoDryLib"]


_PREFERRED_ENCODING = locale.getpreferredencoding(False)
_ATTODRY_MSG_MAXLEN = 500

logger = logging.getLogger(__name__)


class AttoDryDevice(enum.IntEnum):
    """Device model ids"""
    __AttoDry1100 = 0  # not supported/tested yet
    AttoDry2100 = 1
    __AttoDry800 = 2  # not supported/tested yet


class AttoDryLibError(Exception):
    """Default exception class for AttoDryLib

    Args:
        message (str): Error message
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AttoDryLibNonZeroExitCodeError(AttoDryLibError):
    """A attoDRYLib function returned with a non-zero exit-code.

    Args:
        exit_code (int): Exit code returned by the failed function.
    """

    def __init__(self, exit_code: int, function_name: str = None):
        if function_name is None:
            message = "Function failed "
        else:
            message = f"Function \"{function_name}\" failed "
        message += f"with {exit_code}: "
        message += get_labview_error_message(exit_code)

        super().__init__(message)
        
        self.exit_code = exit_code
        self.function_name = function_name
    
    @staticmethod
    def check(exit_code: int, function_name: str = None) -> None:
        """Raises exception if exit code is non-zero.
        
        Args:
            exit_code (int): Exit code to check.
            function_name (str): Name of function that returned the exit code.
        
        Raises:
            AttoDryLibNonZeroExitCodeError: If `exit_code` is non-zero.
        """
        if exit_code != 0:
            raise AttoDryLibNonZeroExitCodeError(exit_code, function_name)

    @staticmethod
    def check_function(func: callable) -> callable:
        """Wraps function call and checks if library functions succeeded or
        failed. If the function failed, an exception is raised.

        Args:
            func (callable): Function to decorate
        
        Returns:
            callable: Decorated function
        """
        @ft.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Try to call original function
                return func(*args, **kwargs)
            except AttoDryLibNonZeroExitCodeError as exc:
                # Library returned non-zero exit code
                if exc.function_name is None:
                    # Create new exception including function name
                    raise AttoDryLibNonZeroExitCodeError(
                        exc.exit_code, func.__name__) from exc
                else:
                    raise exc  # Raise original exception
            except Exception as exc:
                # Unexpected exception type
                raise AttoDryLibError(f"Function {func.__name__} failed " +
                                      f"unexpectly.") from exc
        
        # Returned decorated function
        return wrapper


class AttoDryLib:
    """Wrapper class for the library "attoDRYLib64bit.dll"

    This class wraps the functions of the DLL and makes them accessible via
    Python functions.

    Args:
        device_type (AttoDryDevice): Device type to be used
        path_to_dll (str, optional): Path to the library "attoDRYLib64bit.dll"
        or None, if it is in the working directory or system path.
                    
    Raises:
        FileNotFoundError: When the DLL cannot be found
        AttoDryLibError: When loading the library fails
    """

    DLL_FILENAME = "AttoDryInterfaceLib64bit.dll"

    def __init__(self, device_type: AttoDryDevice, path_to_dll: str = None):
        self._begun = False  # Flag if `_begin()` has already been called

        if not path_to_dll:
            # Take default filename
            path_to_dll = self.DLL_FILENAME
        
        try:
            if os.path.isfile(path_to_dll):
                # Use path as passed by the caller
                self._path_to_dll = path_to_dll
            else:
                # Find DLL on search paths
                self._path_to_dll = ctypes.util.find_library(path_to_dll)
                if self._path_to_dll is None:
                    raise FileNotFoundError("Could not find attoDRY library: " + path_to_dll)
                logger.debug("Found DLL: " + self._path_to_dll)
        
            # Load DLL with ctypes
            logger.debug("Loading library: " + self._path_to_dll)
            self._library = ctypes.cdll.LoadLibrary(self._path_to_dll)
        except Exception as exc:
            raise AttoDryLibError("Error loading attoDRY library: " + self._path_to_dll) from exc
        
        # Start communication with attoDRY
        self.begin(device_type)
    
    def __del__(self) -> None:
        """Closes library when this object is deleted."""
        if self._library is not None:
            # Close if not happened before
            self.close()

    def close(self) -> None:
        """Stops communication with attoDRY and unloads library."""
        try:
            # Stop communication with attoDRY
            self.end()
        finally:
            logger.debug("Loading library: " + self._path_to_dll)
            # Free library (even if Calling attoDRY library function `_end` failed)
            _ctypes.FreeLibrary(self._library._handle)
            self._library = None

    @AttoDryLibNonZeroExitCodeError.check_function
    def begin(self, device_type: AttoDryDevice) -> None:
        """
        Starts the server that communicates with the attoDRY and loads the
        software for the device specified by `device_type`. This function needs
        to be run before commands can be sent or received.

        Args:
            device_type (AttoDryDevice): Type of device to load the software for.
        """
        if isinstance(device_type, AttoDryDevice):
            # Convert enum to int if necessary
            device_type = device_type.value
        c_device_type = ctypes.c_uint16(int(device_type))

        logger.debug("Calling attoDRY library function AttoDRY_Interface_begin")
        exit_code = self._library.AttoDRY_Interface_begin(c_device_type)
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        self._begun = True  # Set begun flag
    
    @AttoDryLibNonZeroExitCodeError.check_function
    def end(self) -> None:
        """
        Stops the server that is communicating with the attoDRY. The
        `disconnect`-function should be run before this. This function should
        be run before closing your program.
        """
        if not self._begun:
            # Skip if not begun or already ended
            return
        
        logger.debug("Calling attoDRY library function AttoDRY_Interface_end")
        exit_code = self._library.AttoDRY_Interface_end()
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        self._begun = False  # Reset begun flag

    @AttoDryLibNonZeroExitCodeError.check_function
    def connect(self, com_port: str) -> None:
        """Connects to the attoDRY using the specified COM Port.

        Args:
            com_port (str): COM-port the device is connected to
        """
        com_port_bytes = com_port.encode(_PREFERRED_ENCODING)
        c_com_port = ctypes.create_string_buffer(com_port_bytes)

        logger.debug("Calling attoDRY library function AttoDRY_Interface_Connect")
        exit_code = self._library.AttoDRY_Interface_Connect(c_com_port)
        AttoDryLibNonZeroExitCodeError.check(exit_code)

    @AttoDryLibNonZeroExitCodeError.check_function
    def disconnect(self) -> None:
        """Disconnects from the attoDRY, if already connected.
        
        This function should be run before `end()`.
        """
        logger.debug("Calling attoDRY library function AttoDRY_Interface_Disconnect")
        exit_code = self._library.AttoDRY_Interface_Disconnect()
        AttoDryLibNonZeroExitCodeError.check(exit_code)

    @AttoDryLibNonZeroExitCodeError.check_function
    def is_initialized(self) -> bool:
        """Checks to see if the attoDRY has initialized.
        
        Use this function after you have connected and before sending any
        commands or getting any data from the attoDRY.

        Returns:
            bool: True, if the attoDRY device is initialized
        """
        c_initialized = ctypes.c_int(0)

        logger.debug("Calling attoDRY library function AttoDRY_Interface_isDeviceInitialised")
        exit_code = self._library.AttoDRY_Interface_isDeviceInitialised(
            ctypes.byref(c_initialized))
        AttoDryLibNonZeroExitCodeError.check(exit_code)
        
        return bool(c_initialized.value)

    @AttoDryLibNonZeroExitCodeError.check_function
    def is_connected(self) -> bool:
        """Checks to see if the attoDRY is connected.

        Returns:
            bool: True, if the attoDRY device is connected.
        """
        c_connected = ctypes.c_int(0)

        logger.debug("Calling attoDRY library function AttoDRY_Interface_isDeviceConnected")
        exit_code = self._library.AttoDRY_Interface_isDeviceConnected(
            ctypes.byref(c_connected))
        AttoDryLibNonZeroExitCodeError.check(exit_code)
        
        return bool(c_connected.value)

    @AttoDryLibNonZeroExitCodeError.check_function
    def get_sample_temperature(self) -> float:
        """Gets the sample temperature in Kelvin.
        
        This value is updated whenever a status message is received from the
        attoDRY.

        Returns:
            float: Sample temperature (in Kelvin)
        """
        c_sample_temp = ctypes.c_float()

        logger.debug("Calling attoDRY library function AttoDRY_Interface_getSampleTemperature")
        exit_code = self._library.AttoDRY_Interface_getSampleTemperature(
            ctypes.byref(c_sample_temp))
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        return c_sample_temp.value

    @AttoDryLibNonZeroExitCodeError.check_function
    def get_user_temperature(self) -> float:
        """Gets the user set point temperature in Kelvin.
        
        This value is updated whenever a status message is received from the
        attoDRY.

        Returns:
            float: User set point temperature (in Kelvin)
        """
        c_user_temp = ctypes.c_float()

        logger.debug("Calling attoDRY library function AttoDRY_Interface_getUserTemperature")
        exit_code = self._library.AttoDRY_Interface_getUserTemperature(
            ctypes.byref(c_user_temp))
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        return c_user_temp.value

    @AttoDryLibNonZeroExitCodeError.check_function
    def set_user_temperature(self, user_temperature: float) -> None:
        """Sets the user temperature in Kelvin.
        
        This is the temperature used when temperature control is enabled.

        Args:
            user_temperature (float): User set point temperature (in Kelvin)
        """
        c_user_temp = ctypes.c_float(float(user_temperature))

        logger.debug("Calling attoDRY library function AttoDRY_Interface_setUserTemperature")
        exit_code = self._library.AttoDRY_Interface_setUserTemperature(
            c_user_temp)
        AttoDryLibNonZeroExitCodeError.check(exit_code)

    @AttoDryLibNonZeroExitCodeError.check_function
    def get_error_status(self) -> int:
        """Gets the current error code.
        
        Returns:
            int: Current error code
        """
        c_status = ctypes.c_int8()

        logger.debug("Calling attoDRY library function AttoDRY_Interface_getAttodryErrorStatus")
        exit_code = self._library.AttoDRY_Interface_getAttodryErrorStatus(
            ctypes.byref(c_status))
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        return c_status.value

    @AttoDryLibNonZeroExitCodeError.check_function
    def get_error_message(self) -> str:
        """Gets the current error message.
        
        Returns:
            str: Current error message
        """
        c_length = ctypes.c_int32(_ATTODRY_MSG_MAXLEN)
        c_message = ctypes.create_string_buffer(_ATTODRY_MSG_MAXLEN)

        logger.debug("Calling attoDRY library function AttoDRY_Interface_getAttodryErrorMessage")
        exit_code = self._library.AttoDRY_Interface_getAttodryErrorMessage(
            ctypes.byref(c_message), c_length)
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        return c_message.value.decode(_PREFERRED_ENCODING)

    @AttoDryLibNonZeroExitCodeError.check_function
    def get_action_message(self) -> str:
        """Gets the current action message.
        
        If an action is being performed, it will be shown here. It is similar
        to the pop ups on the display.
        
        Returns:
            str: Current action message
        """
        c_length = ctypes.c_int32(_ATTODRY_MSG_MAXLEN)
        c_message = ctypes.create_string_buffer(_ATTODRY_MSG_MAXLEN)

        logger.debug("Calling attoDRY library function AttoDRY_Interface_getActionMessage")
        exit_code = self._library.AttoDRY_Interface_getActionMessage(
            ctypes.byref(c_message), c_length)
        AttoDryLibNonZeroExitCodeError.check(exit_code)

        return c_message.value.decode(_PREFERRED_ENCODING)

    @AttoDryLibNonZeroExitCodeError.check_function
    def confirm(self) -> None:
        """Sends a 'Confirm' command to the attoDRY.
        
        Use this when you want to respond positively to a pop up.
        """
        logger.debug("Calling attoDRY library function AttoDRY_Interface_Confirm")
        exit_code = self._library.AttoDRY_Interface_Confirm()
        AttoDryLibNonZeroExitCodeError.check(exit_code)
        
    @AttoDryLibNonZeroExitCodeError.check_function
    def cancel(self) -> None:
        """Sends a 'Cancel' Command to the attoDRY.
        
        Use this when you want to cancel an action or respond negatively to a
        pop up.
        """
        logger.debug("Calling attoDRY library function AttoDRY_Interface_Cancel")
        exit_code = self._library.AttoDRY_Interface_Cancel()
        AttoDryLibNonZeroExitCodeError.check(exit_code)
