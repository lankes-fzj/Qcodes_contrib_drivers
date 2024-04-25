import functools as ft
import typing as tp

import qcodes as qc

from .Sepia_Library import PicoquantSepia2Lib, PicoquantSepia2LibError


class PicoquantSepia2Module(qc.instrument.InstrumentChannel):
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
    def __init__(self, parent: "PicoquantSepia2", name: str, slot_id: int, is_primary: bool = True):
        super().__init__(parent, name, slot_id, is_primary)

        self.add_parameter("lock",
                           get_cmd=ft.partial(self._lib.scm_get_laser_soft_lock,
                                              self._device_id, self._slot_id),
                           set_cmd=ft.partial(self._lib.scm_set_laser_soft_lock,
                                              self._device_id, self._slot_id),
                           vals=qc.validators.Bool())
        self.add_parameter("soft_lock",
                           get_cmd=ft.partial(self._lib.scm_get_laser_locked,
                                              self._device_id, self._slot_id),
                           set_cmd=False,
                           vals=qc.validators.Bool())


class PicoquantSepia2SLMModule(PicoquantSepia2Module):
    def __init__(self, parent: "PicoquantSepia2", name: str, slot_id: int, is_primary: bool = True):
        super().__init__(parent, name, slot_id, is_primary)

        freq_modes = {'80MHz': 0,
                      '40MHz': 1,
                      '20MHz': 2,
                      '10MHz': 3,
                      '5MHz': 4,
                      '2.5MHz': 5,
                      'rising edge': 6,
                      'falling edge': 7}

        self.add_parameter("power",
                           label="Power intensity",
                           unit="%",
                           get_cmd=ft.partial(self._lib.slm_get_intensity_fine_step,
                                              self._device_id, self._slot_id),
                           set_cmd=ft.partial(self._lib.slm_set_intensity_fine_step,
                                              self._device_id, self._slot_id),
                           vals=qc.validators.Numbers(0, 100),
                           get_parser=lambda raw: raw / 10,
                           set_parser=lambda val: int(val * 10))
        self.add_parameter("freq",
                           label="Frequency mode",
                           get_cmd=ft.partial(self._lib.slm_get_pulse_parameters,
                                              self._lib._device_id, self._slot_id),
                           set_cmd=self._set_freq,
                           get_parser=lambda raw: raw[0],
                           val_mapping=freq_modes,
                           vals=qc.validators.Ints(0, 7))
        self.add_parameter("mode",
                           label="Pulse mode",
                           get_cmd=ft.partial(self._lib.slm_get_pulse_parameters,
                                              self._lib._device_id, self._slot_id),
                           set_cmd=self._set_pulse_mode,
                           get_parser=lambda raw: raw[1],
                           val_mapping={"cw": True, "pulsed": False},
                           vals=qc.validators.Bool())

    def _set_freq(self, freq: int) -> None:
        _, pulse_mode, _ = self._lib.slm_get_pulse_parameters(self._device_id, self._slot_id)
        self._lib.slm_set_pulse_parameters(self._device_id, self._slot_id, freq, pulse_mode)

    def _set_pulse_mode(self, pulse_mode: bool) -> None:
        freq, _, _ = self._lib.slm_get_pulse_parameters(self._device_id, self._slot_id)
        self._lib.slm_set_pulse_parameters(self._device_id, self._slot_id, freq, pulse_mode)


class PicoquantSepia2(qc.Instrument):
    def __init__(self, name, product_model: str = None, serial_num: str = None,
                 dll_path: str = None, str_encoding: str = None, perform_restart: bool = False):
        super().__init__(name)

        self._lib = PicoquantSepia2Lib(dll_path, str_encoding)

        self._device_id = -1
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
            raise RuntimeError("Could not find Picoquant Sepia II device matching the conditions")

        # Get firmware version
        self._fw_version = self._lib.fwr_get_version(self._device_id)

        # Initialize modules
        self._modules = self._init_modules(perform_restart)

        # Print connect message
        self.connect_message()

    def get_idn(self) -> tp.Dict[str, str]:
        return {"vendor": "PicoQuant", "model": self._product_model,
                "serial": self._serial_num, "firmware": self._fw_version}

    def close(self) -> None:
        self._lib.usb_close_device(self._device_id)
        super().close()

    def _init_modules(self, perform_restart: bool = False) -> tp.List[PicoquantSepia2Module]:
        modules = []
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
                mod = PicoquantSepia2Module(self, mod_type_name, slot_id)
                modules.append(mod)
                self.add_submodule(mod_type_abbr, mod)
        finally:
            self._lib.fwr_free_module_map(self._device_id)

        # Add channel list
        ch_tuple = qc.instrument.ChannelTuple(self, "modules", PicoquantSepia2Module, self._modules)
        self.add_submodule("modules", ch_tuple)

        return modules

    @staticmethod
    def list_usb_devices(dll_path: str = None, str_encoding: str = None):
        lib = PicoquantSepia2Lib(dll_path, str_encoding)
        devices = []

        for i in range(8):
            try:
                product, serial = lib.usb_open_get_ser_num_and_close(i, ignore_blocked_busy=True)
            except PicoquantSepia2LibError:
                continue

            devices.append((i, product, serial))

        return devices
