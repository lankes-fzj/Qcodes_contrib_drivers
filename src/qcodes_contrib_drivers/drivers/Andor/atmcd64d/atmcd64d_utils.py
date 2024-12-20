import enum

__all__ = ["Atmcd64dError", "Atmcd64dLibError", "Atmcd64dExitCodes", "Atmcd64dAcquisitionModes",
           "Atmcd64dReadModes", "Atmcd64dShutterTypes", "Atmcd64dShutterModes",
           "Atmcd64dTriggerModes", "TEMPERATURE_IGNORE_ERRORS"]

class Atmcd64dError(Exception):
    pass


class Atmcd64dLibError(Atmcd64dError):
    """Exceptions occurring in `Atmcd64dLib`.
    
    Args:
        error_code (optional): Return code of library function
        error_message (optional): Error message belonging to `error_code`
        function_name (optional): Function causing the error
    """

    def __init__(self, error_code: int = None, error_message: str = None,
                 function_name: str = None):
        self.error_message = error_message
        self.function_name = function_name

        # Convert error_code to enum if possible
        try:
            self.error_code = Atmcd64dExitCodes(error_code)
        except ValueError:
            self.error_code = int(error_code)

        # Create exception message based on available information
        if self.function_name:
            msg = f"Library function '{self.function_name}' "
        else:
            msg = "A library function "
        if self.error_code:
            if isinstance(error_code, Atmcd64dExitCodes):
                msg += f"failed with {self.error_code.value} ({self.error_code.name})"
            else:
                msg += f"failed with {int(self.error_code)}"
        else:
            msg += "failed unexpectedly"
        if self.error_message:
            msg += f": {self.error_message}"

        super().__init__(msg)


class Atmcd64dExitCodes(enum.IntEnum):
    DRV_ERROR_CODES = 20001
    DRV_SUCCESS = 20002
    DRV_VXDNOTINSTALLED = 20003
    DRV_ERROR_SCAN = 20004
    DRV_ERROR_CHECK_SUM = 20005
    DRV_ERROR_FILELOAD = 20006
    DRV_UNKNOWN_FUNCTION = 20007
    DRV_ERROR_VXD_INIT = 20008
    DRV_ERROR_ADDRESS = 20009
    DRV_ERROR_PAGELOCK = 20010
    DRV_ERROR_PAGEUNLOCK = 20011
    DRV_ERROR_BOARDTEST = 20012
    DRV_ERROR_ACK = 20013
    DRV_ERROR_UP_FIFO = 20014
    DRV_ERROR_PATTERN = 20015
    DRV_ACQUISITION_ERRORS = 20017
    DRV_ACQ_BUFFER = 20018
    DRV_ACQ_DOWNFIFO_FULL = 20019
    DRV_PROC_UNKONWN_INSTRUCTION = 20020
    DRV_ILLEGAL_OP_CODE = 20021
    DRV_KINETIC_TIME_NOT_MET = 20022
    DRV_ACCUM_TIME_NOT_MET = 20023
    DRV_NO_NEW_DATA = 20024
    DRV_PCI_DMA_FAIL = 20025
    DRV_SPOOLERROR = 20026
    DRV_SPOOLSETUPERROR = 20027
    DRV_FILESIZELIMITERROR = 20028
    DRV_ERROR_FILESAVE = 20029
    DRV_TEMPERATURE_CODES = 20033
    DRV_TEMPERATURE_OFF = 20034
    DRV_TEMPERATURE_NOT_STABILIZED = 20035
    DRV_TEMPERATURE_STABILIZED = 20036
    DRV_TEMPERATURE_NOT_REACHED = 20037
    DRV_TEMPERATURE_OUT_RANGE = 20038
    DRV_TEMPERATURE_NOT_SUPPORTED = 20039
    DRV_TEMPERATURE_DRIFT = 20040
    DRV_TEMP_CODES = 20033
    DRV_TEMP_OFF = 20034
    DRV_TEMP_NOT_STABILIZED = 20035
    DRV_TEMP_STABILIZED = 20036
    DRV_TEMP_NOT_REACHED = 20037
    DRV_TEMP_OUT_RANGE = 20038
    DRV_TEMP_NOT_SUPPORTED = 20039
    DRV_TEMP_DRIFT = 20040
    DRV_GENERAL_ERRORS = 20049
    DRV_INVALID_AUX = 20050
    DRV_COF_NOTLOADED = 20051
    DRV_FPGAPROG = 20052
    DRV_FLEXERROR = 20053
    DRV_GPIBERROR = 20054
    DRV_EEPROMVERSIONERROR = 20055
    DRV_DATATYPE = 20064
    DRV_DRIVER_ERRORS = 20065
    DRV_P1INVALID = 20066
    DRV_P2INVALID = 20067
    DRV_P3INVALID = 20068
    DRV_P4INVALID = 20069
    DRV_INIERROR = 20070
    DRV_COFERROR = 20071
    DRV_ACQUIRING = 20072
    DRV_IDLE = 20073
    DRV_TEMPCYCLE = 20074
    DRV_NOT_INITIALIZED = 20075
    DRV_P5INVALID = 20076
    DRV_P6INVALID = 20077
    DRV_INVALID_MODE = 20078
    DRV_INVALID_FILTER = 20079
    DRV_I2CERRORS = 20080
    DRV_I2CDEVNOTFOUND = 20081
    DRV_I2CTIMEOUT = 20082
    DRV_P7INVALID = 20083
    DRV_P8INVALID = 20084
    DRV_P9INVALID = 20085
    DRV_P10INVALID = 20086
    DRV_P11INVALID = 20087
    DRV_USBERROR = 20089
    DRV_IOCERROR = 20090
    DRV_VRMVERSIONERROR = 20091
    DRV_GATESTEPERROR = 20092
    DRV_USB_INTERRUPT_ENDPOINT_ERROR = 20093
    DRV_RANDOM_TRACK_ERROR = 20094
    DRV_INVALID_TRIGGER_MODE = 20095
    DRV_LOAD_FIRMWARE_ERROR = 20096
    DRV_DIVIDE_BY_ZERO_ERROR = 20097
    DRV_INVALID_RINGEXPOSURES = 20098
    DRV_BINNING_ERROR = 20099
    DRV_INVALID_AMPLIFIER = 20100
    DRV_INVALID_COUNTCONVERT_MODE = 20101
    DRV_ERROR_NOCAMERA = 20990
    DRV_NOT_SUPPORTED = 20991
    DRV_NOT_AVAILABLE = 20992
    DRV_ERROR_MAP = 20115
    DRV_ERROR_UNMAP = 20116
    DRV_ERROR_MDL = 20117
    DRV_ERROR_UNMDL = 20118
    DRV_ERROR_BUFFSIZE = 20119
    DRV_ERROR_NOHANDLE = 20121
    DRV_GATING_NOT_AVAILABLE = 20130
    DRV_FPGA_VOLTAGE_ERROR = 20131
    DRV_OW_CMD_FAIL = 20150
    DRV_OWMEMORY_BAD_ADDR = 20151
    DRV_OWCMD_NOT_AVAILABLE = 20152
    DRV_OW_NO_SLAVES = 20153
    DRV_OW_NOT_INITIALIZED = 20154
    DRV_OW_ERROR_SLAVE_NUM = 20155
    DRV_MSTIMINGS_ERROR = 20156
    DRV_OA_NULL_ERROR = 20173
    DRV_OA_PARSE_DTD_ERROR = 20174
    DRV_OA_DTD_VALIDATE_ERROR = 20175
    DRV_OA_FILE_ACCESS_ERROR = 20176
    DRV_OA_FILE_DOES_NOT_EXIST = 20177
    DRV_OA_XML_INVALID_OR_NOT_FOUND_ERROR = 20178
    DRV_OA_PRESET_FILE_NOT_LOADED = 20179
    DRV_OA_USER_FILE_NOT_LOADED = 20180
    DRV_OA_PRESET_AND_USER_FILE_NOT_LOADED = 20181
    DRV_OA_INVALID_FILE = 20182
    DRV_OA_FILE_HAS_BEEN_MODIFIED = 20183
    DRV_OA_BUFFER_FULL = 20184
    DRV_OA_INVALID_STRING_LENGTH = 20185
    DRV_OA_INVALID_CHARS_IN_NAME = 20186
    DRV_OA_INVALID_NAMING = 20187
    DRV_OA_GET_CAMERA_ERROR = 20188
    DRV_OA_MODE_ALREADY_EXISTS = 20189
    DRV_OA_STRINGS_NOT_EQUAL = 20190
    DRV_OA_NO_USER_DATA = 20191
    DRV_OA_VALUE_NOT_SUPPORTED = 20192
    DRV_OA_MODE_DOES_NOT_EXIST = 20193
    DRV_OA_CAMERA_NOT_SUPPORTED = 20194
    DRV_OA_FAILED_TO_GET_MODE = 20195
    DRV_PROCESSING_FAILED = 20211


class Atmcd64dAcquisitionModes(enum.IntEnum):
    SINGLE_SCAN = 1
    ACCUMULATE = 2
    KINETICS = 3
    FAST_KINETICS = 4
    RUN_UNTIL_ABORT = 5


class Atmcd64dReadModes(enum.IntEnum):
    FULL_VERTICAL_BINNING = 0
    MULTI_TRACK = 1
    RANDOM_TRACK = 2
    SINGLE_TRACK = 3
    IMAGE = 4


class Atmcd64dShutterTypes(enum.IntEnum):
    LOW = 0
    HIGH = 1


class Atmcd64dShutterModes(enum.IntEnum):
    FULLY_AUTO = 0
    PERMANENTLY_OPEN = 1
    PERMANENTLY_CLOSED = 2
    OPEN_FOR_FVB = 4
    OPEN_FOR_ANY = 5


class Atmcd64dTriggerModes(enum.IntEnum):
    INTERNAL = 0
    EXTERNAL = 1
    EXTERNAL_START = 6
    EXTERNAL_EXPOSURE = 7  # bulb
    EXTERNAL_FVB_EM = 9  # only valid for EM Newton models in FVB mode
    SOFTWARE_TRIGGER = 10
    EXTERNAL_CHARGE_SHIFT = 12


TEMPERATURE_IGNORE_ERRORS = (Atmcd64dExitCodes.DRV_TEMP_NOT_STABILIZED,
                             Atmcd64dExitCodes.DRV_TEMP_STABILIZED,
                             Atmcd64dExitCodes.DRV_TEMP_NOT_REACHED)
