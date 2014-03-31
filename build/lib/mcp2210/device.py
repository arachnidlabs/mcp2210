import hid
from mcp2210 import commands
import time


class CommandException(Exception):
    """Thrown when the MCP2210 returns an error status code."""

    def __init__(self, code):
        super(CommandException, self).__init__("Got error code from device: 0x%.2x" % code)


class GPIOSettings(object):
    """Encapsulates settings for GPIO pins - direction or status."""

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
    """Property decorator that facilitates writing properties for values from a remote device.

    Arguments:
      name: The field name to use on the local object to store the cached property.
      get_command: A function that returns the remote value of the property.
      set_command: A function that accepts a new value for the property and sets it remotely.
      field_name: The name of the field to retrieve from the response message to get operations.
    """

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
    """Represents data stored in the MCP2210 EEPROM."""

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
    """MCP2210 device interface.

    Usage:
        >>> dev = MCP2210(my_vid, my_pid)
        >>> dev.transfer("data")

    Advanced usage:
        >>> dev.manufacturer_name = "Foobar Industries Ltd"
        >>> print dev.manufacturer_name
        Foobar Industries Ltd

        >>> dev.product_name = "Foobinator 1.0"
        >>> print dev.product_name
        Foobinator 1.0

        >>> settings = dev.boot_chip_settings
        >>> settings.pin_designations[0] = 0x01  # GPIO 0 to chip select
        >>> dev.boot_chip_settings = settings  # Settings are updated on property assignment

    See the MCP2210 datasheet (http://ww1.microchip.com/downloads/en/DeviceDoc/22288A.pdf) for full details
    on available commands and arguments.
    """
    def __init__(self, vid, pid):
        """Constructor.

        Arguments:
          vid: Vendor ID
          pid: Product ID
        """
        self.hid = hid.device()
        self.hid.open(vid, pid)
        self.gpio_direction = GPIOSettings(self, commands.GetGPIODirectionCommand, commands.SetGPIODirectionCommand)
        self.gpio = GPIOSettings(self, commands.GetGPIOValueCommand, commands.SetGPIOValueCommand)
        self.eeprom = EEPROMData(self)
        self.cancel_transfer()

    def sendCommand(self, command):
        """Sends a Command object to the MCP2210 and returns its response.

        Arguments:
            A commands.Command instance

        Returns:
            A commands.Response instance, or raises a CommandException on error.
        """
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
    manufacturer_name.__doc__ = "Sets and gets the MCP2210 USB manufacturer name"

    product_name = remote_property(
        '_product_name',
        commands.GetUSBProductCommand,
        commands.SetUSBProductCommand,
        'string')
    product_name.__doc__ = "Sets and gets the MCP2210 USB product name"

    boot_chip_settings = remote_property(
        '_boot_chip_settings',
        commands.GetBootChipSettingsCommand,
        commands.SetBootChipSettingsCommand,
        'settings')
    boot_chip_settings.__doc__ = "Sets and gets boot time chip settings such as GPIO assignments"

    chip_settings = remote_property(
        '_chip_settings',
        commands.GetChipSettingsCommand,
        commands.SetChipSettingsCommand,
        'settings')
    chip_settings.__doc__ = "Sets and gets current chip settings such as GPIO assignments"

    boot_transfer_settings = remote_property(
        '_boot_transfer_settings',
        commands.GetBootSPISettingsCommand,
        commands.SetBootSPISettingsCommand,
        'settings')
    boot_transfer_settings.__doc__ = "Sets and gets boot time transfer settings such as data rate"

    transfer_settings = remote_property(
        '_transfer_settings',
        commands.GetSPISettingsCommand,
        commands.SetSPISettingsCommand,
        'settings')
    transfer_settings.__doc__ = "Sets and gets current transfer settings such as data rate"

    boot_usb_settings = remote_property(
        '_boot_usb_settings',
        commands.GetBootUSBSettingsCommand,
        commands.SetBootUSBSettingsCommand,
        'settings')
    boot_usb_settings.__doc__ = "Sets and gets boot time USB settings such as VID and PID"

    def authenticate(self, password):
        """Authenticates against a password-protected MCP2210.

        Arguments:
            password: The password to use.
        """
        self.sendCommand(commands.SendPasswordCommand(password))

    def transfer(self, data):
        """Transfers data over SPI.

        Arguments:
            data: The data to transfer.

        Returns:
            The data returned by the SPI device.
        """
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
        """Cancels any ongoing transfers."""
        self.sendCommand(commands.CancelTransferCommand())
