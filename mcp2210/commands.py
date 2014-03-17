from ctypes import Structure, c_ubyte, c_ushort, c_uint, c_char


class CommandHeader(Structure):
    _fields_ = [('command', c_ubyte),
                ('subcommand', c_ubyte),
                ('reserved_1', c_ubyte),
                ('reserved_2', c_ubyte)]


class ResponseHeader(Structure):
    _fields_ = [('command', c_ubyte),
                ('status', c_ubyte),
                ('subcommand', c_ubyte),
                ('reserved', c_ubyte)]


class Response(Structure):
    pass


class EmptyResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader)]


class Command(Structure):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__((self.COMMAND, self.SUBCOMMAND, 0x00, 0x00), *args, **kwargs)


class SetBootSettingsCommand(Command):
    COMMAND = 0x60
    RESPONSE = EmptyResponse


class ChipSettings(Structure):
    _fields_ = [('pin_designations', c_ubyte * 9),
                ('gpio_outputs', c_ushort),
                ('gpio_directions', c_ushort),
                ('other_settings', c_ubyte),
                ('access_control', c_ubyte),
                ('new_password', c_char * 8)]


class SetBootChipSettingsCommand(SetBootSettingsCommand):
    SUBCOMMAND = 0x20
    _fields_ = [('header', CommandHeader),
                ('settings', ChipSettings)]


class SPISettings(Structure):
    _fields_ = [('bit_rate', c_uint),
                ('idle_cs', c_ushort),
                ('active_cs', c_ushort),
                ('cs_data_delay', c_ushort),
                ('lb_cs_delay', c_ushort),
                ('interbyte_delay', c_ushort),
                ('spi_tx_size', c_ushort),
                ('spi_mode', c_ubyte)]


class SetBootSPISettingsCommand(SetBootSettingsCommand):
    SUBCOMMAND = 0x10
    _fields_ = [('header', CommandHeader),
                ('settings', SPISettings)]


class USBSettings(Structure):
    _fields_ = [('vid', c_ushort),
                ('pid', c_ushort),
                ('power_option', c_ubyte),
                ('current_request', c_ubyte)]


class SetBootUSBSettingsCommand(SetBootSettingsCommand):
    SUBCOMMAND = 0x30
    _fields_ = [('header', CommandHeader),
                ('settings', USBSettings)]


class SetUSBStringCommand(SetBootSettingsCommand):
    _fields_ = [('header', CommandHeader),
                ('str_len', c_ubyte),
                ('descriptor_id', c_ubyte),
                ('str', c_ubyte * 58)]

    def __init__(self, s):
        super(SetUSBStringCommand, self).__init__()
        self.descriptor_id = 0x03
        self.string = s

    @property
    def string(self):
        return ''.join(chr(x) for x in self.str[:self.str_len - 2]).decode('utf16')

    @string.setter
    def string(self, value):
        for i, x in enumerate((value + '\0').encode('utf16')):
            self.str[i] = ord(x)
        self.str_len = len(value) * 2 + 4


class SetUSBManufacturerCommand(SetUSBStringCommand):
    SUBCOMMAND = 0x50


class SetUSBProductCommand(SetUSBStringCommand):
    SUBCOMMAND = 0x40


class GetBootSettingsCommand(Command):
    COMMAND = 0x61


class GetChipSettingsResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader),
                ('settings', ChipSettings)]


class GetBootChipSettingsCommand(GetBootSettingsCommand):
    SUBCOMMAND = 0x20
    RESPONSE = GetChipSettingsResponse
    _fields_ = [('header', CommandHeader)]


class GetSPISettingsResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader),
                ('settings', SPISettings)]


class GetBootSPISettingsCommand(GetBootSettingsCommand):
    SUBCOMMAND = 0x10
    RESPONSE = GetSPISettingsResponse
    _fields_ = [('header', CommandHeader)]


class GetUSBSettingsResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader),
                ('reserved', c_ubyte * 8),
                ('vid', c_ushort),
                ('pid', c_ushort),
                ('reserved_2', c_ubyte * 13),
                ('power_option', c_ubyte),
                ('current_request', c_ubyte)]

    @property
    def settings(self):
        return USBSettings(self.vid, self.pid, self.power_option, self.current_request)


class GetBootUSBSettingsCommand(GetBootSettingsCommand):
    SUBCOMMAND = 0x30
    RESPONSE = GetUSBSettingsResponse
    _fields_ = [('header', CommandHeader)]


class GetUSBStringResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader),
                ('str_len', c_ubyte),
                ('descriptor_id', c_ubyte),
                ('str', c_ubyte * 58)]

    @property
    def string(self):
        return ''.join(chr(x) for x in self.str[:self.str_len - 2]).decode('utf16')


class GetUSBProductCommand(GetBootSettingsCommand):
    SUBCOMMAND = 0x40
    RESPONSE = GetUSBStringResponse
    _fields_ = [('header', CommandHeader)]


class GetUSBManufacturerCommand(GetBootSettingsCommand):
    SUBCOMMAND = 0x50
    RESPONSE = GetUSBStringResponse
    _fields_ = [('header', CommandHeader)]


class SendPasswordCommand(Command):
    COMMAND = 0x70
    SUBCOMMAND = 0x00
    RESPONSE = EmptyResponse
    _fields_ = [('header', CommandHeader),
                ('password', c_char * 8)]


class GetSPISettingsCommand(Command):
    COMMAND = 0x41
    SUBCOMMAND = 0x00
    RESPONSE = GetSPISettingsResponse
    _fields_ = [('header', CommandHeader)]


class SetSPISettingsCommand(Command):
    COMMAND = 0x40
    SUBCOMMAND = 0x00
    RESPONSE = EmptyResponse
    _fields_ = [('header', CommandHeader),
                ('settings', SPISettings)]


class GetChipSettingsCommand(Command):
    COMMAND = 0x20
    SUBCOMMAND = 0x00
    RESPONSE = GetChipSettingsResponse
    _fields_ = [('header', CommandHeader)]


class SetChipSettingsCommand(Command):
    COMMAND = 0x21
    SUBCOMMAND = 0x00
    RESPONSE = EmptyResponse
    _fields_ = [('header', CommandHeader),
                ('settings', ChipSettings)]


class GetGPIOResponse(Response):
    _anonymous_ = ['header']
    _fields_ = [('header', ResponseHeader),
                ('gpio', c_ushort)]


class GetGPIOCommand(Command):
    SUBCOMMAND = 0x00
    RESPONSE = GetGPIOResponse
    _fields_ = [('header', CommandHeader)]


class GetGPIODirectionCommand(GetGPIOCommand):
    COMMAND = 0x33


class SetGPIOCommand(Command):
    SUBCOMMAND = 0x00
    RESPONSE = EmptyResponse
    _fields_ = [('header', CommandHeader),
                ('gpio', c_ushort)]


class SetGPIODirectionCommand(SetGPIOCommand):
    COMMAND = 0x32


class GetGPIOValueCommand(GetGPIOCommand):
    COMMAND = 0x31


class SetGPIOValueCommand(SetGPIOCommand):
    COMMAND = 0x30


class ReadEEPROMResponse(Structure):
    _fields_ = [('command', c_ubyte),
                ('status', c_ubyte),
                ('address', c_ubyte),
                ('data', c_ubyte)]


class ReadEEPROMCommand(Structure):
    COMMAND = 0x50
    RESPONSE = ReadEEPROMResponse
    _fields_ = [('command', c_ubyte),
                ('address', c_ubyte),
                ('reserved', c_ubyte)]

    def __init__(self, address):
        super(ReadEEPROMCommand, self).__init__(self.COMMAND, address, 0x00)


class WriteEEPROMCommand(Structure):
    COMMAND = 0x51
    RESPONSE = EmptyResponse
    _fields_ = [('command', c_ubyte),
                ('address', c_ubyte),
                ('value', c_ubyte)]

    def __init__(self, address, value):
        super(WriteEEPROMCommand, self).__init__(self.COMMAND, address, value)


SPIBuffer = c_ubyte * 60


class SPITransferResponse(Structure):
    _fields_ = [('command', c_ubyte),
                ('status', c_ubyte),
                ('length', c_ubyte),
                ('engine_status', c_ubyte),
                ('_data', SPIBuffer)]

    @property
    def data(self):
        return ''.join(chr(x) for x in self._data[:self.length])


class SPITransferCommand(Structure):
    COMMAND = 0x42
    RESPONSE = SPITransferResponse
    _fields_ = [('command', c_ubyte),
                ('length', c_ubyte),
                ('reserved', c_ushort),
                ('data', SPIBuffer)]

    def __init__(self, data):
        data = SPIBuffer(*(ord(x) for x in data))
        super(SPITransferCommand, self).__init__(self.COMMAND, len(data), 0x0000, data)


class DeviceStatusResponse(Response):
    _fields_ = [('command', c_ubyte),
                ('status', c_ubyte),
                ('bus_release_status', c_ubyte),
                ('bus_owner', c_ubyte),
                ('password_attempts', c_ubyte),
                ('password_guessed', c_ubyte)]


class CancelTransferCommand(Command):
    COMMAND = 0x11
    SUBCOMMAND = 0x00
    RESPONSE = DeviceStatusResponse
    _fields_ = [('header', CommandHeader)]
