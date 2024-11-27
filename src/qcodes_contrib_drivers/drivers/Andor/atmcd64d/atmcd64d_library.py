import ctypes as ct
import _ctypes
import typing as tp
import sys

from .atmcd64d_utils import Atmcd64dLibError, Atmcd64dExitCodes, Atmcd64dAcquisitionModes, \
    Atmcd64dReadModes, Atmcd64dShutterTypes, Atmcd64dShutterModes, Atmcd64dTriggerModes, \
    TEMPERATURE_IGNORE_ERRORS


class Atmcd64dLib:
    """
    Wrapper class for the atmcd64.dll Andor library.
    The class has been tested for an Andor iDus DU401 BU2.

    Args:
        dll_path: Path to the atmcd64.dll file. If not set, a default path is used.
    """

    _DEFAULT_DLL_PATH = r"C:\Program Files\Andor SDK\atmcd64d.dll"
    _DEFAULT_ENCODING = "ascii"

    def __init__(self, dll_path: str = None, str_encoding: str = None):
        self._dll_path = dll_path or self._DEFAULT_DLL_PATH
        self._str_encoding = str_encoding or self._DEFAULT_ENCODING

        if sys.platform != "win32":
            # wrong OS
            raise OSError("\"atmcd64d.dll\" is only compatible with Microsoft Windows")

        self._dll = ct.windll.LoadLibrary(self._dll_path)

    def __del__(self):
        if self._dll is not None:
            # shutdown driver
            self.shut_down()

    def error_check(self, code: int, function_name: str, error_msg: str = "",
                    ignore: tp.List[int] = None):
        """Checks if exit code of library function.
        
        If the exit code indicates failure, an exception is raised.

        Args:
            code (int): Exit code
            function_name (str): Function that was called
            error_msg (str, optional): Message to append to exception message.
            ignore (tp.List[int], optional): Exit codes to ignore. These exit codes are treated like
                success.
        """
        if code == Atmcd64dExitCodes.DRV_SUCCESS:
            return
        if ignore and code in ignore:
            return

        raise Atmcd64dLibError(code, error_msg, function_name)

    def shut_down(self) -> None:
        """This function will close the AndorMCD system down."""
        code = self._dll.ShutDown()
        self.error_check(code, "ShutDown")

        # Unload DLL
        _ctypes.FreeLibrary(self._dll._handle)
        self._dll = None

    def cooler_off(self) -> None:
        """Switches OFF the cooling.
        
        The rate of temperature change is controlled in some models until the temperature reaches 0
        °C. Control is returned immediately to the calling application.
        """
        code = self._dll.CoolerOFF()
        self.error_check(code, "CoolerOFF")

    def cooler_on(self) -> None:
        """Switches ON the cooling.
        
        On some systems the rate of temperature change is controlled until the temperature is within
        3 °C of the set value. Control is returned immediately to the calling application.
        """
        code = self._dll.CoolerON()
        self.error_check(code, "CoolerON")

    def get_acquired_data(self, size: int) -> tp.List[int]:
        """This function will return the data from the last acquisition.
        
        The data are returned as long integers (32-bit signed integers). The "array" must be large
        enough to hold the complete data set.

        Args:
            size (int): Total number of pixels

        Returns:
            Data storage
        """
        c_data = (ct.c_long * size)()

        code = self._dll.GetAcquiredData(ct.byref(c_data), ct.c_ulong(size))
        self.error_check(code, "GetAcquiredData")

        return list(c_data)

    def get_acquisition_timings(self) -> (float, float, float):
        """This function will return the current "valid" acquisition timing information.
        
        This function should be used after all the acquisitions settings have been set, e.g.
        `set_exposure_time`, `set_kinetic_cycle_time` and `set_read_mode` etc. The values returned
        are the actual times used in subsequent acquisitions.
        
        This function is required as it is possible to set the exposure time to 20ms, accumulate
        cycle time to 30ms and then set the readout mode to full image. As it can take 250ms to read
        out an image it is not possible to have a cycle time of 30ms.

        Returns:
            exposure (float): valid exposure time in seconds
            accumulate (float): valid accumulate cycle time in seconds
            kinetic (float): valid kinetic cycle time in seconds
        """
        c_exposure = ct.c_float()
        c_accumulate = ct.c_float()
        c_kinetic = ct.c_float()

        code = self._dll.GetAcquisitionTimings(ct.byref(c_exposure), ct.byref(c_accumulate),
                                               ct.byref(c_kinetic))
        self.error_check(code, "GetAcquisitionTimings")

        return c_exposure.value, c_accumulate.value, c_kinetic.value

    def get_available_cameras(self) -> int:
        """This function returns the total number of Andor cameras currently installed.
        
        It is possible to call this function before any of the cameras are initialized.
        
        Returns:
            int: number of cameras currently installed
        """
        c_total_cameras = ct.c_long()

        code = self._dll.GetAvailableCameras(ct.byref(c_total_cameras))
        self.error_check(code, "GetAvailableCameras")

        return c_total_cameras.value

    def get_camera_handle(self, camera_index: int) -> int:
        """This function returns the handle for the camera specified by cameraIndex.
        
        When multiple Andor cameras are installed the handle of each camera must be retrieved in
        order to select a camera using the `set_current_camera` function.
        
        The number of cameras can be obtained using the `get_available_cameras` function.

        Args:
            camera_index (int): index of any of the installed cameras (from 0 to NumberOfCameras-1,
                where NumberOfCameras is the value returned by the get_available_cameras function)

        Returns:
            int: _description_
        """
        c_camera_handle = ct.c_long()

        code = self._dll.GetCameraHandle(ct.c_long(camera_index), ct.byref(c_camera_handle))
        self.error_check(code, "GetCameraHandle")

        return c_camera_handle.value

    def get_camera_serial_number(self) -> int:
        """This function will retrieve camera’s serial number.

        Returns:
            int: serial number
        """
        c_serial_number = ct.c_int()

        code = self._dll.GetCameraSerialNumber(ct.byref(c_serial_number))
        self.error_check(code, 'GetCameraSerialNumber')

        return c_serial_number.value

    def get_hardware_version(self) -> (int, int, int, int, int, int):
        """This function returns the Hardware version information.

        Returns:
            pcb (int): Plug-in card version
            decode (int): Flex 10K file version
            dummy1 (int): dummy1
            dummy2 (int): dummy2
            firmware_version (int): Version number of camera firmware
            firmware_build (int): Build number of camera firmware
        """
        c_pcb = ct.c_uint()
        c_decode = ct.c_uint()
        c_dummy1 = ct.c_uint()
        c_dummy2 = ct.c_uint()
        c_firmware_version = ct.c_uint()
        c_firmware_build = ct.c_uint()

        code = self._dll.GetHardwareVersion(ct.byref(c_pcb), ct.byref(c_decode), ct.byref(c_dummy1),
                                            ct.byref(c_dummy2), ct.byref(c_firmware_version),
                                            ct.byref(c_firmware_build))
        self.error_check(code, "GetHardwareVersion")

        return c_pcb.value, c_decode.value, c_dummy1.value, c_dummy2.value, \
            c_firmware_version.value, c_firmware_build.value

    def get_head_model(self) -> str:
        """This function will retrieve the type of CCD attached to your system.

        Returns:
            str: head model
        """
        c_head_model = ct.create_string_buffer(260)

        code = self._dll.GetHeadModel(c_head_model)
        self.error_check(code, "GetHeadModel")

        return c_head_model.value.decode(self._str_encoding)

    def get_detector(self) -> (int, int):
        """This function returns the size of the detector in pixels.
        
        The horizontal axis is taken to be the axis parallel to the readout register.

        Returns:
            x_pixels (int): number of horizontal pixels.
            y_pixels (int): number of vertical pixels.
        """
        c_x_pixels = ct.c_int()
        c_y_pixels = ct.c_int()

        code = self._dll.GetDetector(ct.byref(c_x_pixels), ct.byref(c_y_pixels))
        self.error_check(code, "GetDetector")

        return c_x_pixels.value, c_y_pixels.value

    def get_filter_mode(self) -> bool:
        """This function returns the current state of the cosmic ray filtering mode.

        Returns:
            bool: current state of filter (True: ON, False: OFF)
        """
        c_mode = ct.c_int()

        code = self._dll.GetFilterMode(ct.byref(c_mode))
        self.error_check(code, "GetFilterMode")

        # Convert mode to bool (0 -> False, 2 -> True)
        return bool(c_mode.value)

    def get_status(self) -> Atmcd64dExitCodes:
        """This function will return the current status of the Andor SDK system.
        
        This function should be called before an acquisition is started to ensure that it is IDLE
        and during an acquisition to monitor the process.

        Note:
            If the status is one of the following:
                * DRV_ACCUM_TIME_NOT_MET
                * DRV_KINETIC_TIME_NOT_MET
                * DRV_ERROR_ACK
                * DRV_ACQ_BUFFER
                * DRV_ACQ_DOWNFIFO_FULL
            then the current acquisition will be aborted automatically.

        Returns:
            Atmcd64dExitCodes: current status
        """
        c_status = ct.c_int()

        code = self._dll.GetStatus(ct.byref(c_status))
        self.error_check(code, "GetStatus")

        return Atmcd64dExitCodes(c_status.value)

    def get_temperature(self) -> int:
        """This function returns the temperature of the detector to the nearest degree.
        
        It also gives the status of cooling process.
        
        Returns:
            int: temperature of the detector
        """
        c_temperature = ct.c_int()

        code = self._dll.GetTemperature(ct.byref(c_temperature))
        self.error_check(code, "GetTemperature", ignore=TEMPERATURE_IGNORE_ERRORS)

        return c_temperature.value

    def get_temperature_range(self) -> (int, int):
        """This function returns the valid range of temperatures in centigrade to which the detector
        can be cooled.

        Returns:
            mintemp (int): minimum temperature
            maxtemp (int): maximum temperature
        """
        c_min_temp = ct.c_int()
        c_max_temp = ct.c_int()

        code = self._dll.GetTemperatureRange(ct.byref(c_min_temp), ct.byref(c_max_temp))
        self.error_check(code, "GetTemperatureRange")

        return c_min_temp.value, c_max_temp.value

    def initialize(self, directory: str) -> None:
        """This function will initialize the Andor SDK System.
        
        As part of the initialization procedure on some cameras (i.e. Classic, iStar and earlier
        iXion) the DLL will need access to a DETECTOR.INI which contains information relating to the
        detector head, number pixels, readout speeds etc.

        Args:
            directory (str): Path to the directory containing the files
        """
        c_directory = ct.create_string_buffer(directory)

        code = self._dll.Initialize(ct.byref(c_directory))
        self.error_check(code, "Initialize")

    def is_cooler_on(self) -> bool:
        """This function checks the status of the cooler.

        Returns:
            bool: cooler status (False: OFF, True: ON)
        """
        c_cooler_status = ct.c_int()

        code = self._dll.IsCoolerOn(ct.byref(c_cooler_status))
        self.error_check(code, "IsCoolerOn")

        return bool(c_cooler_status.value)

    def set_accumulation_cycle_time(self, cycle_time: float) -> None:
        """This function will set the accumulation cycle time to the nearest valid value not less
        than the given value. The actual cycle time used is obtained by `get_acquisition_timings`.

        Args:
            cycle_time (float): the accumulation cycle time in seconds.
        """
        code = self._dll.SetAccumulationCycleTime(ct.c_float(cycle_time))
        self.error_check(code, "SetAccumulationCycleTime")

    def set_acquisition_mode(self, mode: Atmcd64dAcquisitionModes) -> None:
        """This function will set the acquisition mode to be used on the next `start_acquisition`.

        Args:
            mode (Atmcd64dAcquisitionModes): the acquisition mode
        """
        code = self._dll.SetAcquisitionMode(ct.c_int(int(mode)))
        self.error_check(code, "SetAcquisitionMode")

    def set_current_camera(self, camera_handle: int) -> None:
        """When multiple Andor cameras are installed this function allows the user to select which
        camera is currently active.
        
        Once a camera has been selected the other functions can be called as normal but they will
        only apply to the selected camera. If only 1 camera is installed calling this function is
        not required since that camera will be selected by default.

        Args:
            camera_handle (int): Handle of the camera to select
        """
        code = self._dll.SetCurrentCamera(ct.c_long(camera_handle))
        self.error_check(code, "SetCurrentCamera")

    def set_exposure_time(self, exposure_time: float) -> None:
        """This function will set the exposure time to the nearest valid value not less than the
        given value.
        
        The actual exposure time used is obtained by `get_acquisition_timings`.

        Args:
            exposure_time (float): the exposure time in seconds.
        """
        code = self._dll.SetExposureTime(ct.c_float(exposure_time))
        self.error_check(code, "SetExposureTime")

    def set_filter_mode(self, mode: bool) -> None:
        """This function will set the state of the cosmic ray filter mode for future acquisitions.
        
        If the filter mode is ON (True), consecutive scans in an accumulation will be compared and
        any cosmic ray-like features that are only present in one scan will be replaced with a
        scaled version of the corresponding pixel value in the correct scan.

        Args:
            mode (bool): current state of the filter (False: OFF, True: ON)
        """
        code = self._dll.SetFilterMode(ct.c_int(2 if mode else 0))
        self.error_check(code, "SetFilterMode")

    def set_number_accumulations(self, number: int) -> None:
        """This function will set the number of scans accumulated in memory.
        
        This will only take effect if the acquisition mode is either Accumulate or Kinetic Series.

        Args:
            number (int): number of scans to accumulate
        """
        code = self._dll.SetNumberAccumulations(ct.c_int(number))
        self.error_check(code, "SetNumberAccumulations")

    def set_read_mode(self, mode: Atmcd64dReadModes) -> None:
        """This function will set the readout mode to be used on the subsequent acquisitions.
        
        Args:
            mode (Atmcd64dReadModes): readout mode
        """
        code = self._dll.SetReadMode(ct.c_int(int(mode)))
        self.error_check(code, "SetReadMode")

    def set_shutter(self, typ: Atmcd64dShutterTypes, mode: Atmcd64dShutterModes, closing_time: int,
                    opening_time: int) -> None:
        """This function controls the behaviour of the shutter.
        
        The typ parameter allows the user to control the TTL signal output to an external shutter.
        
        The mode parameter configures whether the shutter opens & closes automatically (controlled
        by the camera) or is permanently open or permanently closed.
        
        The opening and closing time specify the time required to open and close the shutter
        
        Args:
            typ (Atmcd64dShutterTypes): TTL signal output (0: low, 1: high)
            mode (Atmcd64dShutterModes): shutter mode
            closing_time (int): Time shutter takes to close (milliseconds)
            opening_time (int): Time shutter takes to open (milliseconds)
        """
        code = self._dll.SetShutter(ct.c_int(int(typ)), ct.c_int(int(mode)), ct.c_int(closing_time),
                                    ct.c_int(opening_time))
        self.error_check(code, "SetShutter")

    def set_temperature(self, temperature: int) -> None:
        """This function will set the desired temperature of the detector.
        
        To turn the cooling ON and OFF use the `cooler_on` and `cooler_off` function respectively.
        
        Args:
            temperature (int): the temperature in °C.
        """
        code = self._dll.SetTemperature(ct.c_int(temperature))
        self.error_check(code, "SetTemperature")

    def set_trigger_mode(self, mode: Atmcd64dTriggerModes) -> None:
        """This function will set the trigger mode that the camera will operate in.

        Args:
            mode (Atmcd64dTriggerModes): trigger mode
        """
        code = self._dll.SetTriggerMode(ct.c_int(int(mode)))
        self.error_check(code, "SetTriggerMode")

    def start_acquisition(self) -> None:
        """This function starts an acquisition.
        
        The status of the acquisition can be monitored via `get_status`.
        """
        code = self._dll.StartAcquisition()
        self.error_check(code, "StartAcquisition")

    def wait_for_acquisition(self) -> None:
        """This function can be called after an acquisition is started using `start_acquisition` to
        put the calling thread to sleep until an Acquisition Event occurs.
        
        This can be used as a simple alternative to the functionality provided by the
        `set_driver_event` function, as all Event creation and handling is performed internally by
        the SDK library.
        
        Like the `set_driver_event` functionality it will use less processor resources than
        continuously polling with the `get_status` function. If you wish to restart the calling
        thread without waiting for an Acquisition event, call the function `cancel_wait`.

        An Acquisition Event occurs each time a new image is acquired during an Accumulation,
        Kinetic Series or Run-Till-Abort acquisition or at the end of a Single Scan Acquisition.

        If a second event occurs before the first one has been acknowledged, the first one will be
        ignored. Care should be taken in this case, as you may have to use `cancel_wait` to exit the
        function.
        """
        code = self._dll.WaitForAcquisition()
        self.error_check(code, "WaitForAcquisition")

    def cancel_wait(self) -> None:
        """This function aborts the current acquisition if one is active."""
        code = self._dll.CancelWait()
        self.error_check(code, "CancelWait")

    def abort_acquisition(self) -> None:
        """This function aborts the current acquisition if one is active."""
        code = self._dll.AbortAcquisition()
        self.error_check(code, "AbortAcquisition")

    def set_single_track(self, center: int, height: int) -> None:
        """This function will set the single track parameters.

        The parameters are validated in the following order: center row and then track height.

        Args:
            center (int): center row of track (from 1 to number of vertical pixels)
            height (int): height of track (> 1; maximum value depends on centre row and number of
                vertical pixels)
        """
        code = self._dll.SetSingleTrack(ct.c_int(center), ct.c_int(height))
        self.error_check(code, "SetSingleTrack")

    def get_number_hshift_speeds(self) -> int:
        """As your Andor SDK system is capable of operating at more than one horizontal shift speed
        this function will return the actual number of speeds available.
        
        Returns:
            int: Number of allowed horizontal speeds
        """
        c_num_speeds = ct.c_int()

        code = self._dll.GetNumberHSSpeeds(ct.c_int(0), ct.c_int(0), ct.byref(c_num_speeds))
        self.error_check(code, "GetNumberHSSpeeds")

        return c_num_speeds.value

    def get_number_vshift_speeds(self) -> int:
        """As your Andor SDK system is capable of operating at more than one vertical shift speed
        this function will return the actual number of speeds available.
        
        Returns:
            int: Number of allowed vertical speeds
        """
        c_num_speeds = ct.c_int()

        code = self._dll.GetNumberVSSpeeds(ct.c_int(0), ct.c_int(0), ct.byref(c_num_speeds))
        self.error_check(code, "GetNumberVSSpeeds")

        return c_num_speeds.value

    def get_hshift_speed(self, speed_index: int) -> float:
        """As your Andor system is capable of operating at more than one horizontal shift speed this
        function will return the actual speeds available. The value returned is in MHz.

        Args:
            speed_index (int): speed required (from 0 to NumerOfSpeeds-1, where NumberOfSpeeds can
                be requested via `get_number_hshift_speeds`)

        Returns:
            float: speed in MHz
        """
        c_speed = ct.c_float()

        code = self._dll.GetHSSpeed(ct.c_int(0), ct.c_int(0), ct.c_int(speed_index),
                                    ct.byref(c_speed))
        self.error_check(code, "GetHSSpeed")

        return c_speed.value

    def set_hshift_speed(self, speed_index: int) -> None:
        """This function will set the speed at which the pixels are shifted into the output node
        during the readout phase of an acquisition.
        
        Typically your camera will be capable of operating at several horizontal shift speeds. To
        get the actual speed that an index corresponds to use the `get_hshift_speed` function.

        Args:
            speed_index (int): the horizontal speed to be used (from 0 to NumerOfSpeeds-1, where
                NumberOfSpeeds can be requested via `get_number_hshift_speeds`)
        """
        code = self._dll.SetHSSpeed(0, ct.c_int(speed_index))
        self.error_check(code, "SetHSSpeed")

    def get_vshift_speed(self, speed_index: int) -> float:
        """As your Andor system is capable of operating at more than one vertical shift speed this
        function will return the actual speeds available. The value returned is in MHz.

        Args:
            speed_index (int): speed required (from 0 to NumerOfSpeeds-1, where NumberOfSpeeds can
                be requested via `get_number_hshift_speeds`)

        Returns:
            float: speed in MHz
        """
        c_speed = ct.c_float()

        code = self._dll.GetVSSpeed(ct.c_int(speed_index), ct.byref(c_speed))
        self.error_check(code, "GetVSSpeed")

        return c_speed.value

    def set_vshift_speed(self, speed_index: int) -> None:
        """This function will set the speed at which the pixels are shifted into the output node
        during the readout phase of an acquisition.
        
        Typically your camera will be capable of operating at several vertical shift speeds. To
        get the actual speed that an index corresponds to use the `get_hshift_speed` function.

        Args:
            speed_index (int): the vertical speed to be used (from 0 to NumerOfSpeeds-1, where
                NumberOfSpeeds can be requested via `get_number_hshift_speeds`)
        """
        code = self._dll.SetVSSpeed(ct.c_int(speed_index))
        self.error_check(code, "SetVSSpeed")

    def get_number_pre_amp_gains(self) -> int:
        """Available in some systems are a number of pre amp gains that can be applied to the data
        as it is read out. This function gets the number of these pre amp gains available.
        
        The functions `get_pre_amp_gain` and `set_pre_amp_gain` can be used to specify which of
        these gains is to be used.
        """
        c_num_gains = ct.c_int()

        code = self._dll.GetNumberPreAmpGains(ct.byref(c_num_gains))
        self.error_check(code, "GetNumberPreAmpGains")

        return c_num_gains.value

    def get_pre_amp_gain(self, gain_index: int) -> float:
        """For those systems that provide a number of pre amp gains to apply to the data as it is
        read out; this function retrieves the amount of gain that is stored for a particular index.
        
        The number of gains available can be obtained by calling the `get_number_pre_amp_gains`
        function and a specific Gain can be selected using the function `set_pre_amp_gain`.

        Args:
            gain_index (int): gain index (from 0 to `get_number_pre_amp_gains`-1)

        Returns:
            float: gain factor for the given index.
        """
        c_pre_amp_gain = ct.c_float()

        code = self._dll.GetPreAmpGain(ct.c_int(gain_index), ct.byref(c_pre_amp_gain))
        self.error_check(code, "GetPreAmpGain")

        return c_pre_amp_gain.value

    def set_pre_amp_gain(self, gain_index: int) -> None:
        """This function will set the pre amp gain to be used for subsequent acquisitions.
        
        The actual gain factor that will be applied can be found through a call to the
        `get_pre_amp_gain` function.

        The number of Pre Amp Gains available is found by calling the `get_number_pre_amp_gains`
        function.

        Args:
            gain_index (int): index pre amp gain table (from 0 to `get_number_pre_amp_gains`-1)
        """
        code = self._dll.SetPreAmpGain(ct.c_int(gain_index))
        self.error_check(code, "SetPreAmpGain")
