__all__ = ["APT_ERROR_CODES"]


APT_ERROR_CODES = {
    10000: "UNKNOWN_ERR (10000): An unknown Server error has occurred.",
    10001: "INTERNAL_ERR (10001): A Server internal error has occurred.",
    10002: "FAILED (10002): A Server call has failed.",
    10003: "INVALIDPARAM_ERR (10003): An attempt has been made to pass a parameter that is invalid or out of range. In the case of motor commands, this error may occur when a move is requested that exceeds the stage travel or exceeds the calibration data",
    10004: "SETTINGSNOTFOUND (10004): An attempt has been made to save or load control parameters to the registry (using the SaveParamSet or LoadParamSet methods) when the unit serial number has not been specified.",
    10005: "DLLNOTINITIALISED (10005): APT DLL not intialised.",
    10050: "DISKACCESS_ERR (10050): An error has occurred whilst accessing the disk. Check that the drive is not full, missing or corrupted.",
    10051: "ETHERNET_ERR (10051): An error has occurred with the ethernet connections or the windows sockets.",
    10052: "REGISTRY_ERR (10052): An error has occurred whilst accessing the registry.",
    10053: "MEMORY_ERR (10053): An internal memory allocation error or de-allocation error has occurred.",
    10054: "COM_ERR (10054): An error has occurred with the COM system. Restart the program.",
    10055: "USB_ERR (10055): An error has occurred with the USB communications.",
    10056: "NOTTHORLABSDEVICE_ERR (10056): Not Thorlabs USB device error.",
    10100: "SERIALNUMUNKNOWN_ERR (10100): A serial number has been specified that is unknown to the server.",
    10101: "DUPLICATESERIALNUM_ERR (10101): A duplicate serial number has been detected. Serial numbers are required to be unique.",
    10102: "DUPLICATEDEVICEIDENT_ERR (10102): A duplicate device identifier has been detected.",
    10103: "INVALIDMSGSRC_ERR (10103): An invalid message source has been detected.",
    10104: "UNKNOWNMSGIDENT_ERR (10104): A message has been received with an unknown identifier.",
    10105: "UNKNOWNHWTYPE_ERR (10105): An unknown hardware identifier has been encountered.",
    10106: "INVALIDSERIALNUM_ERR (10106): An invalid serial number has been detected.",
    10107: "INVALIDMSGDEST_ERR (10107): An invalid message destination ident has been detected.",
    10108: "INVALIDINDEX_ERR (10108): An invalid index parameter has been passed.",
    10109: "CTRLCOMMSDISABLED_ERR (10109): A software call has been made to a control which is not currently communicating with any hardware. This may be because the control has not been started or may be due to an incorrect serial number or missing hardware.",
    10110: "HWRESPONSE_ERR (10110): A notification or response message has been received from a hardware unit. This may be indicate a hardware fault or that an illegal command/parameter has been sent to the hardware.",
    10111: "HWTIMEOUT_ERR (10111): A time out has occurred while waiting for a hardware unit to respond. This may be due to communications problems or a hardware fault.",
    10112: "INCORRECTVERSION_ERR (10112): Some functions are applicable only to later versions of embedded code. This error is returned when a software call is made to a unit with an incompatible version of embedded code installed.",
    10115: "INCOMPATIBLEHARDWARE_ERR (10115): Some functions are applicable only to later versions of hardware. This error is returned when a software call is made to an incompatible version of hardware.",
    10116: "OLDVERSION_ERR (10116): Older version of embedded code that can still be used",
    10150: "NOSTAGEAXISINFO (10150): The GetStageAxisInfo method has been called when no stage has been assigned.",
    10151: "CALIBTABLE_ERR (10151): An internal error has occurred when using an encoded stage.",
    10152: "ENCCALIB_ERR (10152): An internal error has occurred when using an encoded stage.",
    10153: "ENCNOTPRESENT_ERR (10153): A software call applicable only to encoded stages has been made to a non-encoded stage.",
    10154: "MOTORNOTHOMED_ERR (10154): motor not homed error",
    10155: "MOTORDISABLED_ERR (10155): motor disabled error",
    10156: "PMDMSG_ERR (10156): PMD processor message error",
    10157: "PMDREADONLY_ERR (10157): PMD based controller stage parameter 'read only' error",
    10200: "PIEZOLED_ERR (10200): Encoder not present error",
    10250: "NANOTRAKLED_ERR (10250): Encoder not present error",
    10251: "NANOTRAKCLOSEDLOOP_ERR (10251): Closed loop error - closed loop selected with no feedback signal",
    10252: "NANOTRAKPOWER_ERR (10252): Power supply error - voltage rails out of limits"
}