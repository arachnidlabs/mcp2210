#!/usr/bin/env python

from distutils.core import setup

setup(name="mcp2210",
      version="0.1.3",
      description="Python interface for the MCP2210 USB-SPI interface",
      author="Nick Johnson",
      author_email="nick@arachnidlabs.com",
      url="https://github.com/arachnidlabs/mcp2210/",
      packages=["mcp2210"],
      requires=["hidapi"])
