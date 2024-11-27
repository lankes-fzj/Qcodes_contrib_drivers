"""
Wrapper for the wlmData.dll which controls the HighFinesse Wavemeter.

The class ``WlmDataLib`` wraps the functions from the DLL and makes them
accessible via Python functions.

Authors:
    Lankes, Lukas (Forschungszentrum Jülich, IBI-TAE) <l.lankes@fz-juelich.de>
"""

import logging

from .wlmData import load_dll, close_dll

__all__ = ["WlmDataLib", "WlmDataLibError"]


logger = logging.getLogger(__name__)


class WlmDataLibError(Exception):
    """Default exception class for AttoDryLib

    Args:
        message (str): Error message
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class WlmDataLib:
    """Wrapper class for the library "wlmData.dll"

    This class wraps the functions of the DLL and makes them accessible via
    Python functions.

    Args:
        path_to_dll (str, optional): Path to the library "wlmData.dll"
        or None, if it is in the working directory or system path.
                    
    Raises:
        FileNotFoundError: When the DLL cannot be found
    """

    def __init__(self, path_to_dll: str = None):
        self._dll = load_dll(path_to_dll)

    def __del__(self) -> None:
        """Closes library when this object is deleted."""
        if self._dll is not None:
            # Close if not happened before
            self.close()

    def close(self) -> None:
        """Unloads library."""
        close_dll()
