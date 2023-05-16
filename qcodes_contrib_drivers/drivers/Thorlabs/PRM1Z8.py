from qcodes import Instrument
from .APT import Thorlabs_APT, ThorlabsHWType


class Thorlabs_PRM1Z8(Instrument):
    """
    Instrument driver for the Thorlabs PRMZ1Z8 polarizer wheel.

    The instrument can be initialized with either a serial number or the
    device id from discovery results. If both are provided, the serial number
    is prioritized.

    Args:
        name: Instrument name.
        serial_number (optional): Serial number of the device.
        device_id (optional): Device id from APT discovery.
        dll_path (optional): Path of the APT.dll

    Attributes:
        apt: Thorlabs APT server.
        serial_number: Serial number of the polarizer wheel.
        model: Model description.
        version: Firmware version.
    """

    def __init__(self, name: str, *, serial_number: int = None,
                 device_id: int = 0, dll_path: str = None, **kwargs):
        super().__init__(name, **kwargs)

        # save APT server link
        self.apt = apt

        # Store serial number
        if serial_number is None:
            # Use device id to obtain serial number
            self.serial_number = self.apt.get_hw_serial_num_ex(ThorlabsHWType.PRM1Z8, device_id)
        else:
            # Use serial number from arguments
            self.serial_number = serial_number
        
        # initialization
        self.apt.init_hw_device(self.serial_number)
        self.model, self.version, _ = self.apt.get_hw_info(self.serial_number)

        # add parameters
        self.add_parameter('position',
                           get_cmd=self._get_position,
                           set_cmd=self._set_position,
                           unit=u"\u00b0",
                           label='Position')

        # print connect message
        self.connect_message()

    def close(self) -> None:
        """Closes the instruments ressources"""
        self.apt.close_hw_device(self.serial_number)
        super().close()

    # get methods
    def get_idn(self):
        return {'vendor': 'Thorlabs', 'model': self.model,
                'firmware': self.version, 'serial': self.serial_number}

    def _get_position(self):
        return self.apt.mot_get_position(self.serial_number)

    # set methods
    def _set_position(self, position):
        self.apt.mot_move_absolute_ex(self.serial_number, position, True)
