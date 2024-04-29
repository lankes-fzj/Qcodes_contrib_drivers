import functools as ft
import typing as tp
import math

import qcodes as qc

from .Sepia_Library import PicoquantSepia2Lib, PicoquantSepia2LibError


class PicoquantSepia2Module(qc.instrument.InstrumentChannel):
    """Picoquant Sepia II common module.
    
    The functions of the common module are strictly generic and will work on any module you might
    find plugged to a Picoquant laser device. Except for the functions on presets and updates, they
    are mainly informative.
    
    This class serves as base class for all other modules and is also used for not yet implemented
    modules.
    
    Args:
        parent (qc.Instrument): Parent instrument
        name (str): Instrument module name
        slot_id (int): Module's slot id
        is_primary (bool, optional): True, if this is a primary module (default)
    """
    def __init__(self, parent: "PicoquantSepia2", name: str, slot_id: int, is_primary: bool = True):
        super().__init__(parent, name)

        self._slot_id = slot_id
        self._is_primary = is_primary

        self._lib = self.parent._lib
        self._device_id = self.parent._device_id

        self._serial_num = \
            self._lib.com_get_serial_number(self._device_id, self._slot_id, self._is_primary)
        self._label, self._release_date, self._revision, self._memo = \
            self._lib.com_get_supplementary_infos(self._device_id, self._slot_id, self._is_primary)


class PicoquantSepia2SCMModule(PicoquantSepia2Module):
    """Picoqunt Sepia II SCM module
    
    This module implements the safety features of the PQ Laser Device, as there are the thermal and
    voltage monitoring, the interlock (hard locking) and soft locking capabilities.

    Args:
        parent (qc.Instrument): Parent instrument
        name (str): Instrument module name
        slot_id (int): Module's slot id
        is_primary (bool, optional): Primary (True, default) or secondary (False) module
        disable_soft_lock (bool, optional): True (default) to disable soft lock on initialization
    """

    def __init__(self, parent: "PicoquantSepia2", name: str, slot_id: int, is_primary: bool = True,
                 disable_soft_lock: bool = True):
        super().__init__(parent, name, slot_id, is_primary)

        self.add_parameter("lock",
                           label="Lock state of laser power line",
                           get_cmd=ft.partial(self._lib.scm_get_laser_locked,
                                              self._device_id, self._slot_id),
                           set_cmd=False,
                           vals=qc.validators.Bool(),
                           docstring="State of the laser power line. Indicates if the laser is " +
                                     "down either by hardlock, softlock or power failure.")
        self.add_parameter("soft_lock",
                           label="Soft lock register",
                           get_cmd=ft.partial(self._lib.scm_get_laser_soft_lock,
                                              self._device_id, self._slot_id),
                           set_cmd=ft.partial(self._lib.scm_set_laser_soft_lock,
                                              self._device_id, self._slot_id),
                           vals=qc.validators.Bool(),
                           docstring="Content of soft lock register. To get the real lock-state " +
                                     "the laser, user parameter `lock` instead.")

        if disable_soft_lock and self.soft_lock():
            # Disable soft lock
            self.soft_lock(False)


class PicoquantSepia2SLMModule(PicoquantSepia2Module):
    """Picoqunt Sepia II SLM 828 module
    
    SLM 828 modules can interface the huge families of pulsed laser diode heads (LDH series) and
    pulsed LED heads (PLS series) from Picoquant. These functions let the application control their
    working modes and intensity.

    Args:
        parent (qc.Instrument): Parent instrument
        name (str): Instrument module name
        slot_id (int): Module's slot id
        is_primary (bool, optional): Primary (True, default) or secondary (False) module
    """

    def __init__(self, parent: "PicoquantSepia2", name: str, slot_id: int, is_primary: bool = True):
        super().__init__(parent, name, slot_id, is_primary)

        self.add_parameter("power",
                           label="Power intensity",
                           unit="%",
                           get_cmd=ft.partial(self._lib.slm_get_intensity_fine_step,
                                              self._device_id, self._slot_id),
                           set_cmd=ft.partial(self._lib.slm_set_intensity_fine_step,
                                              self._device_id, self._slot_id),
                           vals=qc.validators.Numbers(0, 100),
                           get_parser=lambda raw: raw / 10,
                           set_parser=lambda val: int(val * 10),
                           docstring="Power intensity in percent of the controlling voltage")
        self.add_parameter("freq_mode",
                           label="Frequency mode",
                           get_cmd=ft.partial(self._lib.slm_get_pulse_parameters,
                                              self._lib._device_id, self._slot_id),
                           set_cmd=self._set_freq,
                           get_parser=lambda raw: raw[0],
                           val_mapping={"80MHz": 0,
                                        "40MHz": 1,
                                        "20MHz": 2,
                                        "10MHz": 3,
                                        "5MHz": 4,
                                        "2.5MHz": 5,
                                        "rising edge": 6,
                                        "falling edge": 7},
                           vals=qc.validators.Ints(0, 7),
                           docstring="Index to the list of internal frequencies or external " +
                                     "trigger modi.")
        self.add_parameter("freq",
                           label="Frequency",
                           unit="MHz",
                           get_cmd=ft.partial(self._lib.slm_get_pulse_parameters,
                                               self._lib._device_id, self._slot_id),
                           set_cmd=self._set_freq,
                           get_parser=lambda raw: raw[0],
                           val_mapping={80: 0,  # 80 MHz
                                        40: 1,  # 40 MHz
                                        20: 2,  # 20 MHz
                                        10: 3,  # 10 MHz
                                        5: 4,  # 5 MHz
                                        2.5: 5,  # 2.5 MHz
                                        math.inf: 6,  # rising edge
                                        -math.inf: 7},  # falling edge
                           vals=qc.validators.Ints(0, 7),
                           docstring="Frequency in MHz. Or +/- infinity for rising/falling edge " +
                                     "trigger mode")
        self.add_parameter("mode",
                           label="Pulse mode",
                           get_cmd=ft.partial(self._lib.slm_get_pulse_parameters,
                                              self._lib._device_id, self._slot_id),
                           set_cmd=self._set_pulse_mode,
                           get_parser=lambda raw: raw[1],
                           val_mapping={"pulsed": True, "cw": False},
                           vals=qc.validators.Bool(),
                           docstring="Pulse mode, standing for either 'pulses enabled' (True / " +
                                     "\"pulsed\") or 'continuous wave' (False / \"cw\").")

    def _set_freq(self, freq: int) -> None:
        _, pulse_mode, _ = self._lib.slm_get_pulse_parameters(self._device_id, self._slot_id)
        self._lib.slm_set_pulse_parameters(self._device_id, self._slot_id, freq, pulse_mode)

    def _set_pulse_mode(self, pulse_mode: bool) -> None:
        freq, _, _ = self._lib.slm_get_pulse_parameters(self._device_id, self._slot_id)
        self._lib.slm_set_pulse_parameters(self._device_id, self._slot_id, freq, pulse_mode)


class PicoquantSepia2(qc.Instrument):
    """Picoquant Sepia II instrument

    Picoquant Laser Devices of the product model "Sepia II" are usually equipped with an oscillator
    module (type SOM 828 or SOM 828-D) in slot 100 and a variable number of SLM 828 laser driver
    modules in the higher numbered slots.
    But as the Sepia II is the forebear to the whole family, it could house literally all types of
    slot-mountable modules designed for the family.

    There are several options to connect to the laser device:
    * by device id: Uses the internal device id (0..7) given by the library (-1 to ignore device id)
    * by product model and/or serial number: If no device id is given, the intrument driver selects
        the first matching device. The results can be filtered by product model and serial number.

    Args:
        name (str):
        device_id (int, optional): Id of the device to connect to (0..7)
        product_model (str, optional): Product model name to search for
        serial_num (str, optional): Serial number to search for
        dll_path (str, optional): Path to the driver DLL
        str_encoding (str, optional): String encoding used for the DLL functions
        perform_restart (bool, optional): True, to restart the instrument and reload all modules
                                          (default: False)
    """

    def __init__(self, name, device_id: int = -1, product_model: str = None, serial_num: str = None,
                 dll_path: str = None, str_encoding: str = None, perform_restart: bool = False):
        super().__init__(name)

        self._lib = PicoquantSepia2Lib(dll_path, str_encoding)

        self._device_id = device_id

        if self._device_id < 0:
            # Find first matching device
            for i in range(8):
                try:
                    # Try to open device
                    self._serial_num, self._product_model = \
                        self._lib.usb_open_device(i, product_model, serial_num)
                    # No error ocurred -> device found
                    self._device_id = i
                    break
                except PicoquantSepia2LibError:
                    pass
            else:
                raise RuntimeError("Could not find Picoquant Sepia II device matching the " +
                                   "conditions")

        # Get firmware version
        self._fw_version = self._lib.fwr_get_version(self._device_id)

        # Initialize modules
        self._modules = self._init_modules(perform_restart)

        # Print connect message
        self.connect_message()

    def get_idn(self) -> tp.Dict[str, str]:
        """Gets device information (vendor, model, serial number and firmware version) as
        dictionary. This is used by the IDN parameter.

        Returns:
            dict: Device information
        """
        return {"vendor": "PicoQuant", "model": self._product_model,
                "serial": self._serial_num, "firmware": self._fw_version}

    def close(self) -> None:
        """Close instrument connection and unload library"""
        self._lib.usb_close_device(self._device_id)
        super().close()

    def _init_modules(self, perform_restart: bool = False) -> tp.List[PicoquantSepia2Module]:
        """Iterate through device modules and add as instrument channels

        Args:
            perform_restart (bool, optional): Restart instrument when loading module list (default:
                False)

        Returns:
            List: List of connected instrument modules
        """
        modules = []
        # Get module list
        module_count = self._lib.fwr_get_module_map(self._device_id, perform_restart)

        try:
            slots = set()

            # Iterate through modules
            for i in range(module_count):
                slot_id, _, _, _ = self._lib.fwr_get_module_info_by_map_id(self._device_id, i)
                slots.add(slot_id)

            for slot_id in slots:
                # Get module type and name
                mod_type = self._lib.com_get_module_type(self._device_id, slot_id, True)
                mod_type_name = self._lib.com_decode_module_type(mod_type)
                mod_type_abbr = self._lib.com_decode_module_type_abbr(mod_type)

                # Create module
                if mod_type_abbr == "SCM":
                    mod = PicoquantSepia2SCMModule(self, mod_type_name, slot_id)
                elif mod_type_abbr == "SLM":
                    mod = PicoquantSepia2SLMModule(self, mod_type_name, slot_id)
                else:
                    # Add unknown module type as common module
                    mod = PicoquantSepia2Module(self, mod_type_name, slot_id)

                modules.append(mod)
                # Add module as Qcodes-submodule
                self.add_submodule(mod_type_abbr, mod)
        finally:
            self._lib.fwr_free_module_map(self._device_id)

        # Add channel list
        ch_tuple = qc.instrument.ChannelTuple(self, "modules", PicoquantSepia2Module, self._modules)
        self.add_submodule("modules", ch_tuple)

        return modules

    @staticmethod
    def list_usb_devices(dll_path: str = None, str_encoding: str = None) \
            -> tp.List[tp.Tuple[int, str, str]]:
        """List connected Picoquant Sepia instruments.
        
        Also busy or blocked instruments are listed. Note that you cannot establish a connection to
        those devices. When trying to create an instance it will fail with code -9004 or -9005.

        Args:
            dll_path (str, optional): Path to DLL.
            str_encoding (str, optional): Sting encoding used for DLL functions

        Returns:
            List of tuples (int, str, str): List of devices with device id, product model and serial
                number
        """
        lib = PicoquantSepia2Lib(dll_path, str_encoding)
        devices = []

        # Iterate through device ids
        for i in range(8):
            try:
                # Open device, get information and close (ignore errors caused by busy instruments)
                product, serial = lib.usb_open_get_ser_num_and_close(i, ignore_blocked_busy=True)
            except PicoquantSepia2LibError:
                continue

            # Add device to list
            devices.append((i, product, serial))

        return devices
