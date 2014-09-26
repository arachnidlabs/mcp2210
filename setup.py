#!/usr/bin/env python

from setuptools import setup

setup(name="mcp2210",
      version="0.1.4",
      description="Python interface for the MCP2210 USB-SPI interface",
      author="Nick Johnson",
      author_email="nick@arachnidlabs.com",
      url="https://github.com/arachnidlabs/mcp2210/",
      packages=["mcp2210"],
      install_requires=["hidapi>=0.7.99"])
