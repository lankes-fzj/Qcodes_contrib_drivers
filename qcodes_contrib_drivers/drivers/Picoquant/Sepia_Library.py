import ctypes
import datetime
import enum
import os
import typing

from .Sepia_Library_utils import PicoquantSepia2LibError, handle_errors, \
    PicoquantSepia2SupportRequestOptions, PicoquantSepia2Preset, \
        PicoquantSepia2SPMStates, PicoquantSepia2SWSStates


class PicoquantSepia2Lib:
    _DEFAULT_DLL_PATH = r"C:\Program Files\Picoquant\GenericLaserDriver\Sepia2_Lib.dll"
    _DEFAULT_STR_ENCODING = "utf-8"

    def __init__(self, dll_path: str = None, str_encoding: str = None):
        self.dll = ctypes.CDLL(dll_path or self._DEFAULT_DLL_PATH)
        self.str_encoding = str_encoding or self._DEFAULT_STR_ENCODING

    def check_error(self, exit_code: int, function_name: str = None) -> None:
        if exit_code == 0:
            return

        try:
            error_msg = self.lib_decode_error(exit_code)
        except PicoquantSepia2LibError:
            error_msg = None

        raise PicoquantSepia2LibError(exit_code, error_msg, function_name)

    @handle_errors
    def lib_decode_error(self, error_code: int) -> str:
        c_error_string = ctypes.create_string_buffer(64)

        internal_error_code = self.dll.SEPIA2_LIB_DecodeError(ctypes.c_int(error_code),
                                                              c_error_string)
        if internal_error_code == 0:
            return c_error_string.value.decode(self.str_encoding)

        # Try to decode error code
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
        c_version_string = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_LIB_GetVersion(c_version_string)
        self.check_error(error_code, "SEPIA2_LIB_GetVersion")

        return c_version_string.value.decode(self.str_encoding)

    @handle_errors
    def lib_is_running_on_wine(self) -> bool:
        c_is_running_on_wine = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_LIB_IsRunningOnWine(ctypes.byref(c_is_running_on_wine))
        self.check_error(error_code, "SEPIA2_LIB_IsRunningOnWine")

        return bool(c_is_running_on_wine.value)

    @handle_errors
    def usb_open_device(self, device_id: int) -> (str, str):
        c_product_model = ctypes.create_string_buffer(32)
        c_serial_num = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_USB_OpenDevice(ctypes.c_int(device_id),
                                                    ctypes.byref(c_product_model),
                                                    ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_USB_OpenDevice")

        return c_product_model.value.decode(self.str_encoding), \
            c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def usb_open_get_ser_num_and_close(self, device_id: int) -> (str, str):
        c_product_model = ctypes.create_string_buffer(32)
        c_serial_num = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_USB_OpenGetSerNumAndClose(ctypes.c_int(device_id),
                                                               ctypes.byref(c_product_model),
                                                               ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_USB_OpenGetSerNumAndClose")

        return c_product_model.value.decode(self.str_encoding), \
            c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def usb_get_str_descriptor(self, device_id: int) -> str:
        c_descriptor = ctypes.create_string_buffer(255)

        error_code = self.dll.SEPIA2_USB_GetStrDescriptor(ctypes.c_int(device_id),
                                                          ctypes.byref(c_descriptor))
        self.check_error(error_code, "SEPIA2_USB_GetStrDescriptor")

        return c_descriptor.value.decode(self.str_encoding)

    @handle_errors
    def usb_close_device(self, device_id: int) -> None:
        error_code = self.dll.SEPIA2_USB_CloseDevice(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_USB_CloseDevice")

    @handle_errors
    def fwr_decode_err_phase_name(self, phase_error: int) -> str:
        c_error_string = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_FWR_DecodeErrPhaseName(ctypes.c_int(phase_error),
                                                            ctypes.byref(c_error_string))
        self.check_error(error_code, "SEPIA2_FWR_DecodeErrPhaseName")

        return c_error_string.value.decode(self.str_encoding)

    @handle_errors
    def fwr_get_version(self, device_id: int) -> str:
        c_fw_version = ctypes.create_string_buffer(8)

        error_code = self.dll.SEPIA2_FWR_GetVersion(ctypes.c_int(device_id),
                                                    ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_FWR_GetVersion")

        return c_fw_version.value.decode(self.str_encoding)

    @handle_errors
    def fwr_get_last_error(self, device_id: int) -> (int, int, int, int, str):
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
    def fwr_get_working_mode(self, device_id: int) -> int:
        c_mode = ctypes.c_int()

        error_code = self.dll.SEPIA2_FWR_GetWorkingMode(ctypes.c_int(device_id),
                                                        ctypes.byref(c_mode))
        self.check_error(error_code, "SEPIA2_FWR_GetWorkingMode")

        return c_mode.value

    @handle_errors
    def fwr_set_working_mode(self, device_id: int, mode: int) -> None:
        error_code = self.dll.SEPIA2_FWR_SetWorkingMode(ctypes.c_int(device_id), ctypes.c_int(mode))
        self.check_error(error_code, "SEPIA2_FWR_SetWorkingMode")

    @handle_errors
    def fwr_roll_back_to_permanent_values(self, device_id: int) -> None:
        error_code = self.dll.SEPIA2_FWR_RollBackToPermanentValues(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_RollBackToPermanentValues")

    @handle_errors
    def fwr_store_as_permanent_values(self, device_id: int) -> None:
        error_code = self.dll.SEPIA2_FWR_StoreAsPermanentValues(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_StoreAsPermanentValues")

    @handle_errors
    def fwr_get_module_map(self, device_id: int, perform_restart: bool) -> int:
        c_module_count = ctypes.c_int()

        error_code = self.dll.SEPIA2_FWR_GetModuleMap(ctypes.c_int(device_id),
                                                      ctypes.c_int(int(perform_restart)),
                                                      ctypes.byref(c_module_count))
        self.check_error(error_code, "SEPIA2_FWR_GetModuleMap")

        return c_module_count.value

    @handle_errors
    def fwr_get_module_info_by_map_id(self, device_id: int, map_id: int) -> (int, bool, bool, bool):
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
    def fwr_get_uptime_info_by_map_idx(self, device_id: int, map_id: int) -> (int, int, int):
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
        error_code = self.dll.SEPIA2_FWR_FreeModuleMap(ctypes.c_int(device_id))
        self.check_error(error_code, "SEPIA2_FWR_FreeModuleMap")

    @handle_errors
    def com_decode_module_type(self, module_type: int) -> str:
        c_module_type_str = ctypes.create_string_buffer(55)

        error_code = self.dll.SEPIA2_COM_DecodeModuleType(ctypes.c_int(module_type),
                                                          ctypes.byref(c_module_type_str))
        self.check_error(error_code, "SEPIA2_COM_DecodeModuleType")

        return c_module_type_str.value.decode(self.str_encoding)

    @handle_errors
    def com_decode_module_type_abbr(self, module_type: int) -> str:
        c_module_type_abbr = ctypes.create_string_buffer(4)

        error_code = self.dll.SEPIA2_COM_DecodeModuleTypeAbbr(ctypes.c_int(module_type),
                                                              ctypes.byref(c_module_type_abbr))
        self.check_error(error_code, "SEPIA2_COM_DecodeModuleTypeAbbr")

        return c_module_type_abbr.value.decode(self.str_encoding)

    @handle_errors
    def com_get_module_type(self, device_id: int, slot_id: int, get_primary: bool) -> int:
        c_module_type = ctypes.c_int()

        error_code = self.dll.SEPIA2_COM_GetModuleType(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.c_int(get_primary),
                                                       ctypes.byref(c_module_type))
        self.check_error(error_code, "SEPIA2_COM_GetModuleType")

        return c_module_type.value

    @handle_errors
    def com_has_secondary_module(self, device_id: int, slot_id: int) -> bool:
        c_has_secondary = ctypes.c_int()

        error_code = self.dll.SEPIA2_COM_HasSecondaryModule(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_has_secondary))
        self.check_error(error_code, "SEPIA2_COM_HasSecondaryModule")

        return bool(c_has_secondary.value)

    @handle_errors
    def com_get_serial_number(self, device_id: int, slot_id: int, get_primary: bool) -> str:
        c_serial_num = ctypes.create_string_buffer(12)

        error_code = self.dll.SEPIA2_COM_GetSerialNumber(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(get_primary),
                                                         ctypes.byref(c_serial_num))
        self.check_error(error_code, "SEPIA2_COM_GetSerialNumber")

        return c_serial_num.value.decode(self.str_encoding)

    @handle_errors
    def com_get_supplementary_infos(self, device_id: int, slot_id: int, get_primary: bool) \
            -> (str, datetime.datetime, str, str):
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
    def com_get_preset_info(self, device_id: int, slot_id: int, get_primary: bool,
                            preset_nr: PicoquantSepia2Preset) -> (bool, str):
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
        error_code = self.dll.SEPIA2_COM_RecallPreset(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      ctypes.c_int(get_primary),
                                                      ctypes.c_int(preset_nr))
        self.check_error(error_code, "SEPIA2_COM_RecallPreset")

    @handle_errors
    def com_save_as_preset(self, device_id: int, slot_id: int, get_primary: bool,
                          preset_nr: PicoquantSepia2Preset, preset_memo: str) -> None:
        c_preset_memo = ctypes.create_string_buffer(preset_memo)

        error_code = self.dll.SEPIA2_COM_SaveAsPreset(ctypes.c_int(device_id),
                                                      ctypes.c_int(slot_id),
                                                      ctypes.c_int(get_primary),
                                                      ctypes.c_int(preset_nr),
                                                      c_preset_memo)
        self.check_error(error_code, "SEPIA2_COM_SaveAsPreset")

    @handle_errors
    def com_is_writable_module(self, device_id: int, slot_id: int, get_primary: bool) -> bool:
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
        c_dcl_filename = ctypes.create_string_buffer(dcl_filename)

        error_code = self.dll.SEPIA2_COM_UpdateModuleData(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(set_primary),
                                                          ctypes.byref(c_dcl_filename))
        self.check_error(error_code, "SEPIA2_COM_UpdateModuleData")

    @handle_errors
    def scm_get_power_and_laser_leds(self, device_id: int, slot_id: int) -> (bool, bool):
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
        c_is_locked = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SCM_GetLaserLocked(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_is_locked))
        self.check_error(error_code, "SEPIA2_SCM_GetLaserLocked")

        return bool(c_is_locked.value)

    @handle_errors
    def scm_get_laser_soft_lock(self, device_id: int, slot_id: int) -> bool:
        c_is_soft_locked = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SCM_GetLaserSoftLock(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_is_soft_locked))
        self.check_error(error_code, "SEPIA2_SCM_GetLaserSoftLock")

        return bool(c_is_soft_locked.value)

    @handle_errors
    def scm_set_laser_soft_lock(self, device_id: int, slot_id: int, soft_locked: bool) -> None:
        error_code = self.dll.SEPIA2_SCM_SetLaserSoftLock(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_ubyte(soft_locked))
        self.check_error(error_code, "SEPIA2_SCM_SetLaserSoftLock")

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
    def som_decode_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> str:
        c_freq_trig_mode_str = ctypes.create_string_buffer(32)

        error_code = self.dll.SEPIA2_SOM_DecodeFreqTrigMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq_trig_mode),
                                                            ctypes.byref(c_freq_trig_mode_str))
        self.check_error(error_code, "SEPIA2_SOM_DecodeFreqTrigMode")

        return c_freq_trig_mode_str.value.decode(self.str_encoding)

    @handle_errors
    def som_get_freq_trig_mode(self, device_id: int, slot_id: int) -> int:
        c_freq_trig_mode = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOM_GetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_freq_trig_mode))
        self.check_error(error_code, "SEPIA2_SOM_GetFreqTrigMode")

        return c_freq_trig_mode.value

    @handle_errors
    def som_set_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> None:
        error_code = self.dll.SEPIA2_SOM_SetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(freq_trig_mode))
        self.check_error(error_code, "SEPIA2_SOM_SetFreqTrigMode")

    @handle_errors
    def som_get_trigger_range(self, device_id: int, slot_id: int) -> (int, int):
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
        c_trig_level = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOM_GetTriggerLevel(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_trig_level))
        self.check_error(error_code, "SEPIA2_SOM_GetTriggerLevel")

        return c_trig_level.value

    @handle_errors
    def som_set_trigger_level(self, device_id: int, slot_id: int, trig_level: int) -> None:
        error_code = self.dll.SEPIA2_SOM_SetTriggerLevel(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(trig_level))
        self.check_error(error_code, "SEPIA2_SOM_SetTriggerLevel")

    @handle_errors
    def som_get_burst_values(self, device_id: int, slot_id: int) -> None:
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
        error_code = self.dll.SEPIA2_SOM_SetBurstValues(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.c_ubyte(divider),
                                                        ctypes.c_ubyte(pre_sync),
                                                        ctypes.c_ubyte(mask_sync))
        self.check_error(error_code, "SEPIA2_SOM_SetBurstValues")

    @handle_errors
    def som_get_burst_length_array(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int):
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
        if (array_len := len(burst_lengths)) != 8:
            raise ValueError(f"Invalid array size ({array_len}). Expected 8 channels.")

        error_code = self.dll.SEPIA2_SOM_SetBurstLengthArray(ctypes.c_int(device_id),
                                                             ctypes.c_int(slot_id),
                                                             *[ctypes.c_long(bl)
                                                               for bl in burst_lengths])
        self.check_error(error_code, "SEPIA2_SOM_SetBurstLengthArray")

    @handle_errors
    def som_get_out_n_sync_enable(self, device_id: int, slot_id: int) -> (int, int, bool):
        c_out_enable = ctypes.c_ubyte()
        c_sync_enable = ctypes.c_ubyte()
        c_sync_inverse = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOM_GetOutNSyncEnable(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.byref(c_out_enable),
                                                           ctypes.byref(c_sync_enable),
                                                           ctypes.byref(c_sync_inverse))
        self.check_error(error_code, "SEPIA2_SOM_GetOutNSyncEnable")

        return c_out_enable.value, c_sync_enable.value, bool(c_sync_inverse.value)

    @handle_errors
    def som_set_out_n_sync_enable(self, device_id: int, slot_id: int, out_enable: int, sync_enable: int,
                              sync_inverse: bool) -> None:
        error_code = self.dll.SEPIA2_SOM_SetOutNSyncEnable(ctypes.c_int(device_id),
                                                           ctypes.c_int(slot_id),
                                                           ctypes.c_ubyte(out_enable),
                                                           ctypes.c_ubyte(sync_enable),
                                                           ctypes.c_ubyte(sync_inverse))
        self.check_error(error_code, "SEPIA2_SOM_SetOutNSyncEnable")

    @handle_errors
    def som_decode_aux_in_sequencer_ctrl(self, aux_in_ctrl: int) -> str:
        c_sequencer_ctrl = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_SOM_DecodeAUXINSequencerCtrl(ctypes.c_int(aux_in_ctrl),
                                                                  ctypes.byref(c_sequencer_ctrl))
        self.check_error(error_code, "SEPIA2_SOM_DecodeAUXINSequencerCtrl")

        return c_sequencer_ctrl.value.decode(self.str_encoding)

    @handle_errors
    def som_get_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int) -> (bool, int):
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
        error_code = self.dll.SEPIA2_SOM_SetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                               ctypes.c_int(slot_id),
                                                               ctypes.c_ubyte(aux_out_ctrl),
                                                               ctypes.c_ubyte(aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOM_SetAUXIOSequencerCtrl")

    @handle_errors
    def somd_decode_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int) -> str:
        c_freq_trig_mode_str = ctypes.create_string_buffer(32)

        error_code = self.dll.SEPIA2_SOM_DecodeFreqTrigMode(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_int(freq_trig_mode),
                                                            ctypes.byref(c_freq_trig_mode_str))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeFreqTrigMode")

        return c_freq_trig_mode_str.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_freq_trig_mode(self, device_id: int, slot_id: int) -> (int, bool):
        c_freq_trig_mode = ctypes.c_int()
        c_synchronize = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOM_GetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_freq_trig_mode),
                                                         ctypes.byref(c_synchronize))
        self.check_error(error_code, "SEPIA2_SOMD_GetFreqTrigMode")

        return c_freq_trig_mode.value, bool(c_synchronize)

    @handle_errors
    def somd_set_freq_trig_mode(self, device_id: int, slot_id: int, freq_trig_mode: int,
                                synchronize: bool) -> None:
        error_code = self.dll.SEPIA2_SOM_SetFreqTrigMode(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_int(freq_trig_mode),
                                                         ctypes.c_ubyte(synchronize))
        self.check_error(error_code, "SEPIA2_SOMD_SetFreqTrigMode")

    @handle_errors
    def somd_get_trigger_range(self, device_id: int, slot_id: int) -> (int, int):
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
        c_trig_level = ctypes.c_int()

        error_code = self.dll.SEPIA2_SOMD_GetTriggerLevel(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.byref(c_trig_level))
        self.check_error(error_code, "SEPIA2_SOMD_GetTriggerLevel")

        return c_trig_level.value

    @handle_errors
    def somd_set_trigger_level(self, device_id: int, slot_id: int, trig_level: int) -> None:
        error_code = self.dll.SEPIA2_SOMD_SetTriggerLevel(ctypes.c_int(device_id),
                                                          ctypes.c_int(slot_id),
                                                          ctypes.c_int(trig_level))
        self.check_error(error_code, "SEPIA2_SOMD_SetTriggerLevel")

    @handle_errors
    def get_burst_values(self, device_id: int, slot_id: int) -> (int, int, int):
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
    def set_burst_values(self, device_id: int, slot_id: int, divider: int,
                         pre_sync: int, sync_mask: int) -> None:
        error_code = self.dll.SEPIA2_SOMD_SetBurstValues(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.c_ushort(divider),
                                                         ctypes.c_ubyte(pre_sync),
                                                         ctypes.c_ubyte(sync_mask))
        self.check_error(error_code, "SEPIA2_SOMD_SetBurstValues")

    @handle_errors
    def somd_get_burst_length_array(self, device_id: int, slot_id: int) \
            -> (int, int, int, int, int, int, int, int):
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
        if (array_len := len(burst_lengths)) != 8:
            raise ValueError(f"Invalid array size ({array_len}). Expected 8 channels.")

        error_code = self.dll.SEPIA2_SOMD_SetBurstLengthArray(ctypes.c_int(device_id),
                                                              ctypes.c_int(slot_id),
                                                              *[ctypes.c_long(bl)
                                                                for bl in burst_lengths])
        self.check_error(error_code, "SEPIA2_SOMD_SetBurstLengthArray")

    @handle_errors
    def somd_get_out_n_sync_enable(self, device_id: int, slot_id: int) -> (int, int, bool):
        c_out_enable = ctypes.c_ubyte()
        c_sync_enable = ctypes.c_ubyte()
        c_sync_inverse = ctypes.c_ubyte()

        error_code = self.dll.SEPIA2_SOMD_GetOutNSyncEnable(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.byref(c_out_enable),
                                                            ctypes.byref(c_sync_enable),
                                                            ctypes.byref(c_sync_inverse))
        self.check_error(error_code, "SEPIA2_SOMD_GetOutNSyncEnable")

        return c_out_enable.value, c_sync_enable.value, bool(c_sync_inverse.value)

    @handle_errors
    def somd_set_out_n_sync_enable(self, device_id: int, slot_id: int, out_enable: int,
                                   sync_enable: int, sync_inverse: bool) -> None:
        error_code = self.dll.SEPIA2_SOMD_SetOutNSyncEnable(ctypes.c_int(device_id),
                                                            ctypes.c_int(slot_id),
                                                            ctypes.c_ubyte(out_enable),
                                                            ctypes.c_ubyte(sync_enable),
                                                            ctypes.c_ubyte(sync_inverse))
        self.check_error(error_code, "SEPIA2_SOMD_SetOutNSyncEnable")

    @handle_errors
    def somd_decode_aux_in_sequencer_ctrl(self, aux_in_ctrl: int) -> str:
        c_sequencer_ctrl = ctypes.create_string_buffer(24)

        error_code = self.dll.SEPIA2_SOMD_DecodeAUXINSequencerCtrl(ctypes.c_int(aux_in_ctrl),
                                                                   ctypes.byref(c_sequencer_ctrl))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeAUXINSequencerCtrl")

        return c_sequencer_ctrl.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_aux_io_sequencer_ctrl(self, device_id: int, slot_id: int) -> (bool, int):
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
        error_code = self.dll.SEPIA2_SOMD_SetAUXIOSequencerCtrl(ctypes.c_int(device_id),
                                                                ctypes.c_int(slot_id),
                                                                ctypes.c_ubyte(aux_out_ctrl),
                                                                ctypes.c_ubyte(aux_in_ctrl))
        self.check_error(error_code, "SEPIA2_SOMD_SetAUXIOSequencerCtrl")

    @handle_errors
    def somd_get_seq_output_infos(self, device_id: int, slot_id: int, seq_output_id: int) \
            -> (bool, bool, int, bool, float, int):
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
    def somd_synchronize_now(self, device_id: int, slot_id: int) -> None:
        error_code = self.dll.SEPIA2_SOMD_SynchronizeNow(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id))
        self.check_error(error_code, "SEPIA2_SOMD_SynchronizeNow")

    @handle_errors
    def somd_decode_module_state(self, state: int) -> str:
        c_status_text = ctypes.create_string_buffer(95)

        error_code = self.dll.SEPIA2_SOMD_DecodeModuleState(ctypes.c_ushort(state),
                                                            ctypes.byref(c_status_text))
        self.check_error(error_code, "SEPIA2_SOMD_DecodeModuleState")

        return c_status_text.value.decode(self.str_encoding)

    @handle_errors
    def somd_get_status_error(self, device_id: int, slot_id: int) -> (int, int):
        c_state = ctypes.c_ushort()
        c_error_code = ctypes.c_short()

        error_code = self.dll.SEPIA2_SOMD_GetStatusError(ctypes.c_int(device_id),
                                                         ctypes.c_int(slot_id),
                                                         ctypes.byref(c_state),
                                                         ctypes.byref(c_error_code))
        self.check_error(error_code, "SEPIA2_SOMD_GetStatusError")

        return c_state.value, c_error_code.value

    @handle_errors
    def somd_get_trig_sync_freq(self, device_id: int, slot_id: int) -> (bool, int):
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
        c_coarse_delay_step = ctypes.c_double()
        c_fine_delay_steps = ctypes.c_byte()

        error_code = self.dll.SEPIA2_SOMD_GetDelayUnits(ctypes.c_int(device_id),
                                                        ctypes.c_int(slot_id),
                                                        ctypes.byref(c_coarse_delay_step),
                                                        ctypes.byref(c_fine_delay_steps))
        self.check_error(error_code, "SEPIA2_SOMD_GetDelayUnits")

        return c_coarse_delay_step.value, c_fine_delay_steps.value

    @handle_errors
    def somd_get_fw_version(self, device_id: int, slot_id: int) -> (int, int, int):
        c_fw_version = ctypes.c_ulong()

        error_code = self.dll.SEPIA2_SOMD_GetFWVersion(ctypes.c_int(device_id),
                                                       ctypes.c_int(slot_id),
                                                       ctypes.byref(c_fw_version))
        self.check_error(error_code, "SEPIA2_SOMD_GetFWVersion")

        fw_version_bytes = c_fw_version.value.to_bytes(4)

        # major, minor, build
        return fw_version_bytes[0], fw_version_bytes[1], int.from_bytes(fw_version_bytes[2:])

    @handle_errors
    def somd_get_hw_params(self, device_id: int, slot_id: int) \
            -> ((int, int, int), (int, int, int, int), int):
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

    # Missing functions (since not documented):
    #  SEPIA2_SOMD_FWReadPage
    #  SEPIA2_SOMD_FWWritePage
    #  SEPIA2_SOMD_Calibrate

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
