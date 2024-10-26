import abc
from typing import Dict, Union

import pyvisa_py as _pyvisa_py
import requests
from pyvisa import Resource, ResourceManager  # noqa
from pyvisa import constants

from pygnova.instrument_url import VisaUsbUrl, VisaTcpUrl, RestUrl, url_from_str

pyvisa_py = _pyvisa_py


class ScpiReadWrite(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def read(self, command: str) -> str | Dict:
        """
        The trailing '?' is appended automatically and shall be omitted in the command string.

        Command examples:
        - read identification: "*IDN"
        - read CH1 scale:      "CHANnel1:SCALe" or "chan1:scal"
        """
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, command: str) -> int | Dict:
        """
        Optional space-separated arguments may be contained in the command string.

        Command examples:
        - write CH1 scale to 500mV: "CHANnel1:SCALe 0.5" or "chan1:scal 500m"
        """
        raise NotImplementedError


class VisaInstrument(ScpiReadWrite):

    def __init__(self,
                 url: Union[VisaTcpUrl, VisaUsbUrl],
                 write_termination: str = "\n",
                 read_termination: str = "\n",
                 rw_timeout: int = 1000,
                 resource_manager_class: str | None = "@py"):
        self.instrument_url: str = url.to_str_url()
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

    def read(self, command: str) -> str:
        cmd = f"{command}?"
        print(f"-> write={self.instrument.write(cmd)} command=\"{cmd}\"")  # noqa
        response = self.instrument.read()  # noqa
        print(f"<- recv=\"{response}\"")
        return response

    def write(self, command: str) -> int:
        response = self.instrument.write(command)  # noqa
        print(f"-> write={response} command=\"{command}\"")  # noqa
        return response


class RestInstrument(ScpiReadWrite):

    def __init__(self, instrument_url: RestUrl):
        self.instrument_url = instrument_url.to_str_url()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def read(self, command: str) -> Dict:
        print(f"-> write={command}")
        response = requests.post(self.instrument_url, json=f"{command}?").json()
        print(f"<- recv={response}")
        return response

    def write(self, command: str) -> Dict:
        print(f"-> write={command}")
        return requests.post(self.instrument_url, json=f"{command}").json()


def get_instrument_from_url(url: str) -> RestInstrument | VisaInstrument | None:
    known_types = {
        RestUrl: RestInstrument,
        VisaUsbUrl: VisaInstrument,
        VisaTcpUrl: VisaInstrument,
        None: lambda _o: None}

    url_object = url_from_str(url)
    return known_types[type(url_object)](url_object)
