import argparse
import os
from argparse import _SubParsersAction  # noqa

from pygnova.instrument_url import RestUrl, VisaTcpUrl, VisaUsbUrl


class CliArgs:

    def __init__(self) -> None:
        self.id_vendor: int = 0x19B2  # Batronix
        self.id_product: int = 0x0030  # Magnova
        self.serial_nr: str = "001065"  # my device SN
        self.ip_address: str = "192.168.2.24"  # my device IP-address
        self.default_tcp_scpi_port: int = 5025
        self.default_tcp_rest_port: int = 8080

        self.default_rest_url: RestUrl = RestUrl(self.ip_address, self.default_tcp_rest_port)
        self.default_tcp_url: VisaTcpUrl = VisaTcpUrl(self.ip_address, self.default_tcp_scpi_port)
        self.default_usb_url: VisaUsbUrl = VisaUsbUrl(self.id_vendor, self.id_product, self.serial_nr)
        self.commands_pickle_name = "scpi-commands.pickle"
        self.commands_default_artifact_path = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../tmp"))

        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self._add_global_args(self.parser)

        commands_parser = self.parser.add_subparsers(dest='command', title="command")
        self.device_parser = self._declare_device_args(commands_parser)
        self.commands_parser = self._declare_commands_args(commands_parser)

        self.args: argparse.Namespace | None = None

    def _add_global_args(self, parser: argparse.ArgumentParser) -> None:
        grp = parser.add_argument_group(title="connection args")
        grp = grp.add_mutually_exclusive_group()
        grp.add_argument(
            "-u", "--url",
            help=f"USBTMC/USB URL; use - for default (default: {self.default_usb_url.to_str_url()})",
            default=argparse.SUPPRESS,
            const=self.default_usb_url.to_str_url(),
            dest="url",
            nargs="?",
            type=lambda u, default=self.default_usb_url.to_str_url(), clazz=VisaUsbUrl, msg="invalid USBTMC URL":
            default if u == "-"
            else clazz.from_str_url(u).to_str_url() if clazz.from_str_url(u) is not None
            else parser.error(msg)
        )
        grp.add_argument(
            "-t", "--tcp",
            help=f"SCPI-RAW/TCP URL; use - for default (default: {self.default_tcp_url.to_str_url()})",
            default=argparse.SUPPRESS,
            const=self.default_tcp_url.to_str_url(),
            dest="url",
            nargs="?",
            type=lambda u, default=self.default_tcp_url.to_str_url(), clazz=VisaTcpUrl, msg="invalid SCPI-Raw URL":
            default if u == "-"
            else clazz.from_str_url(u).to_str_url() if clazz.from_str_url(u) is not None
            else parser.error(msg)
        )
        grp.add_argument(
            "-r", "--rest",
            help=f"REST/http URL; use - for default (default: {self.default_rest_url.to_str_url()})",
            default=argparse.SUPPRESS,
            const=self.default_rest_url.to_str_url(),
            dest="url",
            nargs="?",
            type=lambda u, default=self.default_rest_url.to_str_url(), clazz=RestUrl, msg="invalid REST API URL":
            default if u == "-"
            else clazz.from_str_url(u).to_str_url() if clazz.from_str_url(u) is not None
            else parser.error(msg)
        )

        grp = parser.add_argument_group(title="known commands file")
        grp.add_argument(
            "-c", "--commandsfile",
            help="known SCPI commands file",
            default=self.commands_pickle_name,
            type=str)
        grp.add_argument(
            "-d", "--datadir",
            help="artifacts directory",
            default=self.commands_default_artifact_path,
            type=str)
        grp.add_argument(
            "-n", "--nocheck",
            help="skip command check with commands file",
            action="store_true")

    def _declare_device_args(self, action: _SubParsersAction) -> argparse.ArgumentParser:
        parser = action.add_parser(
            "device",
            help="device commands",
            description="Send read/write commands to device.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        grp = parser.add_argument_group(title="device command option")
        sub_grp = grp.add_mutually_exclusive_group()
        sub_grp.add_argument(
            "-g", "--get",
            help="request/read argument from device",
            type=str)
        sub_grp.add_argument(
            "-s", "--set",
            help="send/write argument to device",
            type=str)
        return parser

    def _declare_commands_args(self, action: _SubParsersAction) -> argparse.ArgumentParser:
        parser = action.add_parser(
            "commands",
            help="known device commands",
            description="known device commands",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        grp = parser.add_argument_group(title="commands command options")
        grp = grp.add_mutually_exclusive_group()
        grp.add_argument(
            "-l", "--list",
            help="List all known commands from file; requires no connection URL",
            action="store_true")
        grp.add_argument(
            "-g", "--get",
            help="Fetch all known commands from device via REST API (only with rest URL: \"--rest http://<addr>:8080/scpi\")",
            action="store_true")

        return parser

    def get_commands_file_path(self) -> str:
        return os.path.realpath(os.path.join(self.args.datadir, self.args.commandsfile))

    def parse(self) -> argparse.Namespace:
        self.args: argparse.Namespace = self.parser.parse_args()

        usb_url = VisaUsbUrl(self.id_vendor, self.id_product, self.serial_nr).to_str_url()
        self.args.url = usb_url if not hasattr(self.args, "url") else self.args.url

        return self.args
