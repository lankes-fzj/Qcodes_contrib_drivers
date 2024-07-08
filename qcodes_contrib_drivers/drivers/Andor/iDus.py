import os, sys
from qcodes import Instrument, Parameter
import qcodes.utils.validators as qc_vals
from qcodes.utils.helpers import create_on_off_val_mapping
import typing as tp

from .atmcd64d.atmcd64d_library import Atmcd64dLib, Atmcd64dAcquisitionModes, Atmcd64dReadModes, \
    Atmcd64dShutterTypes, Atmcd64dShutterModes, Atmcd64dTriggerModes


class Spectrum(Parameter):
    """
    Parameter class for a spectrum taken with an Andor CCD.
    The spectrum is saved in a list with the length being set by the number of pixels on the CCD.

    Args:
        name: Parameter name.
    """

    def __init__(self, name: str, instrument: "Andor_DU401", **kwargs):
        super().__init__(name, instrument=instrument, **kwargs)
        self.ccd = instrument

    def get_raw(self) -> tp.List[int]:
        # get acquisition mode
        acquisition_mode = self.ccd.acquisition_mode.get()

        # start acquisition
        self.ccd.atmcd64d.start_acquisition()

        if acquisition_mode == "single scan":
            # wait for single acquisition
            self.ccd.atmcd64d.wait_for_acquisition()
        elif acquisition_mode == "accumulate":
            # wait for accumulate acquisition
            number_accumulations = self.ccd.number_accumulations.get()
            for i in range(number_accumulations):
                self.ccd.atmcd64d.wait_for_acquisition()

        # get and return spectrum
        return self.ccd.atmcd64d.get_acquired_data(self.ccd.x_pixels)

    def set_raw(self, value):
        raise NotImplementedError()


class Andor_iDus(Instrument):
    """
    Instrument driver for the Andor iDus.

    Args:
        name: Instrument name.
        dll_path: Path to the atmcd64.dll file. If not set, a default path is used.
        camera_id: ID for the desired CCD.
        setup: Flag for the setup of the CCD. If true, some default settings will be sent to the CCD.

    Attributes:
        serial_number: Serial number of the CCD.
        head_model: Head model of the CCD.
        firmware_version: Firmware version of the CCD.
        firmware_build: Firmware build of the CCD.
        x_pixels: Number of pixels on the x axis.
        y_pixels: Number of pixels on the y axis.

    """

    def __init__(self, name: str, dll_path: str = None, camera_id: int = 0, setup: bool = True,
                 **kwargs):
        super().__init__(name, **kwargs)

        # link to dll
        self.atmcd64d = Atmcd64dLib(dll_path)

        # initialization
        self.atmcd64d.initialize(" ")
        self.atmcd64d.set_current_camera(self.atmcd64d.get_camera_handle(camera_id))

        # get camera information
        self.serial_number = self.atmcd64d.get_camera_serial_number()
        self.head_model = self.atmcd64d.get_head_model()
        self.firmware_version = self.atmcd64d.get_hardware_version()[4]
        self.firmware_build = self.atmcd64d.get_hardware_version()[5]
        self.x_pixels, self.y_pixels = self.atmcd64d.get_detector()

        # add the instrument parameters
        self.add_parameter("accumulation_cycle_time",
                           get_cmd=self.atmcd64d.get_acquisition_timings,
                           set_cmd=self.atmcd64d.set_accumulation_cycle_time,
                           get_parser=lambda ans: float(ans[1]),
                           unit="s",
                           label="accumulation cycle time")

        self.add_parameter("acquisition_mode",
                           set_cmd=self.atmcd64d.set_acquisition_mode,
                           label="acquisition mode",
                           val_mapping={
                               "single scan": Atmcd64dAcquisitionModes.SINGLE_SCAN,
                               "accumulate": Atmcd64dAcquisitionModes.ACCUMULATE,
                               "kinetics": Atmcd64dAcquisitionModes.KINETICS,
                               "fast kinetics": Atmcd64dAcquisitionModes.FAST_KINETICS,
                               "run until abort": Atmcd64dAcquisitionModes.RUN_UNTIL_ABORT,
                           })

        self.add_parameter("cooler",
                           get_cmd=self.atmcd64d.is_cooler_on,
                           set_cmd=self._set_cooler,
                           val_mapping=create_on_off_val_mapping(),
                           label="cooler")

        self.add_parameter("exposure_time",
                           get_cmd=self.atmcd64d.get_acquisition_timings,
                           set_cmd=self.atmcd64d.set_exposure_time,
                           get_parser=lambda ans: float(ans[0]),
                           unit="s",
                           label="exposure time")

        self.add_parameter("filter_mode",
                           get_cmd=self.atmcd64d.get_filter_mode,
                           set_cmd=self.atmcd64d.set_filter_mode,
                           val_mapping=create_on_off_val_mapping(),
                           label="filter mode")

        self.add_parameter("number_accumulations",
                           set_cmd=self.atmcd64d.set_number_accumulations,
                           label="number accumulations")

        self.add_parameter("read_mode",
                           set_cmd=self.atmcd64d.set_read_mode,
                           val_mapping={
                               "full vertical binning": Atmcd64dReadModes.FULL_VERTICAL_BINNING,
                               "multi track": Atmcd64dReadModes.MULTI_TRACK,
                               "random track": Atmcd64dReadModes.RANDOM_TRACK,
                               "single track": Atmcd64dReadModes.SINGLE_TRACK,
                               "image": Atmcd64dReadModes.IMAGE
                           })

        min_temperature, max_temperature = self.atmcd64d.get_temperature_range()
        self.add_parameter("temperature",
                           get_cmd=self.atmcd64d.get_temperature,
                           set_cmd=self.atmcd64d.set_temperature,
                           vals=qc_vals.Ints(min_value=min_temperature,
                                             max_value=max_temperature),
                           unit="°C",
                           label="temperature")

        self.add_parameter("shutter_mode",
                           set_cmd=self._set_shutter_mode,
                           label="shutter mode",
                           val_mapping={
                               "fully auto": Atmcd64dShutterModes.FULLY_AUTO,
                               "permanently open": Atmcd64dShutterModes.PERMANENTLY_OPEN,
                               "permanently closed": Atmcd64dShutterModes.PERMANENTLY_CLOSED,
                               "open for fvb": Atmcd64dShutterModes.OPEN_FOR_FVB,
                               "open for any": Atmcd64dShutterModes.OPEN_FOR_ANY})

        self.add_parameter("single_track",
                           set_cmd=self._set_single_track,
                           label="single track definition")

        self.add_parameter("spectrum",
                           parameter_class=Spectrum,
                           shape=qc_vals.Arrays(self.x_pixels),
                           label="spectrum")

        self.add_parameter("trigger_mode",
                           set_cmd=self.atmcd64d.set_trigger_mode,
                           val_mapping={
                               "internal": Atmcd64dTriggerModes.INTERNAL,
                               "external": Atmcd64dTriggerModes.EXTERNAL,
                               "external start": Atmcd64dTriggerModes.EXTERNAL_START,
                               "external exposure": Atmcd64dTriggerModes.EXTERNAL_EXPOSURE,
                               "external fvb em": Atmcd64dTriggerModes.EXTERNAL_FVB_EM,
                               "software trigger": Atmcd64dTriggerModes.SOFTWARE_TRIGGER,
                               "external charge shift": Atmcd64dTriggerModes.EXTERNAL_CHARGE_SHIFT
                            })

        val_mapping_hspeed = {self.atmcd64d.get_hshift_speed(i): i
                              for i in range(self.atmcd64d.get_number_hshift_speeds())}
        val_mapping_vspeed = {self.atmcd64d.get_vshift_speed(i): i
                              for i in range(self.atmcd64d.get_number_vshift_speeds())}

        self.add_parameter("horizontal_speed",
                           set_cmd=self.atmcd64d.set_hshift_speed,
                           val_mapping=val_mapping_hspeed,
                           unit="MHz",
                           label="horizonal shift speed")

        self.add_parameter("vertical_speed",
                           set_cmd=self.atmcd64d.set_vshift_speed,
                           val_mapping=val_mapping_vspeed,
                           unit="MHz",
                           label="vertical shift speed")

        val_mapping_pre_amp_gain = {self.atmcd64d.get_pre_amp_gain(i): i
                                    for i in range(self.atmcd64d.get_number_pre_amp_gains())}

        self.add_parameter("pre_amp_gain",
                           set_cmd=self.atmcd64d.set_pre_amp_gain,
                           val_mapping=val_mapping_pre_amp_gain,
                           label="pre amp gain")

        # set up detector with default settings
        if setup:
            self.cooler.set("ON")
            self.set_temperature.set(-60)
            self.read_mode.set("full vertical binning")
            self.acquisition_mode.set("single scan")
            self.trigger_mode.set("internal")
            self.shutter_mode.set("fully auto")

        # print connect message
        self.connect_message(idn_param="IDN")

    # get methods
    def get_idn(self) -> tp.Dict[str, str]:
        return {"vendor": "Andor", "model": self.head_model,
                "serial": str(self.serial_number),
                "firmware": f"{self.firmware_version}.{self.firmware_build}"}

    # set methods
    def _set_cooler(self, cooler_on: int) -> None:
        if cooler_on == 1:
            self.atmcd64d.cooler_on()
        elif cooler_on == 0:
            self.atmcd64d.cooler_off()

    def _set_shutter_mode(self, shutter_mode: int) -> None:
        self.atmcd64d.set_shutter(1, shutter_mode, 30, 30)

    def _set_single_track(self, height: int) -> None:
        self.atmcd64d.set_single_track(129, height)

    # further methods
    def close(self) -> None:
        self.atmcd64d.shut_down()
        super().close()
