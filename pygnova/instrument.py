import urllib.error
import urllib.request
from typing import Any, Dict

import pyvisa_py as _pyvisa_py
from pyvisa import Resource, ResourceManager  # noqa
from pyvisa import constants

pyvisa_py = _pyvisa_py


class VisaInstrument:

    def __init__(self,
                 instrument_url: str,
                 write_termination: str = "\n",
                 read_termination: str = "\n",
                 rw_timeout: int = 1000,
                 resource_manager_class: str | None = "@py"):
        self.instrument_url: str | None = instrument_url
        self.resource_manager: ResourceManager = ResourceManager(resource_manager_class if resource_manager_class is not None else "")
        self.instrument: Resource | None = None
        self.write_termination: str = write_termination
        self.read_termination: str = read_termination
        self.rw_timeout: int = rw_timeout

    def __enter__(self):
        if self.instrument is None:
            print(f"opening device={self.instrument_url}")
            self.instrument: Resource = self.resource_manager.open_resource(
                self.instrument_url,
                access_mode=constants.AccessModes.exclusive_lock,
                open_timeout=10)
            self.instrument.write_termination = self.write_termination
            self.instrument.read_termination = self.read_termination
            self.instrument.timeout = self.rw_timeout
        else:
            print(f"warning: device already opened={self.instrument_url}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.instrument is not None:
            print(f"closing device={self.instrument_url}")
            self.instrument.close()
            self.instrument = None
        return False

    def read(self, command: str):
        """
        examples:
        - "*IDN"
        - "MEASurement:VPPReshoot:REMove"
        - "DIGItal1:STATe"

        :param command:
        :return:
        """
        cmd = f"{command}?"
        print(f"-> write={self.instrument.write(cmd)} command=\"{cmd}\"")  # noqa
        print(f"<- recv=\"{self.instrument.read()}\"")  # noqa

    def write(self, command: str):
        print(f"-> write={self.instrument.write(command)} command=\"{command}\"")  # noqa


class RestInstrument:
    def __init__(self, address: str, port: int, path: str, headers: Dict[str, str] | None = None):
        self.source_url = f"http://{address}:{port}/{path}"
        headers = {"Accept": "text/html"} if headers is None else headers
        self.request: urllib.request.Request = urllib.request.Request(self.source_url, headers=headers)
        self.open_context_manager: Any | None = None

    def __enter__(self):
        if self.open_context_manager is None:
            self.open_context_manager = urllib.request.urlopen(self.request)
        else:
            print(f"warning: device is already opened={self.source_url}")
        return self.open_context_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_context_manager is not None:
            print(f"closing device={self.source_url}")
            self.open_context_manager.close()
            self.open_context_manager = None
        return False
