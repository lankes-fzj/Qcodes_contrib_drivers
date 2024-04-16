import ctypes
import datetime
import enum
import os
import typing

from .Sepia_Library_utils import PicoquantSepia2LibError, handle_errors, \
    PicoquantSepia2WorkingMode, PicoquantSepia2SupportRequestOptions, \
    PicoquantSepia2Preset, PicoquantSepia2SOMDState, PicoquantSepia2SPMStates, \
    PicoquantSepia2SWSStates


class PicoquantSepia2Lib:
    """Wrapper for Picoquant Sepia II library.
    
    This class wraps all functions from Sepia2_Lib.dll to make it available in Python.
    
    Args:
        dll_path (str, optional): Path to DLL-file or None to use default path
        str_encoding (str, optional): Encoding used for strings (defaults to "utf-8")
    """

    _DEFAULT_DLL_PATH = r"C:\Program Files\Picoquant\GenericLaserDriver\Sepia2_Lib.dll"
    _DEFAULT_STR_ENCODING = "utf-8"

    def __init__(self, dll_path: str = None, str_encoding: str = None):
        self.dll = ctypes.CDLL(dll_path or self._DEFAULT_DLL_PATH)
        self.str_encoding = str_encoding or self._DEFAULT_STR_ENCODING

    def check_error(self, exit_code: int, function_name: str = None) -> None:
        """Checks a function's return code to see if it succeeded.
        
        In case of an error (exit_code != 0), an exception is raised.
        
        Args:
            exit_code: Return code of library function
            function_name (optional): Name of the library function called. This is used for more
                detailed error information in the exception.
        
        Raises:
            PicoquantSepia2LibError, if return code indicates a failure.
        """
        if exit_code == 0:
            # Nothing to do, in case of success
            return

        try:
            # Try to get an error description
            error_msg = self.lib_decode_error(exit_code)
        except PicoquantSepia2LibError:
            error_msg = None

        raise PicoquantSepia2LibError(exit_code, error_msg, function_name)

    @handle_errors
    def lib_decode_error(self, error_code: int) -> str:
        """This function is supposed to return an error string (human-readable) associated with a
        given error code.
        
        If `error_code` is no member of the legal error codes list, the function raises a
        PicoquantSepia2LibError.

        Args:
            error_code (int): error code, returned from any SEPIA2_...- function call

        Raises:
            PicoquantSepia2LibError: In case of unknown error code.

        Returns:
            str: error string
        """
        c_error_string = ctypes.create_string_buffer(64)

        internal_error_code = self.dll.SEPIA2_LIB_DecodeError(ctypes.c_int(error_code),
                                                              c_error_string)
        if internal_error_code == 0:
            # Return error message when function call was successful
            return c_error_string.value.decode(self.str_encoding)

        # Try to decode internal error code
        #  `check_error` cannot be used here, to prevent endless recursions
        internal_error_code_2 = self.dll.SEPIA2_LIB_DecodeError(ctypes.c_int(internal_error_code),
                                                                c_error_string)
        if internal_error_code_2 == 0:
            raise PicoquantSepia2LibError(internal_error_code,
                                          c_error_string.value.decode(self.str_encoding),
                                          "SEPIA2_LIB_DecodeError")
        else:
            raise PicoquantSepia2LibError(internal_error_code, None,
                                          "SEPIA2_LIB_DecodeError")

    @handle_errors
    def lib_get_version(self) -> str:
        """This function returns the current library version string. To be aware of version changing
        trouble, you should call this function and check the version string in your programs, too.
        
        The format of the version string is: <MajorVersion:1>.<MinorVersion:1>.<Target:2>.<Build>
        where <Target> identifies the word width of the CPU, the library was compiled for.
        
        A legal version string could read e.g. "1.1.32.393", which stands for the software version
        1.1, compiled for an x86 target architecture and coming as build 393, whilst "1.1.64.393"
        identifies the same software version, but compiled for a x64 target.
        
        Take care that at least the first three parts of the version string comply with the expected
        reference, thus check for compliance of the first 7 characters.
        
        Returns:
            str: library version string
        """
        c_version_string = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_LIB_GetVersion(c_version_string)
        self.check_error(error_code, "SEPIA2_LIB_GetVersion")

        return c_version_string.value.decode(self.str_encoding)

    @handle_errors
    def lib_is_running_on_wine(self) -> bool:
        """This function returns the boolean information if the library is running on Wine, relevant
        in a case of service. Besides this, this function is solely informative.

        Returns:
            bool: True, if running in a Wine environment on a POSIX system.
        """
        c_is_running_on_wine = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_LIB_IsRunningOnWine(ctypes.byref(c_is_running_on_wine))
        self.check_error(error_code, "SEPIA2_LIB_IsRunningOnWine")

        return bool(c_is_running_on_wine.value)

    @handle_errors
    def usb_open_device(self, device_id: int, product_model: str = None, serial_num: str = None) \
            -> (str, str):
        """On success, this function grants exclusive access to the PQ Laser Device on USB channel
        `device_id`. It returns the product model and serial number of the device, even if the
        device is blocked or busy (error code -9004 or -9005; refer to appendix 4.2).
        
        If called with non-empty string arguments, the respective string works as condition. If you
        pass a product model string, e.g. "Sepia II" or "Solea", all devices other than the
        specified model are ignored. The analogue goes, if you pass a serial number; Specifying both
        will work out as a logical AND performed on the respective conditions. Thus an error code is
        returned, if none of the connected devices fit the condition.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            product_model (str, optional): product model filter
            serial_num (str, optional): serial number filter

        Returns:
            str: product model
            str: serial number
        """
        c_product_model = ctypes.create_string_buffer(product_model or 32)
        c_serial_num = ctypes.create_string_buffer(serial_num or 12)

        error_code = self.dll.SEPIA2_USB_OpenDevice(ctypes.c_int(device_id),
                                                    ctypes.byref(c_product_model),
                                                    ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_USB_OpenDevice")

        return c_product_model.value.decode(self.str_encoding), \
            c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def usb_open_get_ser_num_and_close(self, device_id: int, product_model: str = None,
                                       serial_num: str = None) -> (str, str):
        """When called with empty string parameters given, this function is used to iteratively get
        a complete list of all currently present PQ Laser Devices.
        
        It returns the product model and serial number of the device, even if the device is blocked
        or busy (error code -9004 or -9005; refer to appendix 4.2). The function opens the PQ Laser
        Device on USB channel `device_id` nonexclusively, reads the product model and serial number
        and immediately closes the device again.
        
        When called with non-empty string parameters, with respect to the conditions, the function
        behaves as specified for the `usb_open_device` function.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            product_model (str, optional): product model filter
            serial_num (str, optional): serial number filter

        Returns:
            str: product model
            str: serial number
        """
        c_product_model = ctypes.create_string_buffer(product_model or 32)
        c_serial_num = ctypes.create_string_buffer(serial_num or 12)

        error_code = self.dll.SEPIA2_USB_OpenGetSerNumAndClose(ctypes.c_int(device_id),
                                                               ctypes.byref(c_product_model),
                                                               ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_USB_OpenGetSerNumAndClose")

        return c_product_model.value.decode(self.str_encoding), \
            c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def usb_get_str_descriptor(self, device_id: int) -> str:
        """Returns the concatenated string descriptors of the USB device. For a PQ Laser Device, you
        could find e.g. the product model string and the firmware build number there, relevant in a
        case of service. Besides this, this function is solely informative.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)

        Returns:
            str: USB string descriptors
        """
        c_descriptor = ctypes.create_string_buffer(255)

        error_code = self.dll.SEPIA2_USB_GetStrDescriptor(ctypes.c_int(device_id),
                                                          ctypes.byref(c_descriptor))
        self.check_error(error_code, "SEPIA2_USB_GetStrDescriptor")

        return c_descriptor.value.decode(self.str_encoding)

    @handle_errors
    def usb_close_device(self, device_id: int) -> None:
        """Terminates the exclusive access to the PQ Laser Device identified by `device_id`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
        """
        error_code = self.dll.SEPIA2_USB_CloseDevice(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_USB_CloseDevice")

    @handle_errors
    def fwr_decode_err_phase_name(self, phase_error: int) -> str:
        """This function also works "off-line", without a PQ Laser Device running. It decodes the
        phase in which an error occurred during the latest firmware start up. Refer to the
        `fwr_get_last_error` function below.

        Args:
            phase_error (int): error phase, returned by firmware function `fwr_get_last_error`

        Returns:
            str: error phase string
        """
        c_error_string = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_FWR_DecodeErrPhaseName(ctypes.c_int(phase_error),
                                                            ctypes.byref(c_error_string))
        self.check_error(error_code, "SEPIA2_FWR_DecodeErrPhaseName")

        return c_error_string.value.decode(self.str_encoding)

    @handle_errors
    def fwr_get_version(self, device_id: int) -> str:
        """This function, in opposite to other GetVersion functions only works "on line", with the
        need for a PQ Laser Device running. It returns the actual firmware version string. To be
        aware of version changing trouble, you should call this function and check the version in
        your programs, too.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)

        Returns:
            str: firmware version string
        """
        c_fw_version = ctypes.create_string_buffer(8)

        error_code = self.dll.SEPIA2_FWR_GetVersion(ctypes.c_int(device_id),
                                                    ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_FWR_GetVersion")

        return c_fw_version.value.decode(self.str_encoding)

    @handle_errors
    def fwr_get_last_error(self, device_id: int) -> (int, int, int, int, str):
        """This function returns the error description data from the last start up of the PQ Laser
        Device's firmware. Decode the error code using the function `lib_decode_error`. Analogous,
        use the function `fwr_decode_err_phase_name` for error phase. Location and condition can't
        be decoded and are introduced only for a few phases, but if given, they identify the
        circumstances of error more detailed.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)

        Returns:
            int: error code
            int: error phase
            int: error location
            int: error slot
            str: error condition string
        """
        c_error_code = ctypes.c_int()
        c_phase = ctypes.c_int()
        c_location = ctypes.c_int()
        c_slot = ctypes.c_int()
        c_condition = ctypes.create_string_buffer(55)

        error_code = self.dll.SEPIA2_FWR_GetLastError(ctypes.c_int(device_id),
                                                      ctypes.byref(c_error_code),
                                                      ctypes.byref(c_phase),
                                                      ctypes.byref(c_location),
                                                      ctypes.byref(c_slot),
                                                      ctypes.byref(c_condition))
        self.check_error(error_code, "SEPIA2_FWR_GetLastError")

        return c_error_code.value, c_phase.value, c_location.value, c_location.value, \
            c_slot.value, c_condition.value.decode(self.str_encoding)

    @handle_errors
    def fwr_get_module_map(self, device_id: int, perform_restart: bool) -> int:
        """The map is a firmware and library internal data structure, which is essential to the work
        with PQ Laser Devices. It will be created by the firmware during start up. The library needs
        to have a copy of an actual map before you may access any module. You don't need to prepare
        memory, the function autonomously manages the memory acquirements for this task.

        Since the firmware doesn't actualise the map once it is running, you might wish to restart
        the firmware to assure up to date mapping. You could switch the power off and on again to
        reach the same goal, but you also could more simply call this function with
        `perform_restart` set to 1. The PQ Laser Device will perform the whole booting cycle with
        the tiny difference of not needing to load the firmware again...

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            perform_restart (bool): defines, if a soft restart should precede fetching the map

        Returns:
            int: current number of PQ Laser Device configurational elements
        """
        c_module_count = ctypes.c_int()

        error_code = self.dll.SEPIA2_FWR_GetModuleMap(ctypes.c_int(device_id),
                                                      ctypes.c_int(int(perform_restart)),
                                                      ctypes.byref(c_module_count))
        self.check_error(error_code, "SEPIA2_FWR_GetModuleMap")

        return c_module_count.value

    @handle_errors
    def fwr_get_module_info_by_map_id(self, device_id: int, map_id: int) -> (int, bool, bool, bool):
        """Once the map is created and populated by the function `fwr_get_module_map`, you can scan
        it module by module, using this function. It returns the slot number, which is needed for
        all module-related functions later on, and three additional boolean information, namely if
        the module in question is a primary (e. g. laser driver) or a secondary module (e. g. laser
        head), if it identifies a backplane and furthermore, if the module supports uptime counters.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            map_id (int): index into the map; defines, which module's info is requested

        Returns:
            slot_id (int): slot number of the module identified by `map_id`
            is_primary (bool): true, if the index given points to a primary module
            is_back_plane (bool): true, if the map index given points to a backplane
            has_utc (bool): true, if the map index given points to a module with uptime counter
        """
        c_slot_id = ctypes.c_int()
        c_is_primary = ctypes.c_ubyte()
        c_is_back_plane = ctypes.c_ubyte()
        c_has_utc = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_FWR_GetModuleInfoByMapIdx(ctypes.c_int(device_id),
                                                               ctypes.c_int(map_id),
                                                               ctypes.byref(c_slot_id),
                                                               ctypes.byref(c_is_primary),
                                                               ctypes.byref(c_is_back_plane),
                                                               ctypes.byref(c_has_utc))
        self.check_error(error_code, "SEPIA2_FWR_GetModuleInfoByMapIdx")

        return c_slot_id.value, bool(c_is_primary.value), bool(c_is_back_plane.value), \
            bool(c_has_utc.value)

    @handle_errors
    def fwr_get_uptime_info_by_map_id(self, device_id: int, map_id: int) -> (float, float, float):
        """If the function `fwr_get_module_info_by_map_id` returned true for `has_utc`, you can get
        three counter values using this function. They can be used to roughly calculate the power up
        times.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            map_id (int): index into the map; defines, which module's info is requested

        Returns:
            main_power (int): main power up counter value of the module identified by `map_id`.
                Divide by 51 to get an approximation of the power up time in minutes
            active_power (int): active power up counter value of the module identified by `map_id`.
                Divide by 51 to get an approximation of the active power up time (i.e. laser
                unlocked) in minutes
            scaled_power (int): scaled power up counter value of the module identified by `map_id`.
                If it is > 255, divide this value by the active power up counter to get an
                approximation of the power factor
        """
        c_main_power = ctypes.c_ulong()
        c_active_power = ctypes.c_ulong()
        c_scaled_power = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_FWR_GetUptimeInfoByMapIdx(ctypes.c_int(device_id),
                                                               ctypes.c_int(map_id),
                                                               ctypes.byref(c_main_power),
                                                               ctypes.byref(c_active_power),
                                                               ctypes.byref(c_scaled_power))
        self.check_error(error_code, "SEPIA2_FWR_GetUptimeInfoByMapIdx")

        return c_main_power.value, c_active_power.value, c_scaled_power.value

    @handle_errors
    def fwr_create_support_request_text(self, device_id: int, preamble: str, calling_sw: str,
                                        options: PicoquantSepia2SupportRequestOptions) -> str:
        """This function creates a comprehensive description of the laser device in its running
        environment e.g. for use in support requests. In case support is needed, PicoQuant relies on
        proper information on the current system state.
        The function creates a standardized description of the as-is state of the whole system. The
        user has to provide it with additional system information: The preamble as given in
        `preamble` is equivalent to the prompting text at the beginning, finishing right before the
        first cutting mark. The information on the calling software as given in `calling_sw` is led
        in by an appropriate title and ends just before the information on the DLL itself.
        The analysis result of the current state of the PicoQuant Laser Device is presented in form
        of a module list. This information is supplemented by global system information,
        incorporatingthe paragraphs on the processors, memory usage, the operating system and all
        currently loaded software modules at the end of the description.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            preamble (str): preamble string
            calling_sw (str): description of the calling software
            options (PicoquantSepia2SupportRequestOptions): options specification

        Returns:
            str: support request text
        """
        c_preamble = ctypes.create_string_buffer(preamble.encode(self.str_encoding))
        c_calling_sw = ctypes.create_string_buffer(calling_sw.encode(self.str_encoding))

        buf_size = 8192
        error_code = -1001  # SEPIA2_ERR_FW_MEMORY_ALLOCATION_ERROR (FW: memory allocation error)

        # Retry until text fits in buffer
        while error_code == -1001:
            c_buffer = ctypes.create_string_buffer(buf_size)

            error_code = self.dll.SEPIA2_FWR_CreateSupportRequestText(
                ctypes.c_int(device_id), c_preamble, c_calling_sw, ctypes.c_int(options),
                ctypes.c_int(buf_size), ctypes.byref(c_buffer))

            buf_size *= 2  # Try again with twice the buffer size in case of failure

        self.check_error(error_code, "SEPIA2_FWR_CreateSupportRequestText")

        return c_buffer.value.decode(self.str_encoding)

    @handle_errors
    def fwr_free_module_map(self, device_id: int) -> None:
        """Since the library had to allocate memory for the map during the `fwr_get_module_map`
        function, this function is to restitute the memory just before your program terminates. You
        don't need to call this function between two calls of `fwr_get_module_map` for the same
        device index but you should call it for each device you ever inquired a map during the
        runtime of your program.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
        """
        error_code = self.dll.SEPIA2_FWR_FreeModuleMap(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_FreeModuleMap")

    @handle_errors
    def fwr_get_working_mode(self, device_id: int) -> PicoquantSepia2WorkingMode:
        """This function returns the current working mode.

        Notice, that this function needs at least a firmware version 1.05.420

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)

        Returns:
            PicoquantSepia2WorkingMode: current firmware working mode
        """
        c_mode = ctypes.c_int()

        error_code = self.dll.SEPIA2_FWR_GetWorkingMode(ctypes.c_int(device_id),
                                                        ctypes.byref(c_mode))
        self.check_error(error_code, "SEPIA2_FWR_GetWorkingMode")

        return PicoquantSepia2WorkingMode(c_mode.value)

    @handle_errors
    def fwr_set_working_mode(self, device_id: int, mode: PicoquantSepia2WorkingMode) -> None:
        """This function sets the new working mode.

        Notice, that this function needs at least a firmware version 1.05.420

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            mode (PicoquantSepia2WorkingMode): new firmware working mode

        Returns:
            PicoquantSepia2WorkingMode: current firmware working mode
        """
        error_code = self.dll.SEPIA2_FWR_SetWorkingMode(ctypes.c_int(device_id), ctypes.c_int(mode))
        self.check_error(error_code, "SEPIA2_FWR_SetWorkingMode")

    @handle_errors
    def fwr_store_as_permanent_values(self, device_id: int) -> None:
        """This function calculates the protective data for all modules changed and sends them to
        the device. The working mode stays "volatile".

        Notice, that this function needs at least a firmware version 1.05.420

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
        """
        error_code = self.dll.SEPIA2_FWR_StoreAsPermanentValues(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_StoreAsPermanentValues")

    @handle_errors
    def fwr_roll_back_to_permanent_values(self, device_id: int) -> None:
        """This function re-sends commands to discard all changes made since the working mode was
        switched. The working mode changes to "stay permanent".

        Notice, that this function needs at least a firmware version 1.05.420

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
        """
        error_code = self.dll.SEPIA2_FWR_RollBackToPermanentValues(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_RollBackToPermanentValues")

    @handle_errors
    def com_decode_module_type(self, module_type: int) -> str:
        """This function works "off line", without a PQ Laser Device running. It decodes the module
        type code returned by the common function `com_get_module_type` and returns the appropriate
        module type string (ASCII-readable).

        Args:
            module_type (int): module type, returned by common function
                `com_get_module_type`

        Returns:
            str: module type string
        """
        c_module_type_str = ctypes.create_string_buffer(55)

        error_code = self.dll.SEPIA2_COM_DecodeModuleType(ctypes.c_int(module_type),
                                                          ctypes.byref(c_module_type_str))
        self.check_error(error_code, "SEPIA2_COM_DecodeModuleType")

        return c_module_type_str.value.decode(self.str_encoding)

    @handle_errors
    def com_decode_module_type_abbr(self, module_type: int) -> str:
        """This function works "off line", without a PQ Laser Device running, too. It decodes the
        module type code returned by the common function `com_get_module_type` and returns the
        appropriate module type abbreviation string (ASCII-readable).

        Args:
            module_type (int): module type, returned by common function `com_get_module_type`

        Returns:
            str: module type abbr. string
        """
        c_module_type_abbr = ctypes.create_string_buffer(4)

        error_code = self.dll.SEPIA2_COM_DecodeModuleTypeAbbr(ctypes.c_int(module_type),
                                                              ctypes.byref(c_module_type_abbr))
        self.check_error(error_code, "SEPIA2_COM_DecodeModuleTypeAbbr")

        return c_module_type_abbr.value.decode(self.str_encoding)

    @handle_errors
    def com_get_module_type(self, device_id: int, slot_id: int, get_primary: bool) -> int:
        """Returns the module type code for a primary or secondary module respectively, located in a
        given slot.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot

        Returns:
            int: module type
        """
        c_module_type = ctypes.c_int()

        error_code = self.dll.SEPIA2_COM_GetModuleType(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_int(get_primary),
                                                       ctypes.byref(c_module_type))
        self.check_error(error_code, "SEPIA2_COM_GetModuleType")

        return c_module_type.value

    @handle_errors
    def com_get_serial_number(self, device_id: int, slot_id: int, get_primary: bool) -> str:
        """Returns the serial number for a given module.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot

        Returns:
            str: serial number string
        """
        c_serial_num = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_COM_GetSerialNumber(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(get_primary),
                                                         ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_COM_GetSerialNumber")

        return c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def com_get_preset_info(self, device_id: int, slot_id: int, get_primary: bool,
                            preset_nr: PicoquantSepia2Preset) -> (bool, str):
        """Returns the preset info identified by `preset_nr` for a given module. Initially, the
        content of preset 1 and preset 2 is not assigned; In this case, the content of `is_set` will
        be false (i.e. 0). Additionally, the text stored with the presets when the function
        `com_save_as_preset` was last invoked for the preset block, is returned in `preset_memo`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot
            preset_nr (PicoquantSepia2Preset): preset number

        Returns:
            is_set (bool): True, if preset block was already assigned
            preset_memo (str): preset memo
        """
        c_is_set = ctypes.c_ubyte()
        c_preset_memo = ctypes.create_string_buffer(64)

        error_code = self.dll.SEPIA2_COM_GetPresetInfo(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_int(get_primary),
                                                       ctypes.c_int(preset_nr),
                                                       ctypes.byref(c_is_set),
                                                       ctypes.byref(c_preset_memo))
        self.check_error(error_code, "SEPIA2_COM_GetPresetInfo")

        return bool(c_is_set.value), c_preset_memo.value.decode(self.str_encoding)

    @handle_errors
    def com_recall_preset(self, device_id: int, slot_id: int, get_primary: bool,
                          preset_nr: PicoquantSepia2Preset) -> None:
        """Recalls the preset data as stored in the preset block identified by `preset_nr`.
        Recalling a preset means to overwrite all current settings by the desired ones. The settings
        previously active are lost!

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot
            preset_nr (PicoquantSepia2Preset): preset number
        """
        error_code = self.dll.SEPIA2_COM_RecallPreset(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      ctypes.c_int(get_primary),
                                                      ctypes.c_int(preset_nr))
        self.check_error(error_code, "SEPIA2_COM_RecallPreset")

    @handle_errors
    def com_save_as_preset(self, device_id: int, slot_id: int, get_primary: bool,
                          preset_nr: PicoquantSepia2Preset, preset_memo: str) -> None:
        """Stores the currently active settings into the preset block identified by `preset_nr` for
        a given module. Consider, if presets were already stored in the desired presets block, they
        will be overwritten without any further request. Don't forget to pass a meaningful text over
        with the `preset_memo`; It might be working as a remainder to prevent you from an
        unintentional loss of preset data. Use the `com_get_preset_info` function to get informed on
        potential presets already stored in the destination block.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot
            preset_nr (PicoquantSepia2Preset): preset number
            preset_memo (str): preset memo
        """
        c_preset_memo = ctypes.create_string_buffer(preset_memo)

        error_code = self.dll.SEPIA2_COM_SaveAsPreset(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      ctypes.c_int(get_primary),
                                                      ctypes.c_int(preset_nr),
                                                      c_preset_memo)
        self.check_error(error_code, "SEPIA2_COM_SaveAsPreset")

    @handle_errors
    def com_get_supplementary_infos(self, device_id: int, slot_id: int, get_primary: bool) \
            -> (str, datetime.datetime, str, str):
        """Returns supplementary string information for a given module. Mainly needed for support...

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot

        Returns:
            label (str): internal label string
            release_date (datetime.datetime): release date string
            revision (str): revision string
            memo (str): serial number string
        """
        c_label = ctypes.create_string_buffer(8)
        c_release_date = ctypes.create_string_buffer(8)
        c_revision = ctypes.create_string_buffer(8)
        c_memo = ctypes.create_string_buffer(128)

        error_code = self.dll.SEPIA2_COM_GetSupplementaryInfos(ctypes.c_int(device_id),
                                                               ctypes.c_int(slot_id),
                                                               ctypes.c_int(get_primary),
                                                               ctypes.byref(c_label),
                                                               ctypes.byref(c_release_date),
                                                               ctypes.byref(c_revision),
                                                               ctypes.byref(c_memo))
        self.check_error(error_code, "SEPIA2_COM_GetSupplementaryInfos")

        release_date = datetime.datetime.strptime(c_release_date.value.decode(self.str_encoding),
                                                  "%y/%m/%d")

        return c_label.value.decode(self.str_encoding), release_date, \
            c_revision.value.decode(self.str_encoding), c_memo.value.decode(self.str_encoding)

    @handle_errors
    def com_has_secondary_module(self, device_id: int, slot_id: int) -> bool:
        """Returns if the module in the named slot has attached a secondary one (laser head).

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)

        Returns:
            has_secondary (bool): True, if the module in the named slot has attached a secondary one
        """
        c_has_secondary = ctypes.c_int()

        error_code = self.dll.SEPIA2_COM_HasSecondaryModule(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_has_secondary))
        self.check_error(error_code, "SEPIA2_COM_HasSecondaryModule")

        return bool(c_has_secondary.value)

    @handle_errors
    def com_is_writable_module(self, device_id: int, slot_id: int, get_primary: bool) -> bool:
        """Returns the write protection state of the module's definition, calibration and set-up
        memory.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            get_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot

        Returns:
            is_writeable (bool): false, if the memory block is write protected
        """
        c_is_writable = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_COM_IsWritableModule(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(get_primary),
                                                          ctypes.byref(c_is_writable))
        self.check_error(error_code, "SEPIA2_COM_IsWritableModule")

        return bool(c_is_writable.value)

    @handle_errors
    def com_update_module_data(self, device_id: int, slot_id: int, set_primary: bool,
                               dcl_filename: str) -> None:
        """Update module data

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number (000..989; refer to manual on slot numbers)
            set_primary (bool): defines, if this call concerns a primary (e.g. laser driver) or a
                secondary module (e.g. laser head) in the given slot
            dcl_filename (str): file name (coming as windows path), of the binary image of the
                update data
        """
        c_dcl_filename = ctypes.create_string_buffer(dcl_filename)

        error_code = self.dll.SEPIA2_COM_UpdateModuleData(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(set_primary),
                                                          ctypes.byref(c_dcl_filename))
        self.check_error(error_code, "SEPIA2_COM_UpdateModuleData")

    @handle_errors
    def scm_get_power_and_laser_leds(self, device_id: int, slot_id: int) -> (bool, bool):
        """Returns the state of the power LED and the laser active LED.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SCM module

        Returns:
            power_led (bool): state of the power LED (true: LED is on)
            laser_active_led (bool): state of the laser active LED (true: LED is on)
        """
        c_power_led = ctypes.c_ubyte()
        c_laser_active_led = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SCM_GetPowerAndLaserLEDS(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              ctypes.byref(c_power_led),
                                                              ctypes.byref(c_laser_active_led))
        self.check_error(error_code, "SEPIA2_SCM_GetPowerAndLaserLEDS")

        return bool(c_power_led.value), bool(c_laser_active_led)

    @handle_errors
    def scm_get_laser_locked(self, device_id: int, slot_id: int) -> bool:
        """Returns the state of the laser power line. If the line is down either by hardlock (key),
        power failure or softlock (firmware, GUI or custom program) it returns locked (i.e. True),
        otherwise unlocked (i.e. False).

        Note, that you can't decide for what reason the line is down...

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SCM module

        Returns:
            is_locked (bool): laser lock state
        """
        c_is_locked = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SCM_GetLaserLocked(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_is_locked))
        self.check_error(error_code, "SEPIA2_SCM_GetLaserLocked")

        return bool(c_is_locked.value)

    @handle_errors
    def scm_get_laser_soft_lock(self, device_id: int, slot_id: int) -> bool:
        """Returns the contents of the soft lock register.
        
        Note, that this information will not stand for the real state of the laser power line. A
        hard lock overrides a soft unlock...

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SCM module

        Returns:
            is_soft_locked (bool): contents of the soft lock register
        """
        c_is_soft_locked = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SCM_GetLaserSoftLock(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_is_soft_locked))
        self.check_error(error_code, "SEPIA2_SCM_GetLaserSoftLock")

        return bool(c_is_soft_locked.value)

    @handle_errors
    def scm_set_laser_soft_lock(self, device_id: int, slot_id: int, soft_locked: bool) -> None:
        """Sets the contents of the soft lock register.
        
        Note, that this information will not stand for the real state of the laser power line. A
        hard lock overrides a soft unlock...

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SCM module
            soft_locked (bool): desired value for the soft lock register
        """
        error_code = self.dll.SEPIA2_SCM_SetLaserSoftLock(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_ubyte(soft_locked))
        self.check_error(error_code, "SEPIA2_SCM_SetLaserSoftLock")

    @handle_errors
    def som_decode_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> str:
        """Returns the frequency resp. trigger mode string at list position `freq_trig_mode` for a
        given SOM module. This function only works "on line", with a PQ Laser Device running,
        because each SOM may carry its individual list of reference sources. Only the list positions
        0 and 1 are identical for all SOM modules: They always carry the external trigger option on
        respectively raising and falling edges. To get the whole table, loop over the list position
        index starting with 0 until the function terminates with an error.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            freq_trig_mode (int): index into the list of reference sources (0..4)

        Returns:
            freq_trig_mode_str (str): frequency resp. trigger mode string
        """
        c_freq_trig_mode_str = ctypes.create_string_buffer(32)

        error_code = self.dll.SEPIA2_SOM_DecodeFreqTrigMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq_trig_mode),
                                                            ctypes.byref(c_freq_trig_mode_str))
        self.check_error(error_code, "SEPIA2_SOM_DecodeFreqTrigMode")

        return c_freq_trig_mode_str.value.decode(self.str_encoding)

    @handle_errors
    def som_get_freq_trig_mode(self, device_id: int, slot_id: int) -> int:
        """This function inquires the current setting for the reference source in a given SOM. In
        the integer variable, pointed to by `freq_trig_mode` it returns an index into the list of
        possible sources.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            freq_trig_mode (int): index into the list of reference sources
        """
        c_freq_trig_mode = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOM_GetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_freq_trig_mode))
        self.check_error(error_code, "SEPIA2_SOM_GetFreqTrigMode")

        return c_freq_trig_mode.value

    @handle_errors
    def som_set_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> None:
        """This function sets the new reference source for a given SOM. It is passed over as a new
        value for the index into the list of possible sources.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            freq_trig_mode (int): index into the list of reference sources
        """
        error_code = self.dll.SEPIA2_SOM_SetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(freq_trig_mode))
        self.check_error(error_code, "SEPIA2_SOM_SetFreqTrigMode")

    @handle_errors
    def som_get_trigger_range(self, device_id: int, slot_id: int) -> (int, int):
        """This function gets the adjustable range of the trigger level. The limits are specified in
        mV.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            trig_range_low (int): lower limit of the trigger range
            trig_range_high (int): upper limit of the trigger range
        """
        c_trig_range_low = ctypes.c_int()
        c_trig_range_high = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOM_GetTriggerRange(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_trig_range_low),
                                                         ctypes.byref(c_trig_range_high))
        self.check_error(error_code, "SEPIA2_SOM_GetTriggerRange")

        return c_trig_range_low.value, c_trig_range_high.value

    @handle_errors
    def som_get_trigger_level(self, device_id: int, slot_id: int) -> int:
        """This function gets the current value of the trigger level specified in mV.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            trig_level (int): actual value of the trigger level
        """
        c_trig_level = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOM_GetTriggerLevel(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_trig_level))
        self.check_error(error_code, "SEPIA2_SOM_GetTriggerLevel")

        return c_trig_level.value

    @handle_errors
    def som_set_trigger_level(self, device_id: int, slot_id: int, trig_level: int) -> None:
        """This function sets the new value of the trigger level specified in mV. To learn about the
        individual valid range for the trigger level, call `som_get_trigger_range`.
        
        Notice: Since the scale of the trigger level has its individual step width, the value you
        specified will be rounded off to the nearest valid value. It is recommended to call the
        `som_get_trigger_level` function to check the "level in fact".

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            trig_level (int): trigger level
        """
        error_code = self.dll.SEPIA2_SOM_SetTriggerLevel(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(trig_level))
        self.check_error(error_code, "SEPIA2_SOM_SetTriggerLevel")

    @handle_errors
    def som_get_burst_values(self, device_id: int, slot_id: int) -> (int, int, int):
        """This function returns the current settings of the determining values for the timing of
        the pre scaler. Refer to the main manual chapter on SOM 828 modules to learn about these
        values.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            divider (int): current divider for the pre scaler
            pre_sync (int): current pre sync value
            mask_sync (int): current mask sync value
        """
        c_divider = ctypes.c_ubyte()
        c_pre_sync = ctypes.c_ubyte()
        c_mask_sync = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOM_GetBurstValues(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_divider),
                                                        ctypes.byref(c_pre_sync),
                                                        ctypes.byref(c_mask_sync))
        self.check_error(error_code, "SEPIA2_SOM_GetBurstValues")

        return c_divider.value, c_pre_sync.value, c_mask_sync.value

    @handle_errors
    def som_set_burst_values(self, device_id: int, slot_id: int, divider: int, pre_sync: int,
                         mask_sync: int) -> None:
        """This function sets the new determining values for the timing of the pre scaler.
        
        Refer to the main manual chapter on SOM 828 modules to learn about these values.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            divider (int): current divider for the pre scaler (1..255)
            pre_sync (int): current pre sync value (0..`divider`-1)
            mask_sync (int): current mask sync value (0..255)
        """
        error_code = self.dll.SEPIA2_SOM_SetBurstValues(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_ubyte(divider),
                                                        ctypes.c_ubyte(pre_sync),
                                                        ctypes.c_ubyte(mask_sync))
        self.check_error(error_code, "SEPIA2_SOM_SetBurstValues")

    @handle_errors
    def som_get_burst_length_array(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int):
        """This function gets the current values for the respective burst length of the eight output
        channels.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            burst_lengths (tuple, 8x int): each channels current burst length
        """
        c_burst_lengths = [ctypes.c_long() for i in range(8)]

        error_code = self.dll.SEPIA2_SOM_GetBurstLengthArray(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             *[ctypes.byref(bl)
                                                               for bl in c_burst_lengths])
        self.check_error(error_code, "SEPIA2_SOM_GetBurstLengthArray")

        return tuple(bl.value for bl in c_burst_lengths)

    @handle_errors
    def som_set_burst_length_array(self, device_id: int, slot_id: int,
                                   burst_lengths: typing.Sequence[int]) -> None:
        """This function sets the new values for the respective burst length of the eight output
        channels.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            burst_lengths (tuple, 8x int): each channels current burst length (0..16777215)

        Raises:
            ValueError: If len(`burst_lengths`) != 8
        """
        if (array_len := len(burst_lengths)) != 8:
            raise ValueError(f"Invalid array size ({array_len}). Expected 8 channels.")

        error_code = self.dll.SEPIA2_SOM_SetBurstLengthArray(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             *[ctypes.c_long(bl)
                                                               for bl in burst_lengths])
        self.check_error(error_code, "SEPIA2_SOM_SetBurstLengthArray")

    @handle_errors
    def som_get_out_n_sync_enable(self, device_id: int, slot_id: int) \
            -> (typing.Tuple[bool, bool, bool, bool, bool, bool, bool, bool],
                typing.Tuple[bool, bool, bool, bool, bool, bool, bool, bool], bool):
        """This function gets the current values of the output control and sync signal composing.
        
        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            out_enable (tuple, 8x bool): output channel enable mask
            sync_enable (tuple, 8x bool): sync channel enable mask
            sync_inverse (bool): sync function inverse
        """
        c_out_enable = ctypes.c_ubyte()
        c_sync_enable = ctypes.c_ubyte()
        c_sync_inverse = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOM_GetOutNSyncEnable(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.byref(c_out_enable),
                                                           ctypes.byref(c_sync_enable),
                                                           ctypes.byref(c_sync_inverse))
        self.check_error(error_code, "SEPIA2_SOM_GetOutNSyncEnable")

        out_enable = tuple(bool(int(b)) for b in f"{c_out_enable.value:08b}")
        sync_enable = tuple(bool(int(b)) for b in f"{c_sync_enable.value:08b}")

        return out_enable, sync_enable, bool(c_sync_inverse.value)

    @handle_errors
    def som_set_out_n_sync_enable(self, device_id: int, slot_id: int,
                                  out_enable_list: typing.Sequence[bool],
                                  sync_enable_list: typing.Sequence[bool], 
                                  sync_inverse: bool) -> None:
        """This function sets the new values for the output control and sync signal composing.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            out_enable (tuple, 8x bool): output channel enable mask
            sync_enable (tuple, 8x bool): sync channel enable mask
            sync_inverse (bool): sync function inverse

        Raises:
            ValueError: If len(`out_enable_list`) or len (`sync_enable_list`) != 8
        """
        if (array_len := len(out_enable_list)) != 8:
            raise ValueError(f"Invalid array size ({array_len}) of out_enable_list. Expected 8 " +
                             "channels.")
        if (array_len := len(sync_enable_list)) != 8:
            raise ValueError(f"Invalid array size ({array_len}) of sync_enable_list. Expected 8 " +
                             "channels.")

        out_enable = int("".join("1" if b else "0" for b in out_enable_list), 2)
        sync_enable = int("".join("1" if b else "0" for b in sync_enable_list), 2)

        error_code = self.dll.SEPIA2_SOM_SetOutNSyncEnable(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.c_ubyte(out_enable),
                                                           ctypes.c_ubyte(sync_enable),
                                                           ctypes.c_ubyte(sync_inverse))
        self.check_error(error_code, "SEPIA2_SOM_SetOutNSyncEnable")

    @handle_errors
    def som_decode_aux_in_sequencer_ctrl(self, aux_in_ctrl: int) -> str:
        """This function works "off line", without a PQ Laser Device running, too. It decodes the
        sequencer control code returned by the SOM function `som_get_aux_io_sequencer_ctrl` and
        returns the appropriate sequencer control string (ASCII-readable).

        Args:
            aux_in_ctrl (int): sequencer control, integer, taking the value as returned by the SOM
                function `som_get_aux_io_sequencer_ctrl`

        Returns:
            str: sequencer control string
        """
        c_sequencer_ctrl = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_SOM_DecodeAUXINSequencerCtrl(ctypes.c_int(aux_in_ctrl),
                                                                  ctypes.byref(c_sequencer_ctrl))
        self.check_error(error_code, "SEPIA2_SOM_DecodeAUXINSequencerCtrl")

        return c_sequencer_ctrl.value.decode(self.str_encoding)

    @handle_errors
    def som_get_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int) -> (bool, int):
        """This function gets the current control values for AUX OUT and AUX IN.
        The byte pointed at by `aux_out_ctrl` stands for a boolean "sequence index pulse enabled
        on AUX Out". The value of the byte pointed at by `aux_out_ctrl` stands for the current
        running/restart mode of the sequencer. The user can decode this value to a human readable
        string using the `som_decode_aux_in_sequencer_ctrl` function. 
        
        The SOM 828 sequencer knows three modes:
            0: free running,
            1: running / restarting, if AUX IN is on logical High level,
            2: running / restarting, if AUX IN is on logical Low level.
        Additionally, the SOM 828-D knows a fourth mode:
            3: disabled / restarting on neither level at AUX IN.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module

        Returns:
            aux_out_ctrl: true, if sequence index pulse enabled on AUX OUT
            aux_in_ctrl: current restarting condition of the sequencer
        """
        c_aux_out_ctrl = ctypes.c_ubyte()
        c_aux_in_ctrl = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOM_GetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                               ctypes.c_int(slot_id),
                                                               ctypes.byref(c_aux_out_ctrl),
                                                               ctypes.byref(c_aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOM_GetAUXIOSequencerCtrl")

        return bool(c_aux_out_ctrl.value), c_aux_in_ctrl.value

    @handle_errors
    def som_set_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int, aux_out_ctrl: bool,
                                      aux_in_ctrl: int) -> None:
        """This function sets the current control values for AUX OUT and AUX IN.
        The byte given by `aux_out_ctrl` stands for a boolean "sequence index pulse enabled on AUX
        Out". The value of the byte `aux_in_ctrl` stands for the intended running/restart mode of
        the sequencer. The user can decode this value to a human readable string using the
        `som_decode_aux_in_sequencer_ctrl` function. Refer to the sequencer modes as described at
        SOM function `som_get_aux_io_sequencer_ctrl`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOM module
            aux_out_ctrl (bool): true, if sequence index pulse enabled on AUX OUT
            aux_in_ctrl (int): current restarting condition of the sequencer
        """
        error_code = self.dll.SEPIA2_SOM_SetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                               ctypes.c_int(slot_id),
                                                               ctypes.c_ubyte(aux_out_ctrl),
                                                               ctypes.c_ubyte(aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOM_SetAUXIOSequencerCtrl")

    @handle_errors
    def somd_decode_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> str:
        """Returns the frequency resp. trigger mode string at list position `freq_trig_mode` for a
        given SOMD module. This function only works "on line", with a PQ Laser Device running,
        because each SOMD may carry its individual list of reference sources. Only the list
        positions 0 and 1 are identical for all SOMD modules: They always carry the external trigger
        option on respectively raising and falling edges. To get the whole table, loop over the list
        position index starting with 0 until the function terminates with an error.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            freq_trig_mode (int): index into the list of reference sources (0..4)

        Returns:
            freq_trig_mode_str (str): frequency resp. trigger mode string
        """
        c_freq_trig_mode_str = ctypes.create_string_buffer(32)

        error_code = self.dll.SEPIA2_SOMD_DecodeFreqTrigMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq_trig_mode),
                                                            ctypes.byref(c_freq_trig_mode_str))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeFreqTrigMode")

        return c_freq_trig_mode_str.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_freq_trig_mode(self, device_id: int, slot_id: int) -> (int, bool):
        """This function inquires the current setting for the reference source in a given SOMD. In
        the integer variable, pointed to by `freq_trig_mode` it returns an index into the list of
        possible sources.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            freq_trig_mode (int): index into the list of reference sources
        """
        c_freq_trig_mode = ctypes.c_int()
        c_synchronize = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetFreqTrigMode(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_freq_trig_mode),
                                                          ctypes.byref(c_synchronize))
        self.check_error(error_code, "SEPIA2_SOMD_GetFreqTrigMode")

        return c_freq_trig_mode.value, bool(c_synchronize)

    @handle_errors
    def somd_set_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int,
                                synchronize: bool) -> None:
        """This function sets the new reference source for a given SOMD. It is passed over as a new
        value for the index into the list of possible sources.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            freq_trig_mode (int): index into the list of reference sources
        """
        error_code = self.dll.SEPIA2_SOMD_SetFreqTrigMode(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(freq_trig_mode),
                                                          ctypes.c_ubyte(synchronize))
        self.check_error(error_code, "SEPIA2_SOMD_SetFreqTrigMode")

    @handle_errors
    def somd_get_trigger_range(self, device_id: int, slot_id: int) -> (int, int):
        """This function gets the adjustable range of the trigger level. The limits are specified in
        mV.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            trig_range_low (int): lower limit of the trigger range
            trig_range_high (int): upper limit of the trigger range
        """
        c_trig_range_low = ctypes.c_int()
        c_trig_range_high = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOMD_GetTriggerRange(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_trig_range_low),
                                                          ctypes.byref(c_trig_range_high))
        self.check_error(error_code, "SEPIA2_SOMD_GetTriggerRange")

        return c_trig_range_low.value, c_trig_range_high.value

    @handle_errors
    def somd_get_trigger_level(self, device_id: int, slot_id: int) -> int:
        """This function gets the current value of the trigger level specified in mV.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            trig_level (int): actual value of the trigger level
        """
        c_trig_level = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOMD_GetTriggerLevel(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_trig_level))
        self.check_error(error_code, "SEPIA2_SOMD_GetTriggerLevel")

        return c_trig_level.value

    @handle_errors
    def somd_set_trigger_level(self, device_id: int, slot_id: int, trig_level: int) -> None:
        """This function sets the new value of the trigger level specified in mV. To learn about the
        individual valid range for the trigger level, call `somd_get_trigger_range`.
        
        Notice: Since the scale of the trigger level has its individual step width, the value you
        specified will be rounded off to the nearest valid value. It is recommended to call the
        `somd_get_trigger_level` function to check the "level in fact".

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            trig_level (int): trigger level
        """
        error_code = self.dll.SEPIA2_SOMD_SetTriggerLevel(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(trig_level))
        self.check_error(error_code, "SEPIA2_SOMD_SetTriggerLevel")

    @handle_errors
    def somd_get_burst_values(self, device_id: int, slot_id: int) -> (int, int, int):
        """This function returns the current settings of the determining values for the timing of
        the pre scaler. Refer to the main manual chapter on SOM 828-D modules to learn about these
        values.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            divider (int): current divider for the pre scaler
            pre_sync (int): current pre sync value
            mask_sync (int): current mask sync value
        """
        c_divider = ctypes.c_ushort()
        c_pre_sync = ctypes.c_ubyte()
        c_sync_mask = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetBurstValues(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_divider),
                                                         ctypes.byref(c_pre_sync),
                                                         ctypes.byref(c_sync_mask))
        self.check_error(error_code, "SEPIA2_SOMD_GetBurstValues")

        return c_divider.value, c_pre_sync.value, c_sync_mask.value

    @handle_errors
    def somd_set_burst_values(self, device_id: int, slot_id: int, divider: int,
                         pre_sync: int, sync_mask: int) -> None:
        """This function sets the new determining values for the timing of the pre scaler.
        
        Refer to the main manual chapter on SOM 828-D modules to learn about these values.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            divider (int): current divider for the pre scaler (1..255)
            pre_sync (int): current pre sync value (0..`divider`-1)
            mask_sync (int): current mask sync value (0..255)
        """
        error_code = self.dll.SEPIA2_SOMD_SetBurstValues(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_ushort(divider),
                                                         ctypes.c_ubyte(pre_sync),
                                                         ctypes.c_ubyte(sync_mask))
        self.check_error(error_code, "SEPIA2_SOMD_SetBurstValues")

    @handle_errors
    def somd_get_burst_length_array(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int):
        """This function gets the current values for the respective burst length of the eight output
        channels.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            burst_lengths (tuple, 8x int): each channels current burst length
        """
        c_burst_lengths = [ctypes.c_long() for i in range(8)]

        error_code = self.dll.SEPIA2_SOMD_GetBurstLengthArray(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              *[ctypes.byref(bl)
                                                                for bl in c_burst_lengths])
        self.check_error(error_code, "SEPIA2_SOMD_GetBurstLengthArray")

        return tuple(bl.value for bl in c_burst_lengths)

    @handle_errors
    def somd_set_burst_length_array(self, device_id: int, slot_id: int,
                               burst_lengths: typing.Sequence[int]) -> None:
        """This function sets the new values for the respective burst length of the eight output
        channels.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            burst_lengths (tuple, 8x int): each channels current burst length (0..16777215)

        Raises:
            ValueError: If len(`burst_lengths`) != 8
        """
        if (array_len := len(burst_lengths)) != 8:
            raise ValueError(f"Invalid array size ({array_len}). Expected 8 channels.")

        error_code = self.dll.SEPIA2_SOMD_SetBurstLengthArray(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              *[ctypes.c_long(bl)
                                                                for bl in burst_lengths])
        self.check_error(error_code, "SEPIA2_SOMD_SetBurstLengthArray")

    @handle_errors
    def somd_get_out_n_sync_enable(self, device_id: int, slot_id: int) \
            -> (typing.Tuple[bool, bool, bool, bool, bool, bool, bool, bool],
                typing.Tuple[bool, bool, bool, bool, bool, bool, bool, bool], bool):
        """This function gets the current values of the output control and sync signal composing.
        
        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            out_enable (tuple, 8x bool): output channel enable mask
            sync_enable (tuple, 8x bool): sync channel enable mask
            sync_inverse (bool): sync function inverse
        """
        c_out_enable = ctypes.c_ubyte()
        c_sync_enable = ctypes.c_ubyte()
        c_sync_inverse = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetOutNSyncEnable(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_out_enable),
                                                            ctypes.byref(c_sync_enable),
                                                            ctypes.byref(c_sync_inverse))
        self.check_error(error_code, "SEPIA2_SOMD_GetOutNSyncEnable")

        out_enable = tuple(bool(int(b)) for b in f"{c_out_enable.value:08b}")
        sync_enable = tuple(bool(int(b)) for b in f"{c_sync_enable.value:08b}")

        return out_enable, sync_enable, bool(c_sync_inverse.value)

    @handle_errors
    def somd_set_out_n_sync_enable(self, device_id: int, slot_id: int,
                                   out_enable_list: typing.Sequence[bool],
                                   sync_enable_list: typing.Sequence[bool], 
                                   sync_inverse: bool) -> None:
        """This function sets the new values for the output control and sync signal composing.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            out_enable (tuple, 8x bool): output channel enable mask
            sync_enable (tuple, 8x bool): sync channel enable mask
            sync_inverse (bool): sync function inverse

        Raises:
            ValueError: If len(`out_enable_list`) or len (`sync_enable_list`) != 8
        """
        if (array_len := len(out_enable_list)) != 8:
            raise ValueError(f"Invalid array size ({array_len}) of out_enable_list. Expected 8 " +
                             "channels.")
        if (array_len := len(sync_enable_list)) != 8:
            raise ValueError(f"Invalid array size ({array_len}) of sync_enable_list. Expected 8 " +
                             "channels.")

        out_enable = int("".join("1" if b else "0" for b in out_enable_list), 2)
        sync_enable = int("".join("1" if b else "0" for b in sync_enable_list), 2)

        error_code = self.dll.SEPIA2_SOMD_SetOutNSyncEnable(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_ubyte(out_enable),
                                                            ctypes.c_ubyte(sync_enable),
                                                            ctypes.c_ubyte(sync_inverse))
        self.check_error(error_code, "SEPIA2_SOMD_SetOutNSyncEnable")

    @handle_errors
    def somd_decode_aux_in_sequencer_ctrl(self, aux_in_ctrl: int) -> str:
        """This function works "off line", without a PQ Laser Device running, too. It decodes the
        sequencer control code returned by the SOMD function `somd_get_aux_io_sequencer_ctrl` and
        returns the appropriate sequencer control string (ASCII-readable).

        Args:
            aux_in_ctrl (int): sequencer control, integer, taking the value as returned by the SOMD
                function `somd_get_aux_io_sequencer_ctrl`

        Returns:
            str: sequencer control string
        """
        c_sequencer_ctrl = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_SOMD_DecodeAUXINSequencerCtrl(ctypes.c_int(aux_in_ctrl),
                                                                   ctypes.byref(c_sequencer_ctrl))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeAUXINSequencerCtrl")

        return c_sequencer_ctrl.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int) -> (bool, int):
        """This function gets the current control values for AUX OUT and AUX IN.
        The byte pointed at by `aux_out_ctrl` stands for a boolean "sequence index pulse enabled
        on AUX Out". The value of the byte pointed at by `aux_out_ctrl` stands for the current
        running/restart mode of the sequencer. The user can decode this value to a human readable
        string using the `som_decode_aux_in_sequencer_ctrl` function. 
        
        The SOM 828 sequencer knows three modes:
            0: free running,
            1: running / restarting, if AUX IN is on logical High level,
            2: running / restarting, if AUX IN is on logical Low level.
        Additionally, the SOM 828-D knows a fourth mode:
            3: disabled / restarting on neither level at AUX IN.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            aux_out_ctrl: true, if sequence index pulse enabled on AUX OUT
            aux_in_ctrl: current restarting condition of the sequencer
        """
        c_aux_out_ctrl = ctypes.c_ubyte()
        c_aux_in_ctrl = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                                ctypes.c_int(slot_id),
                                                                ctypes.byref(c_aux_out_ctrl),
                                                                ctypes.byref(c_aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOMD_GetAUXIOSequencerCtrl")

        return bool(c_aux_out_ctrl.value), c_aux_in_ctrl.value

    @handle_errors
    def somd_set_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int, aux_out_ctrl: bool,
                                  aux_in_ctrl: int) -> None:
        """This function sets the current control values for AUX OUT and AUX IN.
        The byte given by `aux_out_ctrl` stands for a boolean "sequence index pulse enabled on AUX
        Out". The value of the byte `aux_in_ctrl` stands for the intended running/restart mode of
        the sequencer. The user can decode this value to a human readable string using the
        `som_decode_aux_in_sequencer_ctrl` function. Refer to the sequencer modes as described at
        SOMD function `somd_get_aux_io_sequencer_ctrl`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            aux_out_ctrl (bool): true, if sequence index pulse enabled on AUX OUT
            aux_in_ctrl (int): current restarting condition of the sequencer
        """
        error_code = self.dll.SEPIA2_SOMD_SetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                                ctypes.c_int(slot_id),
                                                                ctypes.c_ubyte(aux_out_ctrl),
                                                                ctypes.c_ubyte(aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOMD_SetAUXIOSequencerCtrl")

    @handle_errors
    def somd_decode_module_state(self, state: int) -> str:
        """Decodes the module state to a string.

        Args:
            state (int): module state (0..65535)

        Returns:
            status_text (str): module status string
        """
        c_status_text = ctypes.create_string_buffer(511)

        error_code = self.dll.SEPIA2_SOMD_DecodeModuleState(ctypes.c_ushort(state),
                                                            ctypes.byref(c_status_text))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeModuleState")

        return c_status_text.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_status_error(self, device_id: int, slot_id: int) -> (PicoquantSepia2SOMDState, int):
        """The state is bit coded and can be decoded by the SOMD function
        `somd_decode_module_state`. If the error state HARDWARE_ERROR (0x10) is set, the
        `error_code` is transmitted as well, else this variable is zero. As a side effect, error
        state and error code are cleared, if there are no further errors pending. Decode the error
        codes received with the LIB function `lib_decode_error`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            state (PicoquantSepia2SOMDState): state of the SOMD module
            error_code (int): error code
        """
        c_state = ctypes.c_ushort()
        c_error_code = ctypes.c_short()

        error_code = self.dll.SEPIA2_SOMD_GetStatusError(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_state),
                                                         ctypes.byref(c_error_code))
        self.check_error(error_code, "SEPIA2_SOMD_GetStatusError")

        return PicoquantSepia2SOMDState(c_state.value), c_error_code.value

    @handle_errors
    def somd_get_hw_params(self, device_id: int, slot_id: int) \
            -> ((int, int, int), (int, int, int, int), int):
        """This function returns the current results of some temperature and voltage measurements
        inside the SOMD module. These values are used to rate the working conditions and judge the
        stability of the module. The function is needed for documentation of the module's current
        working conditions in case of a support request, beside this, it is solely informative.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            temperatures (tuple, 3x int): temperatures at measuring point 1-3
            voltages (tuple, 4x int): voltages at measuring point 1-4
            aux (int): result of an auxiliary measurement
        """
        c_temperatures = [ctypes.c_ushort() for i in range(3)]
        c_voltages = [ctypes.c_ushort() for i in range(4)]
        c_aux = ctypes.c_ushort()

        error_code = self.dll.SEPIA2_SOMD_GetHWParams(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      *[ctypes.byref(t) for t in c_temperatures],
                                                      *[ctypes.byref(v) for v in c_voltages],
                                                      ctypes.byref(c_aux))
        self.check_error(error_code, "SEPIA2_SOMD_GetHWParams")

        return tuple(t.value for t in c_temperatures), tuple(v.value for v in c_voltages), \
            c_aux.value

    @handle_errors
    def somd_get_fw_version(self, device_id: int, slot_id: int) -> (int, int, int):
        """Gets the modules firmware version

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            fw_version (tuple, 3x int): major, minor, build
        """
        c_fw_version = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SOMD_GetFWVersion(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_SOMD_GetFWVersion")

        fw_version_bytes = c_fw_version.value.to_bytes(4)

        # major, minor, build
        return fw_version_bytes[0], fw_version_bytes[1], int.from_bytes(fw_version_bytes[2:])

    @handle_errors
    def somd_synchronize_now(self, device_id: int, slot_id: int) -> None:
        """If the triggering is set to one of the external modes using the function
        `somd_set_freq_trig_mode`, this function is used to synchronize to the external triggering
        signal. Once this function succeeded, it is allowed to apply delay info to the bursts at the
        sequencer outputs. Call `somd_get_status_error` to check the state afterwards!
        Get information on the synchronized-to signal calling `somd_get_trig_sync_freq`.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
        """
        error_code = self.dll.SEPIA2_SOMD_SynchronizeNow(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id))
        self.check_error(error_code, "SEPIA2_SOMD_SynchronizeNow")

    @handle_errors
    def somd_get_trig_sync_freq(self, device_id: int, slot_id: int) -> (bool, int):
        """If synchronized, call this function to get information on the triggering signal.
        `freq_stable` stays true, as long as the signal stays within the tolerance window of ±100
        ppm.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            freq_stable (bool): true, if the synchronized-to frequency is still stable (within a
                tolerance window of ±100 ppm).
            trig_sync_freq (int): triggering frequency in Hz
        """
        c_freq_stable = ctypes.c_ubyte()
        c_trig_sync_freq = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SOMD_GetTrigSyncFreq(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_freq_stable),
                                                          ctypes.byref(c_trig_sync_freq))
        self.check_error(error_code, "SEPIA2_SOMD_GetTrigSyncFreq")

        return bool(c_freq_stable.value), c_trig_sync_freq.value

    @handle_errors
    def somd_get_delay_units(self, device_id: int, slot_id: int) -> (float, int):
        """This function should always be called, after the base oscillator values (source, divider,
        synchronized frequency, etc.) had changed. It returns the coarse delay stepwidth in seconds
        and the currently possible amount of fine steps to apply. The coarse delay stepwidth is
        mainly varying with the main clock, depending on the trigger source (base oscillator or
        external signal) and the pre-division factor. Usually the stepwidth will be about 650 to 950
        psec; the value is given in seconds. Since this value is varying on all changes to the main
        clock, the amount of steps to meet a desired delay length has to be recalculated then. The
        same goes for the amount of fine steps. A fine step has a module depending, individually
        varying steplength of typically 15 to 35 psec.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module

        Returns:
            coarse_delay_step (float): width of a coarse delay step, in sec
            fine_delay_steps (int): fine delay maximum step count
        """
        c_coarse_delay_step = ctypes.c_double()
        c_fine_delay_steps = ctypes.c_byte()

        error_code = self.dll.SEPIA2_SOMD_GetDelayUnits(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_coarse_delay_step),
                                                        ctypes.byref(c_fine_delay_steps))
        self.check_error(error_code, "SEPIA2_SOMD_GetDelayUnits")

        return c_coarse_delay_step.value, c_fine_delay_steps.value

    @handle_errors
    def somd_get_seq_output_infos(self, device_id: int, slot_id: int, seq_output_id: int) \
            -> (bool, bool, int, bool, float, int):
        """This function returns all information necessary to describe the state of the sequencer
        output identified by `seq_output_id`. Note, that it returns apparently redundant
        information: If e.g. `delayded` is true, the information on output combinations seems sort
        of useless, since burst combinations aren't allowed on delayed signals. On the other hand,
        there is no virtue in reading delay data, if `delayded` is false or `force_undelayed` is
        true. But then again, consider, this function was designed for complex GUI purposes. It
        offers all the alternately hidden, but still effective information, to enable a GUI to
        seamlessly switch back and forth between the different states.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            seq_output_id (int): sequencer output index (0..7)

        Returns:
            delayed (bool): delayed
            forced_undelayed (bool): forced being undelayed
            out_combi (int): output channel combination mask, bitcoded (1..255)
            masked_combi (bool): masked combi
            coarse_delay (float): coarse delay in ns
            fine_delay (int): fine delay steps in a.u. (0..63)
        """
        c_delayed = ctypes.c_ubyte()
        c_forced_undelayed = ctypes.c_ubyte()
        c_out_combi = ctypes.c_ubyte()
        c_masked_combi = ctypes.c_ubyte()
        c_coarse_delay = ctypes.c_double()
        c_fine_delay = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetSeqOutputInfos(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_ubyte(seq_output_id),
                                                            ctypes.byref(c_delayed),
                                                            ctypes.byref(c_forced_undelayed),
                                                            ctypes.byref(c_out_combi),
                                                            ctypes.byref(c_masked_combi),
                                                            ctypes.byref(c_coarse_delay),
                                                            ctypes.byref(c_fine_delay))
        self.check_error(error_code, "SEPIA2_SOMD_GetSeqOutputInfos")

        return bool(c_delayed.value), bool(c_forced_undelayed.value), c_out_combi.value, \
            bool(c_masked_combi.value), c_coarse_delay.value, c_fine_delay.value

    @handle_errors
    def somd_set_seq_output_infos(self, device_id: int, slot_id: int, seq_output_id: int,
                                  delayed: bool, out_combi: int, masked_combi: bool,
                                  coarse_delay: float, fine_delay: int) -> None:
        """This function sets all information necessary to describe the state of the sequencer
        output identified by `seq_output_id`. Note, that it transmits apparently redundant
        information: If e.g. `delayed` is true, the information on output combinations seems sort of
        useless, since burst combinations aren't allowed on delayed signals. On the other hand,
        there is no virtue in setting delay data, if `delayed` is false. But then again, consider,
        this function was designed for complex GUI purposes. It sends all the alternately hidden,
        but still effective information, to enable a GUI to seamlessly switch back and forth between
        the different states.
        
        Note: `out_combi` must not equal 0. (At least one channel has to be assigned to the output.)
        
        Note, that the currently legal values for `fine_delay` are module state dependent and have
        to be queried using the SOMD function GetDelayUnits.

        Args:
            device_id (int): PQ Laser Device index (USB channel number, 0..7)
            slot_id (int): slot number of SOMD module
            seq_output_id (int): sequencer output index (0..7)
            delayed (bool): delayed
            out_combi (int): output channel combination mask, bitcoded (1..255)
            masked_combi (bool): masked combi
            coarse_delay (float): coarse delay in ns
            fine_delay (int): fine delay steps in a.u. (0..63)
        """
        error_code = self.dll.SEPIA2_SOMD_SetSeqOutputInfos(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_ubyte(seq_output_id),
                                                            ctypes.c_ubyte(delayed),
                                                            ctypes.c_ubyte(out_combi),
                                                            ctypes.c_ubyte(masked_combi),
                                                            ctypes.c_double(coarse_delay),
                                                            ctypes.c_ubyte(fine_delay))
        self.check_error(error_code, "SEPIA2_SOMD_SetSeqOutputInfos")

    @handle_errors
    def slm_decode_freq_trig_mode(self, freq: int) -> str:
        c_freq_trig_mode = ctypes.create_string_buffer(28)

        error_code = self.dll.SEPIA2_SLM_DecodeFreqTrigMode(ctypes.c_int(freq),
                                                            ctypes.byref(c_freq_trig_mode))
        self.check_error(error_code, "SEPIA2_SLM_DecodeFreqTrigMode")

        return c_freq_trig_mode.value.decode(self.str_encoding)

    @handle_errors
    def slm_decode_head_type(self, head_type: int) -> str:
        c_head_type_str = ctypes.create_string_buffer(18)

        error_code = self.dll.SEPIA2_SLM_DecodeHeadType(ctypes.c_int(head_type),
                                                        ctypes.byref(c_head_type_str))
        self.check_error(error_code, "SEPIA2_SLM_DecodeHeadType")

        return c_head_type_str.value.decode(self.str_encoding)

    @handle_errors
    def slm_get_parameters(self, device_id: int, slot_id: int) -> (int, bool, int, float):
        c_freq = ctypes.c_int()
        c_pulse_mode = ctypes.c_ubyte()
        c_head_type = ctypes.c_int()
        c_intensity = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SLM_GetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_freq),
                                                       ctypes.byref(c_pulse_mode),
                                                       ctypes.byref(c_head_type),
                                                       ctypes.byref(c_intensity))
        self.check_error(error_code, "SEPIA2_SLM_GetParameters")

        return c_freq.value, bool(c_pulse_mode.value), c_head_type.value, \
            c_intensity.value / 100

    @handle_errors
    def slm_set_parameters(self, device_id: int, slot_id: int, freq: int, pulse_mode: bool,
                           intensity: float) -> None:
        error_code = self.dll.SEPIA2_SLM_SetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_int(freq),
                                                       ctypes.c_ubyte(pulse_mode),
                                                       ctypes.c_ubyte(round(intensity * 100)))
        self.check_error(error_code, "SEPIA2_SLM_SetParameters")

    @handle_errors
    def slm_get_intensity_fine_step(self, device_id: int, slot_id: int) -> float:
        c_intensity = ctypes.c_ushort()

        error_code = self.dll.SEPIA2_SLM_GetIntensityFineStep(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              ctypes.byref(c_intensity))
        self.check_error(error_code, "SEPIA2_SLM_GetIntensityFineStep")

        return c_intensity.value / 1000


    @handle_errors
    def slm_set_intensity_fine_step(self, device_id: int, slot_id: int, intensity: float) -> None:
        error_code = self.dll.SEPIA2_SLM_SetIntensityFineStep(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              ctypes.c_ushort(round(intensity * 1000)))
        self.check_error(error_code, "SEPIA2_SLM_SetIntensityFineStep")

    @handle_errors
    def slm_get_pulse_parameters(self, device_id: int, slot_id: int) -> (int, bool, int):
        c_freq = ctypes.c_int()
        c_pulse_mode = ctypes.c_ubyte()
        c_head_type = ctypes.c_int()

        error_code = self.dll.SEPIA2_SLM_GetPulseParameters(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_freq),
                                                            ctypes.byref(c_pulse_mode),
                                                            ctypes.byref(c_head_type))
        self.check_error(error_code, "SEPIA2_SLM_GetPulseParameters")

        return c_freq.value, bool(c_pulse_mode.value), c_head_type.value

    @handle_errors
    def slm_set_pulse_parameters(self, device_id: int, slot_id: int, freq: int, pulse_mode: bool) -> None:
        error_code = self.dll.SEPIA2_SLM_SetPulseParameters(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq),
                                                            ctypes.c_ubyte(pulse_mode))
        self.check_error(error_code, "SEPIA2_SLM_SetPulseParameters")

    @handle_errors
    def sml_decode_head_type(self, head_type: int) -> str:
        c_head_type_str = ctypes.create_string_buffer(18)

        error_code = self.dll.SEPIA2_SML_DecodeHeadType(ctypes.c_int(head_type),
                                                        ctypes.byref(c_head_type_str))
        self.check_error(error_code, "SEPIA2_SML_DecodeHeadType")

        return c_head_type_str.value.decode(self.str_encoding)

    @handle_errors
    def sml_get_parameters(self, device_id: int, slot_id: int) -> (bool, int, float):
        c_pulse_mode = ctypes.c_ubyte()
        c_head_type = ctypes.c_int()
        c_intensity = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SML_GetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_pulse_mode),
                                                       ctypes.byref(c_head_type),
                                                       ctypes.byref(c_intensity))
        self.check_error(error_code, "SEPIA2_SML_GetParameters")

        return bool(c_pulse_mode.value), c_head_type.value, c_intensity.value / 100

    @handle_errors
    def sml_set_parameters(self, device_id: int, slot_id: int, pulse_mode: bool, intensity: float) -> None:
        error_code = self.dll.SEPIA2_SML_SetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_ubyte(pulse_mode),
                                                       ctypes.c_ubyte(round(intensity * 100)))
        self.check_error(error_code, "SEPIA2_SML_SetParameters")

    @handle_errors
    def swm_decode_range_idx(self, device_id: int, slot_id: int, time_base_id: int) -> int:
        c_upper_limit = ctypes.c_int()

        error_code = self.dll.SEPIA2_SWM_DecodeRangeIdx(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_int(time_base_id),
                                                        ctypes.byref(c_upper_limit))
        self.check_error(error_code, "SEPIA2_SWM_DecodeRangeIdx")

        return c_upper_limit.value

    @handle_errors
    def swm_get_ui_constants(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int):
        c_time_bases_count = ctypes.c_ubyte()
        c_max_amplitude = ctypes.c_ushort()
        c_max_slew_rate = ctypes.c_ushort()
        c_exp_ramp_factor = ctypes.c_ushort()
        c_min_user_val = ctypes.c_ushort()
        c_max_user_val = ctypes.c_ushort()
        c_user_resolution = ctypes.c_ushort()
        
        error_code = self.dll.SEPIA2_SWM_GetUIConstants(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_time_bases_count),
                                                        ctypes.byref(c_max_amplitude),
                                                        ctypes.byref(c_max_slew_rate),
                                                        ctypes.byref(c_exp_ramp_factor),
                                                        ctypes.byref(c_min_user_val),
                                                        ctypes.byref(c_max_user_val),
                                                        ctypes.byref(c_user_resolution))
        self.check_error(error_code, "SEPIA2_SWM_GetUIConstants")

        return c_time_bases_count.value, c_max_amplitude.value, c_max_slew_rate.value, \
            c_exp_ramp_factor.value, c_min_user_val.value, c_max_user_val.value, \
            c_user_resolution.value

    @handle_errors
    def swm_get_curve_params(self, device_id: int, slot_id: int, curve_id: int) \
            -> (int, int, int, int, int, int):
        c_time_base_id = ctypes.c_ubyte()
        c_pulse_amplitude = ctypes.c_ushort()
        c_ramp_slew_rate = ctypes.c_ushort()
        c_pulse_start_delay = ctypes.c_ushort()
        c_ramp_start_delay = ctypes.c_ushort()
        c_wave_stop_delay = ctypes.c_ushort()

        error_code = self.dll.SEPIA2_SWM_GetCurveParams(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_time_base_id),
                                                        ctypes.byref(c_pulse_amplitude),
                                                        ctypes.byref(c_ramp_slew_rate),
                                                        ctypes.byref(c_pulse_start_delay),
                                                        ctypes.byref(c_ramp_start_delay),
                                                        ctypes.byref(c_wave_stop_delay))
        self.check_error(error_code, "SEPIA2_SWM_GetCurveParams")

        return c_time_base_id.value, c_pulse_amplitude.value, c_ramp_slew_rate.value, \
            c_pulse_start_delay.value, c_ramp_start_delay.value, c_wave_stop_delay.value

    @handle_errors
    def swm_set_curve_params(self, device_id: int, slot_id: int, time_base_id: int,
                             pulse_amplitude: int, ramp_slew_rate: int, pulse_start_delay: int,
                             ramp_start_delay: int, wave_stop_delay: int) -> None:
        error_code = self.dll.SEPIA2_SWM_SetCurveParams(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_ubyte(time_base_id),
                                                        ctypes.c_ushort(pulse_amplitude),
                                                        ctypes.c_ushort(ramp_slew_rate),
                                                        ctypes.c_ushort(pulse_start_delay),
                                                        ctypes.c_ushort(ramp_start_delay),
                                                        ctypes.c_ushort(wave_stop_delay))
        self.check_error(error_code, "SEPIA2_SWM_SetCurveParams")

    @handle_errors
    def swm_get_cal_table_val(self, device_id: int, slot_id: int, table_name: str, table_row: int,
                              table_column: int) -> int:
        c_table_name = ctypes.create_string_buffer(table_name)
        c_value = ctypes.c_ushort()

        error_code = self.dll.SEPIA2_SWM_GetCalTableVal(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        c_table_name, ctypes.c_ubyte(table_row),
                                                        ctypes.c_ubyte(table_column),
                                                        ctypes.byref(c_value))
        self.check_error(error_code, "SEPIA2_SWM_GetCalTableVal")

        return c_value.value

    @handle_errors
    def swm_get_ext_attenuation(self, device_id: int, slot_id: int) -> float:
        c_ext_attenuation = ctypes.c_float()

        error_code = self.dll.SEPIA2_SWM_GetExtAtten(ctypes.c_int(device_id), ctypes.c_int(slot_id),
                                                     ctypes.byref(c_ext_attenuation))
        self.check_error(error_code, "SEPIA2_SWM_GetExtAtten")

        return c_ext_attenuation.value

    @handle_errors
    def swm_set_ext_attenuation(self, device_id: int, slot_id: int, ext_attenuation: float) -> None:
        error_code = self.dll.SEPIA2_SWM_SetExtAtten(ctypes.c_int(device_id), ctypes.c_int(slot_id),
                                                     ctypes.c_float(ext_attenuation))
        self.check_error(error_code, "SEPIA2_SWM_SetExtAtten")

    @handle_errors
    def vcl_get_ui_constants(self, device_id: int, slot_id: int) -> (int, int, int):
        c_min_temp = ctypes.c_int()
        c_max_temp = ctypes.c_int()
        c_temp_resolution = ctypes.c_int()

        error_code = self.dll.SEPIA2_VCL_GetUIConstants(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_min_temp),
                                                        ctypes.byref(c_max_temp),
                                                        ctypes.byref(c_temp_resolution))
        self.check_error(error_code, "SEPIA2_VCL_GetUIConstants")

        return c_min_temp.value, c_max_temp.value, c_temp_resolution.value

    @handle_errors
    def vcl_get_temperature(self, device_id: int, slot_id: int) -> int:
        c_temperature = ctypes.c_int()

        error_code = self.dll.SEPIA2_VCL_GetTemperature(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_temperature))
        self.check_error(error_code, "SEPIA2_VCL_GetTemperature")

        return c_temperature.value

    @handle_errors
    def vcl_set_temperature(self, device_id: int, slot_id: int, temperature: int) -> None:
        error_code = self.dll.SEPIA2_VCL_SetTemperature(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_int(temperature))
        self.check_error(error_code, "SEPIA2_VCL_SetTemperature")

    @handle_errors
    def vcl_get_bias_voltage(self, device_id: int, slot_id: int) -> int:
        c_bias_voltage = ctypes.c_int()

        error_code = self.dll.SEPIA2_VCL_GetBiasVoltage(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_bias_voltage))
        self.check_error(error_code, "SEPIA2_VCL_GetBiasVoltage")

        return c_bias_voltage.value

    @handle_errors
    def spm_decode_module_state(self, state: int) -> str:
        c_status_text = ctypes.create_string_buffer(79)

        error_code = self.dll.SEPIA2_SPM_DecodeModuleState(ctypes.c_ushort(state),
                                                           ctypes.byref(c_status_text))
        self.check_error(error_code, "SEPIA2_SPM_DecodeModuleState")

        return c_status_text.value.decode(self.str_encoding)

    @handle_errors
    def spm_get_fw_version(self, device_id: int, slot_id: int) -> (int, int, int):
        c_fw_version = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SPM_GetFWVersion(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_SPM_GetFWVersion")

        fw_version_bytes = c_fw_version.value.to_bytes(4)

        # major, minor, build
        return fw_version_bytes[0], fw_version_bytes[1], int.from_bytes(fw_version_bytes[2:])

    @handle_errors
    def spm_get_sensor_data(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int, int):
        c_sensor_data_array = (ctypes.c_ushort * 9)()

        error_code = self.dll.SEPIA2_SPM_GetSensorData(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_sensor_data_array))
        self.check_error(error_code, "SEPIA2_SPM_GetSensorData")

        # temperatures (6x), overall current, optional sensor 1, optional sensor 2
        return tuple(c_sensor_data_array)

    @handle_errors
    def spm_get_temperature_adjust(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int):
        c_temperature_array = (ctypes.c_ushort * 6)()

        error_code = self.dll.SEPIA2_SPM_GetTemperatureAdjust(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              ctypes.byref(c_temperature_array))
        self.check_error(error_code, "SEPIA2_SPM_GetTemperatureAdjust")

        return tuple(c_temperature_array)

    @handle_errors
    def spm_get_status_error(self, device_id: int, slot_id: int) -> (PicoquantSepia2SPMStates, int):
        c_state = ctypes.c_ushort()
        c_error_code = ctypes.c_short()

        error_code = self.dll.SEPIA2_SPM_GetStatusError(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_state),
                                                        ctypes.byref(c_error_code))
        self.check_error(error_code, "SEPIA2_SPM_GetStatusError")

        return PicoquantSepia2SPMStates(c_state.value), c_error_code

    @handle_errors
    def spm_update_firmware(self, device_id: int, slot_id: int, fwr_filename: str) -> None:
        c_fwr_filename = ctypes.create_string_buffer(fwr_filename)

        error_code = self.dll.SEPIA2_SPM_UpdateFirmware(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        c_fwr_filename)
        self.check_error(error_code, "SEPIA2_SPM_UpdateFirmware")

    @handle_errors
    def spm_set_fram_write_protect(self, device_id: int, slot_id: int, write_protect: bool) -> None:
        error_code = self.dll.SEPIA2_SPM_SetFRAMWriteProtect(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             ctypes.c_ubyte(write_protect))
        self.check_error(error_code, "SEPIA2_SPM_SetFRAMWriteProtect")

    @handle_errors
    def spm_get_fiber_amplifier_fail(self, device_id: int, slot_id: int) -> bool:
        c_fiber_amp_fail = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SPM_GetFiberAmplifierFail(ctypes.c_int(device_id),
                                                               ctypes.c_int(slot_id),
                                                               ctypes.byref(c_fiber_amp_fail))
        self.check_error(error_code, "SEPIA2_SPM_GetFiberAmplifierFail")

        return bool(c_fiber_amp_fail.value)

    @handle_errors
    def spm_reset_fiber_amplifier_fail(self, device_id: int, slot_id: int, fiber_amp_fail: bool) \
            -> None:
        error_code = self.dll.SEPIA2_SPM_ResetFiberAmplifierFail(ctypes.c_int(device_id),
                                                                 ctypes.c_int(slot_id),
                                                                 ctypes.c_ubyte(fiber_amp_fail))
        self.check_error(error_code, "SEPIA2_SPM_ResetFiberAmplifierFail")

    @handle_errors
    def spm_get_pump_power_state(self, device_id: int, slot_id: int) -> (bool, bool):
        c_pump_state = ctypes.c_ubyte()
        c_pump_mode = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SPM_GetPumpPowerState(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.byref(c_pump_state),
                                                           ctypes.byref(c_pump_mode))
        self.check_error(error_code, "SEPIA2_SPM_GetPumpPowerState")

        return bool(c_pump_state.value), bool(c_pump_mode)

    @handle_errors
    def spm_set_pump_power_state(self, device_id: int, slot_id: int, pump_state: bool,
                                 pump_mode: bool) -> None:
        error_code = self.dll.SEPIA2_SPM_SetPumpPowerState(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.c_ubyte(pump_state),
                                                           ctypes.c_ubyte(pump_mode))
        self.check_error(error_code, "SEPIA2_SPM_SetPumpPowerState")

    @handle_errors
    def spm_get_operation_timers(self, device_id: int, slot_id: int) -> (int, int, int, int):
        c_main_power_switch = ctypes.c_ulong()
        c_uptime_overall = ctypes.c_ulong()
        c_uptime_delivery = ctypes.c_ulong()
        c_uptime_fiber_change = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SPM_GetOperationTimers(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_main_power_switch),
                                                            ctypes.byref(c_uptime_overall),
                                                            ctypes.byref(c_uptime_delivery),
                                                            ctypes.byref(c_uptime_fiber_change))
        self.check_error(error_code, "SEPIA2_SPM_GetOperationTimers")

    @handle_errors
    def sws_decode_module_type(self, module_type: int) -> str:
        c_module_type_str = ctypes.create_string_buffer(32)

        error_code = self.dll.SEPIA2_SWS_DecodeModuleType(ctypes.c_int(module_type),
                                                          ctypes.byref(c_module_type_str))
        self.check_error(error_code, "SEPIA2_SWS_DecodeModuleType")

        return c_module_type_str.value.decode(self.str_encoding)

    @handle_errors
    def sws_decode_module_state(self, state: int) -> str:
        c_state_str = ctypes.create_string_buffer(148)

        error_code = self.dll.SEPIA2_SWS_DecodeModuleState(ctypes.c_ushort(state),
                                                           ctypes.byref(c_state_str))
        self.check_error(error_code, "SEPIA2_SWS_DecodeModuleState")

        return c_state_str.value.decode(self.str_encoding)

    @handle_errors
    def sws_get_module_type(self, device_id: int, slot_id: int) -> int:
        c_module_type = ctypes.c_int()

        error_code = self.dll.SEPIA2_SWS_GetModuleType(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_module_type))
        self.check_error(error_code, "SEPIA2_SWS_GetModuleType")

        return c_module_type.value

    @handle_errors
    def sws_get_status_error(self, device_id: int, slot_id: int) -> (PicoquantSepia2SWSStates, int):
        c_state = ctypes.c_ushort()
        c_error_code = ctypes.c_int()

        error_code = self.dll.SEPIA2_SWS_GetStatusError(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_state),
                                                        ctypes.byref(c_error_code))
        self.check_error(error_code, "SEPIA2_SWS_GetStatusError")

        return PicoquantSepia2SWSStates(c_state.value), c_state.error_code

    @handle_errors
    def sws_get_param_ranges(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int, int, int):
        c_wavelen_upper = ctypes.c_ulong()
        c_wavelen_lower = ctypes.c_ulong()
        c_wavelen_stepwidth = ctypes.c_ulong()
        c_wavelen_power_mode_toggle = ctypes.c_ulong()
        c_bandwidth_upper = ctypes.c_ulong()
        c_bandwidth_lower = ctypes.c_ulong()
        c_backwidth_stepwidth = ctypes.c_ulong()
        c_beam_shifter_upper = ctypes.c_int()
        c_beam_shifter_lower = ctypes.c_int()
        c_beam_shifter_stepwidth = ctypes.c_int()
        
        error_code = self.dll.SEPIA2_SWS_GetParamRanges(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_wavelen_upper),
                                                        ctypes.byref(c_wavelen_lower),
                                                        ctypes.byref(c_wavelen_stepwidth),
                                                        ctypes.byref(c_wavelen_power_mode_toggle),
                                                        ctypes.byref(c_bandwidth_upper),
                                                        ctypes.byref(c_bandwidth_lower),
                                                        ctypes.byref(c_backwidth_stepwidth),
                                                        ctypes.byref(c_beam_shifter_upper),
                                                        ctypes.byref(c_beam_shifter_lower),
                                                        ctypes.byref(c_beam_shifter_stepwidth))
        self.check_error(error_code, "SEPIA2_SWS_GetParamRanges")

        return c_wavelen_upper.value, c_wavelen_lower.value, c_wavelen_stepwidth.value, \
            c_wavelen_power_mode_toggle.value, c_bandwidth_upper.value, c_bandwidth_lower.value, \
            c_backwidth_stepwidth.value, c_beam_shifter_upper.value, c_beam_shifter_lower.value, \
            c_beam_shifter_stepwidth.value

    @handle_errors
    def sws_get_parameters(self, device_id: int, slot_id: int) -> (int, int):
        c_wavelen = ctypes.c_ulong()
        c_bandwidth = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SWS_GetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_wavelen),
                                                       ctypes.byref(c_bandwidth))
        self.check_error(error_code, "SEPIA2_SWS_GetParameters")

        return c_wavelen.value, c_bandwidth.value

    @handle_errors
    def sws_set_parameters(self, device_id: int, slot_id: int, wavelength: int, bandwidth: int) \
            -> None:
        error_code = self.dll.SEPIA2_SWS_SetParameters(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_ulong(wavelength),
                                                       ctypes.c_ulong(bandwidth))
        self.check_error(error_code, "SEPIA2_SWS_SetParameters")

    @handle_errors
    def sws_get_intensity(self, device_id: int, slot_id: int) -> (int, float):
        c_intensity_raw = ctypes.c_ulong()
        c_intensity = ctypes.c_float()

        error_code = self.dll.SEPIA2_SWS_GetIntensity(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      ctypes.byref(c_intensity_raw),
                                                      ctypes.byref(c_intensity))
        self.check_error(error_code, "SEPIA2_SWS_GetIntensity")

        return c_intensity_raw.value, c_intensity.value

    @handle_errors
    def sws_get_fw_version(self, device_id: int, slot_id: int) -> (int, int, int):
        c_fw_version = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SWS_GetFWVersion(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_SWS_GetFWVersion")

        fw_version_bytes = c_fw_version.value.to_bytes(4)

        # major, minor, build
        return fw_version_bytes[0], fw_version_bytes[1], int.from_bytes(fw_version_bytes[2:])

    @handle_errors
    def sws_update_firmware(self, device_id: int, slot_id: int, fwr_filename: str) -> None:
        c_fwr_filename_str = ctypes.create_string_buffer(fwr_filename)

        error_code = self.dll.SEPIA2_SWS_UpdateFirmware(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        c_fwr_filename_str)
        self.check_error(error_code, "SEPIA2_SWS_UpdateFirmware")

    @handle_errors
    def sws_set_fram_write_protect(self, device_id: int, slot_id: int, write_protect: bool) -> None:
        error_code = self.dll.SEPIA2_SWS_SetFRAMWriteProtect(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             ctypes.c_ubyte(write_protect))
        self.check_error(error_code, "SEPIA2_SWS_SetFRAMWriteProtect")

    @handle_errors
    def sws_get_beam_pos(self, device_id: int, slot_id: int) -> (int, int):
        c_beam_vpos = ctypes.c_short()
        c_beam_hpos = ctypes.c_short()

        error_code = self.dll.SEPIA2_SWS_GetBeamPos(ctypes.c_int(device_id), ctypes.c_int(slot_id),
                                                    ctypes.byref(c_beam_vpos),
                                                    ctypes.byref(c_beam_hpos))
        self.check_error(error_code, "SEPIA2_SWS_GetBeamPos")

        return c_beam_vpos.value, c_beam_hpos.value

    @handle_errors
    def sws_set_beam_pos(self, device_id: int, slot_id: int, beam_vpos: int, beam_hpos: int) \
            -> None:
        error_code = self.dll.SEPIA2_SWS_SetBeamPos(ctypes.c_int(device_id), ctypes.c_int(slot_id),
                                                    ctypes.c_short(beam_vpos),
                                                    ctypes.c_short(beam_hpos))
        self.check_error(error_code, "SEPIA2_SWS_SetBeamPos")

    @handle_errors
    def sws_set_calibration_mode(self, device_id: int, slot_id: int, calibration_mode: bool) -> None:
        error_code = self.dll.SEPIA2_SWS_SetCalibrationMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_ubyte(calibration_mode))
        self.check_error(error_code, "SEPIA2_SWS_SetCalibrationMode")

    @handle_errors
    def sws_get_cal_table_size(self, device_id: int, slot_id: int) -> (int, int):
        c_wavelen_count = ctypes.c_ushort()
        c_bandwidth_count = ctypes.c_ushort()

        error_code = self.dll.SEPIA2_SWS_GetCalTableSize(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_wavelen_count),
                                                         ctypes.byref(c_bandwidth_count))
        self.check_error(error_code, "SEPIA2_SWS_GetCalTableSize")

        return c_wavelen_count.value, c_bandwidth_count.value

    @handle_errors
    def sws_set_cal_table_size(self, device_id: int, slot_id: int, wavelen_count: int,
                               bandwidth_count: int, init: bool) -> None:
        error_code = self.dll.SEPIA2_SWS_SetCalTableSize(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_ushort(wavelen_count),
                                                         ctypes.c_ushort(bandwidth_count),
                                                         ctypes.c_byte(init))
        self.check_error(error_code, "SEPIA2_SWS_SetCalTableSize")

    @handle_errors
    def sws_get_cal_point_info(self, device_id: int, slot_id: int, wavelen_id: int,
                               bandwidth_id: int) -> (int, int, int, int):
        c_wavelength = ctypes.c_ulong()
        c_bandwidth = ctypes.c_ulong()
        c_beam_vpos = ctypes.c_short()
        c_beam_hpos = ctypes.c_short()

        error_code = self.dll.SEPIA2_SWS_GetCalPointInfo(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_short(wavelen_id),
                                                         ctypes.c_short(bandwidth_id),
                                                         ctypes.byref(c_wavelength),
                                                         ctypes.byref(c_bandwidth),
                                                         ctypes.byref(c_beam_vpos),
                                                         ctypes.byref(c_beam_hpos))
        self.check_error(error_code, "SEPIA2_SWS_GetCalPointInfo")

        return c_wavelength.value, c_bandwidth.value, c_beam_vpos.value, c_beam_hpos.value

    @handle_errors
    def sws_set_cal_point_values(self, device_id: int, slot_id: int, wavelen_id: int,
                                 bandwidth_id: int, beam_vpos: int, beam_hpos: int) -> None:
        error_code = self.dll.SEPIA2_SWS_SetCalPointValues(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.c_short(wavelen_id),
                                                           ctypes.c_short(bandwidth_id),
                                                           ctypes.c_short(beam_vpos),
                                                           ctypes.c_short(beam_hpos))
        self.check_error(error_code, "SEPIA2_SWS_SetCalPointValues")

    @handle_errors
    def ssm_decode_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_id: int) -> (str, int, bool):
        c_freq_trig_str = ctypes.create_string_buffer(15)
        c_frequency = ctypes.c_int()
        c_trig_level_enabled = ctypes.c_byte()

        error_code = self.dll.SEPIA2_SSM_DecodeFreqTrigMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq_trig_id),
                                                            ctypes.byref(c_freq_trig_str),
                                                            ctypes.byref(c_frequency),
                                                            ctypes.byref(c_trig_level_enabled))
        self.check_error(error_code, "SEPIA2_SSM_DecodeFreqTrigMode")

        return c_freq_trig_str.value.decode(self.str_encoding), c_frequency.value, \
            bool(c_trig_level_enabled.value)

    @handle_errors
    def ssm_get_trig_level_range(self, device_id: int, slot_id: int) -> (int, int, int):
        c_trig_level_upper = ctypes.c_int()
        c_trig_level_lower = ctypes.c_int()
        c_trig_level_resolution = ctypes.c_int()

        error_code = self.dll.SEPIA2_SSM_GetTrigLevelRange(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.byref(c_trig_level_upper),
                                                           ctypes.byref(c_trig_level_lower),
                                                           ctypes.byref(c_trig_level_resolution))
        self.check_error(error_code, "SEPIA2_SSM_GetTrigLevelRange")

        return c_trig_level_upper.value, c_trig_level_lower.value, c_trig_level_resolution.value

    @handle_errors
    def ssm_get_trigger_data(self, device_id: int, slot_id: int) -> (int, int):
        c_freq_trig_id = ctypes.c_int()
        c_trig_level = ctypes.c_int()

        error_code = self.dll.SEPIA2_SSM_GetTriggerData(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_freq_trig_id),
                                                        ctypes.byref(c_trig_level))
        self.check_error(error_code, "SEPIA2_SSM_GetTriggerData")

        return c_freq_trig_id.value, c_trig_level.value

    @handle_errors
    def ssm_set_trigger_data(self, device_id: int, slot_id: int, freq_trig_id: int,
                             trig_level: int) -> None:
        error_code = self.dll.SEPIA2_SSM_SetTriggerData(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_int(freq_trig_id),
                                                        ctypes.c_int(trig_level))
        self.check_error(error_code, "SEPIA2_SSM_SetTriggerData")

    @handle_errors
    def ssm_set_fram_write_protect(self, device_id: int, slot_id: int, write_protect: bool) -> None:
        error_code = self.dll.SEPIA2_SSM_SetFRAMWriteProtect(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             ctypes.c_ubyte(write_protect))
        self.check_error(error_code, "SEPIA2_SSM_SetFRAMWriteProtect")

    @handle_errors
    def ssm_get_fram_write_protect(self, device_id: int, slot_id: int) -> bool:
        c_write_protect = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SSM_GetFRAMWriteProtect(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             ctypes.byref(c_write_protect))
        self.check_error(error_code, "SEPIA2_SSM_GetFRAMWriteProtect")

        return bool(c_write_protect.value)
