import re
from typing import Optional


class RestUrl:

    @staticmethod
    def from_str_url(url: str) -> Optional["RestUrl"]:
        matcher = re.compile(r"^http://([0-9a-zA-Z.]+):(\d+)/(\w+)$")
        m = matcher.match(url.lower())
        if m is not None and 3 == len(m.groups()):
            return RestUrl(m.group(1), int(f"{m.group(2)}", 10), m.group(3))
        return None

    def to_str_url(self) -> str:
        return f"{self.protocol}://{self.ip_address}:{self.tcp_port}/{self.path}"

    def __init__(self, ip_address: str, tcp_port: int = 8080, path: str = "scpi", protocol: str = "http"):
        self.protocol: str = protocol
        self.ip_address: str = ip_address
        self.tcp_port: int = tcp_port
        self.path: str = path


class VisaTcpUrl:

    @staticmethod
    def from_str_url(url: str) -> Optional["VisaTcpUrl"]:
        matcher = re.compile(r"^TCPIP::([0-9a-zA-Z.]+)::(\d+)::SOCKET$")
        m = matcher.match(url)
        if m is not None and 2 == len(m.groups()):
            return VisaTcpUrl(m.group(1), int(f"{m.group(2)}", 10))
        return None

    def to_str_url(self) -> str:
        return f"TCPIP::{self.ip_address}::{self.tcp_port}::SOCKET"

    def __init__(self, ip_address: str, tcp_port: int):
        self.ip_address: str = ip_address
        self.tcp_port: int = tcp_port


class VisaUsbUrl:

    @staticmethod
    def from_str_url(url: str) -> Optional["VisaUsbUrl"]:
        matcher = re.compile(r"^USB::0[xX]([0-9a-fA-F]+)::0[xX]([0-9a-fA-F]+)::(\w+)::INSTR$")
        m = matcher.match(url)
        if m is not None and 3 == len(m.groups()):
            return VisaUsbUrl(int(f"{m.group(1)}", 16), int(f"{m.group(2)}", 16), m.group(3))
        return None

    def to_str_url(self) -> str:
        return f"USB::0x{self.id_vendor:x}::0x{self.id_product:x}::{self.serial_nr}::INSTR"

    def __init__(self, id_vendor: int, id_product: int, serial_nr: str):
        self.id_vendor: int = id_vendor
        self.id_product: int = id_product
        self.serial_nr: str = serial_nr


def url_from_str(url: str) -> RestUrl | VisaUsbUrl | VisaTcpUrl | None:
    if RestUrl.from_str_url(url):
        return RestUrl.from_str_url(url)
    elif VisaTcpUrl.from_str_url(url):
        return VisaTcpUrl.from_str_url(url)
    elif VisaUsbUrl.from_str_url(url):
        return VisaUsbUrl.from_str_url(url)
    else:
        return None
