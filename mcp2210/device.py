import hid
from mcp2210 import commands
import time

class CommandException(Exception):
    def __init__(self, code):
        super(CommandException, self).__init__("Got error code from device: 0x%.2x" % code)


class GPIOSettings(object):
    def __init__(self, device, get_command, set_command):
        self._device = device
        self._get_command = get_command
        self._set_command = set_command
        self._value = None

    @property
    def raw(self):
        if self._value is None:
            self._value = self._device.sendCommand(self._get_command()).gpio
        return self._value

    @raw.setter
    def raw(self, value):
        self._value = value
        self._device.sendCommand(self._set_command(value))

    def __getitem__(self, i):
        return (self.raw >> i) & 1

    def __setitem__(self, i, value):
        if value:
            self.raw |= 1 << i
        else:
            self.raw &= ~(1 << i)


def remote_property(name, get_command, set_command, field_name):
    def getter(self):
        try:
            return getattr(self, name)
        except AttributeError:
            value = getattr(self.sendCommand(get_command()), field_name)
            setattr(self, name, value)
            return value

    def setter(self, value):
        setattr(self, name, value)
        self.sendCommand(set_command(value))

    return property(getter, setter)


class EEPROMData(object):
    def __init__(self, device):
        self._device = device

    def __getitem__(self, key):
        if isinstance(key, slice):
            return ''.join(self[i] for i in range(*key.indices(255)))
        else:
            return chr(self._device.sendCommand(commands.ReadEEPROMCommand(key)).header.reserved)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            for i, j in enumerate(range(*key.indices(255))):
                self[j] = value[i]
        else:
            self._device.sendCommand(commands.WriteEEPROMCommand(key, ord(value)))


class MCP2210(object):
    def __init__(self, vid, pid):
        self.hid = hid.device(vid, pid)
        self.gpio_direction = GPIOSettings(self, commands.GetGPIODirectionCommand, commands.SetGPIODirectionCommand)
        self.gpio = GPIOSettings(self, commands.GetGPIOValueCommand, commands.SetGPIOValueCommand)
        self.eeprom = EEPROMData(self)
        self.cancel_transfer()

    def sendCommand(self, command):
        command_data = [ord(x) for x in buffer(command)]
        self.hid.write(command_data)
        response_data = ''.join(chr(x) for x in self.hid.read(64))
        response = command.RESPONSE.from_buffer_copy(response_data)
        if response.status != 0:
            raise CommandException(response.status)
        return response

    manufacturer_name = remote_property(
        '_manufacturer_name',
        commands.GetUSBManufacturerCommand,
        commands.SetUSBManufacturerCommand,
        'string')

    product_name = remote_property(
        '_product_name',
        commands.GetUSBProductCommand,
        commands.SetUSBProductCommand,
        'string')

    boot_chip_settings = remote_property(
        '_boot_chip_settings',
        commands.GetBootChipSettingsCommand,
        commands.SetBootChipSettingsCommand,
        'settings')

    chip_settings = remote_property(
        '_chip_settings',
        commands.GetChipSettingsCommand,
        commands.SetChipSettingsCommand,
        'settings')

    boot_transfer_settings = remote_property(
        '_boot_transfer_settings',
        commands.GetBootSPISettingsCommand,
        commands.SetBootSPISettingsCommand,
        'settings')

    transfer_settings = remote_property(
        '_transfer_settings',
        commands.GetSPISettingsCommand,
        commands.SetSPISettingsCommand,
        'settings')

    boot_usb_settings = remote_property(
        '_boot_usb_settings',
        commands.GetBootUSBSettingsCommand,
        commands.SetBootUSBSettingsCommand,
        'settings')

    def authenticate(self, password):
        self.sendCommand(commands.SendPasswordCommand(password))

    def transfer(self, data):
        settings = self.transfer_settings
        settings.spi_tx_size = len(data)
        self.transfer_settings = settings

        response = ''
        for i in range(0, len(data), 60):
            response += self.sendCommand(commands.SPITransferCommand(data[i:i + 60])).data
            time.sleep(0.01)

        while len(response) < len(data):
            response += self.sendCommand(commands.SPITransferCommand('')).data

        return ''.join(response)

    def cancel_transfer(self):
        self.sendCommand(commands.CancelTransferCommand())
