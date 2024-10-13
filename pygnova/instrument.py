import pyvisa_py as _pyvisa_py
from pyvisa import Resource, ResourceManager  # noqa
from pyvisa import constants

pyvisa_py = _pyvisa_py


class Instrument:

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
            print(f"closing device {self.instrument_url}")
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
        print(f"-> write={self.instrument.write(cmd)} command=\"{cmd}\"")
        print(f"<- recv=\"{self.instrument.read()}\"")

    def write(self, command: str):
        print(f"-> write={self.instrument.write(command)} command=\"{command}\"")
