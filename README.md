mcp2210
=======

Python library for interfacing with the MCP2210 USB-SPI interface.

## Installation

    $ pip install mcp2210

or, clone this repository and install from source:

    $ git clone https://github.com/arachnidlabs/mcp2210.git
    $ cd mcp2210
    $ sudo setup.py install

## Usage

    >>> from mcp2210 import MCP2210
    >>> dev = MCP2210(my_vid, my_pid)
    >>> dev.transfer("data")

In addition to making transfers, device settings can be accessed and modified:

    >>> dev.manufacturer_name = "Foobar Industries Ltd"
    >>> print dev.manufacturer_name
    Foobar Industries Ltd
    
    >>> dev.product_name = "Foobinator 1.0"
    >>> print dev.product_name
    Foobinator 1.0
    
    >>> settings = dev.boot_chip_settings
    >>> settings.pin_designations[0] = 0x01  # GPIO 0 to chip select
    >>> dev.boot_chip_settings = settings  # Settings are updated on property assignment
    
    >>> spisettings = dev.boot_transfer_settings
    >>> spisettings.idle_cs = 0x01
    >>> spisettings.active_cs = 0x00  # Set pin 1 to go low on chip select
    >>> dev.boot_transfer_settings = spisettings

`chip_settings` and `boot_chip_settings` define basic settings such as GPIO pin assignments. `transfer_settings` and `boot_transfer_settings` define SPI settings such as data rate, chip select value, and inter-byte timings. `boot_usb_settings` defines USB configuration options like VID, PID, and power requirements. On boot, the MCP2210 copies `boot_transfer_settings` and `boot_chip_settings` into `transfer_settings` and `chip_settings` respectively.

All properties are cached when fetched, and updated on the device when set, so storing results to the chip requires an assignment, as in the above code, even when the arguments are mutable.

See the [MCP2210 datasheet](http://ww1.microchip.com/downloads/en/DeviceDoc/22288A.pdf) for full details on available commands and arguments.
