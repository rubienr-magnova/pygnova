import argparse
import os

from pygnova.instrument_url import device_usb_url, device_tcp_url


class CliArgs:
    commands_default_artifact_path = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../tmp"))

    def __init__(self) -> None:
        self.id_vendor: int = 0x19B2  # Batronix
        self.id_product: int = 0x0030  # Magnova

        self.my_serial_nr: str = "001065"  # my device SN
        self.my_ip_address: str = "192.168.2.29"  # my device IP-address

        self.default_tcp_scpi_port: int = 5025
        self.default_tcp_url: str = device_tcp_url(self.my_ip_address, self.default_tcp_scpi_port)
        self.default_usb_url: str = device_usb_url(self.id_vendor, self.id_product, self.my_serial_nr)

        self.commands_pickle_name = "scpi-commands.pickle"

        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        commands_parser = self.parser.add_subparsers(
            dest='command',
            title="command")

        # device commands

        self.device_parser = commands_parser.add_parser(
            "device",
            help="device commands",
            description="Device connection URL (TCP/USB).",
            formatter_class=self.parser.formatter_class)

        sub_grp = self.device_parser.add_mutually_exclusive_group()
        sub_grp.add_argument(
            "-t", "--tcpip",
            help=f"TCP URL (default: {self.default_tcp_url})",
            const=self.default_tcp_url,
            default=argparse.SUPPRESS,
            nargs="?",
            dest="url",
            type=str)
        sub_grp.add_argument(
            "-u", "--usbdev",
            help=f"USB URL (default: {self.default_usb_url})",
            const=self.default_usb_url,
            default=argparse.SUPPRESS,
            nargs="?",
            dest="url",
            type=str)

        sub_sub_grp = self.device_parser.add_argument_group(
            description="known commands:")
        sub_sub_grp.add_argument(
            "-c", "--commandsfile",
            help="known SCPI commands file",
            default=self.commands_pickle_name,
            type=str)
        sub_sub_grp.add_argument(
            "--datadir",
            help="artifacts directory",
            default=self.commands_default_artifact_path,
            type=str)
        sub_sub_grp.add_argument(
            "-n", "--nocheck",
            help="skip command check with commands file",
            action="store_true")

        sub_sub_grp = sub_grp.add_mutually_exclusive_group()
        sub_sub_grp.add_argument(
            "-r", "--read",
            help="request/read from device",
            type=str)
        sub_sub_grp.add_argument(
            "-w", "--write",
            help="send/write command (and value) to device",
            type=str)

        # rest commands

        self.rest_parser = commands_parser.add_parser(
            "rest",
            help="REST API",
            description="Device's REST API (TCP)",
            formatter_class=self.parser.formatter_class)

        sub_grp = self.rest_parser.add_mutually_exclusive_group()
        sub_grp.add_argument(
            "-a", "--address",
            help="TCP address",
            default="192.168.2.24",
            type=str)
        sub_grp.add_argument(
            "-p", "--port",
            help="TCP port",
            default=8080,
            type=int)
        sub_grp.add_argument(
            "-d", "--dir",
            help="scpi path",
            default="scpi",
            type=str)
        sub_grp.add_argument(
            "-c", "--commandsfile",
            help=f"store the retrieved commands to known-commands file if specified (default: {self.commands_pickle_name})",
            const=self.commands_pickle_name,
            nargs="?",
            default=argparse.SUPPRESS,
            type=str)
        sub_grp.add_argument(
            "--datadir",
            help="artifacts directory",
            default=self.commands_default_artifact_path,
            type=str)

        # commands' commands

        self.commands_parser = commands_parser.add_parser(
            "commands",
            help="known device commands",
            description="known device commands",
            formatter_class=self.parser.formatter_class)
        sub_grp = self.commands_parser.add_mutually_exclusive_group()
        sub_grp.add_argument(
            "-l", "--list",
            help="List all known commands from file",
            action="store_true")
        sub_grp.add_argument(
            "-c", "--commandsfile",
            help="commands file",
            default=self.commands_pickle_name,
            type=str)
        sub_grp.add_argument(
            "--datadir",
            help="artifacts directory",
            default=self.commands_default_artifact_path,
            type=str)

        self.args: argparse.Namespace | None = None

    def get_commandsfile_path(self) -> str:
        return os.path.realpath(os.path.join(self.args.datadir, self.args.commandsfile))

    def parse(self) -> argparse.Namespace:
        self.args: argparse.Namespace = self.parser.parse_args()

        if self.args.command == "device":
            usb_url = device_usb_url(self.id_vendor, self.id_product, self.my_serial_nr)
            self.args.url = usb_url if not hasattr(self.args, "url") else self.args.url

        return self.args
