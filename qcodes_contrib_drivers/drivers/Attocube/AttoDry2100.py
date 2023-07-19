"""
QCodes-instrument for the Attocube attoDRY2100.

Authors:
    Lankes, Lukas (Forschungszentrum Jülich, IBI-TAE) <l.lankes@fz-juelich.de>
"""

import warnings
import qcodes as qc
from .AttoDryLib import AttoDryLib, AttoDryDevice, AttoDryLibError

__all__ = ["AttoDry2100"]


class AttoDry2100(qc.Instrument):
    """QCodes driver for Atttocube AttoDRY2100.

    Args:
        name: Name of the instrument
        com_port: COM-port the device is connected to
        path_to_dll (str, optional): Path to the library "attoDRYLib.dll"
    """

    def __init__(self, name: str, com_port: str, path_to_dll: str = None):
        super().__init__(name)

        # Create library wrapper
        self._library = AttoDryLib(AttoDryDevice.AttoDry2100, path_to_dll)

        try:
            self._library.connect(com_port)

            # Validate if device is initialized
            if not self._library.is_initialized():
                raise AttoDryLibError("AttoDRY device is not initialized!")
        except Exception:
            # Close instrument if something fails after library was created
            self.close()
            raise

        # Configure QCodes parameters
        self.add_parameter("user_temperature",
                           get_cmd=self._library.get_user_temperature,
                           set_cmd=self._library.set_user_temperature,
                           unit="K",
                           vals=qc.utils.validators.Numbers(0),  # Minimum 0 K
                           docstring="User set point temperature in Kelvin")
        self.add_parameter("sample_temperature",
                           get_cmd=self._library.get_sample_temperature,
                           set_cmd=False,
                           unit="K",
                           vals=qc.utils.validators.Numbers(0),  # Minimum 0 K
                           docstring="Sample temperature in Kelvin")
        
        self.add_parameter("error_status",
                           get_cmd=self._library.get_error_status,
                           set_cmd=False,
                           vals=qc.utils.validators.Strings(),
                           docstring="Current error status")
        self.add_parameter("error_message",
                           get_cmd=self._library.get_error_message,
                           set_cmd=False,
                           vals=qc.utils.validators.Strings(),
                           docstring="Current error message")
        self.add_parameter("action_message",
                           get_cmd=self._library.get_action_message,
                           set_cmd=False,
                           vals=qc.utils.validators.Strings(),
                           docstring="Current action message")
        self.add_parameter("temperature_control",
                           get_cmd=self._library.is_controlling_temperature,
                           set_cmd=False,
                           vals=qc.utils.validators.Bool(),
                           docstring="Checks if temperature control is active")

        self.add_parameter("_is_connected",
                           get_cmd=self._library.is_connected,
                           set_cmd=False,
                           vals=qc.utils.validators.Bool(),
                           docstring="Checks if device is connected")
        self.add_parameter("_is_initialized",
                           get_cmd=self._library.is_initialized,
                           set_cmd=False,
                           vals=qc.utils.validators.Bool(),
                           docstring="Checks if device is initialized")
    
    def close(self) -> None:
        """Closes the instrument.

        This function disconnects the device and unloads the library.
        """
        if self._library is None:
            # Already closed
            return
        
        # Try to close device connection
        try:
            if self._library.is_connected():
                self._library.disconnect()
        except Exception as exc:
            warnings.warn(exc)
        
        # Try to unload library
        try:
            self._library.close()
        finally:
            self._library = None
        
        # Also let Qcodes close its ressources
        super().close()
        
    def confirm(self) -> None:
        """Sends a 'Confirm' command to the attoDRY.
        
        Use this when you want to respond positively to a pop up.
        """
        self._library.confirm()
    
    def cancel(self) -> None:
        """Sends a 'Cancel' Command to the attoDRY.
        
        Use this when you want to cancel an action or respond negatively to a
        pop up.
        """
        self._library.cancel()

    def toggle_full_temperature_control(self) -> None:
        """Toggles temperature control, just as the thermometer icon on the
        touch screen.
        """
        self._library.toggle_full_temperature_control()
    
    def toggle_sample_temperature_control(self) -> None:
        """Toggles the sample temperature controller.
        
        This command only toggles the sample temperature controller. It does
        not pump the volumes etc. Use `toggle_full_temperature_control` for
        behaviour like the temperature control icon on the touch screen.
        """
        self._library.toggle_sample_temperature_control()
