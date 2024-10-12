import argparse
import os

from pygnova.dev_url import device_usb_url, device_tcp_url


class CliArgs:
    def __init__(self) -> None:
        self.id_vendor: int = 0x19B2  # Batronix
        self.id_product: int = 0x0030  # Magnova

        self.my_serial_nr: str = "001065"  # my device SN
        self.my_ip_address: str = "192.168.2.29"  # my device IP-address

        self.default_tcp_scpi_port: int = 5025
        self.default_tcp_url: str = device_tcp_url(self.my_ip_address, self.default_tcp_scpi_port)
        self.default_usb_url: str = device_usb_url(self.id_vendor, self.id_product, self.my_serial_nr)

        self.commands_pickle_name = "../tmp/scpi-commands.pickle"

        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        sub_parsers = self.parser.add_subparsers(
            dest='command',
            title="command (required)",
            description="Run command with the loaded configuration.")

        # device commands

        subp = sub_parsers.add_parser(
            "device",
            help="device commands",
            description="Device connection URL (tcp/usb).",
            formatter_class=self.parser.formatter_class)

        sub_grp = subp.add_mutually_exclusive_group()
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

        sub_sub_grp = subp.add_argument_group(
            description="Request / Response arguments")
        sub_sub_grp.add_argument(
            "-c", "--commandsfile",
            help="known SCPI commands (from file)",
            default=self.commands_pickle_name,
            type=str)

        sub_sub_grp = sub_sub_grp.add_mutually_exclusive_group()
        sub_sub_grp.add_argument(
            "-r", "--read",
            help="request/read from device",
            type=str)
        sub_sub_grp.add_argument(
            "-w", "--write",
            help="send/write command (and value) to device",
            type=str)

        # rest commands

        subp = sub_parsers.add_parser(
            "rest",
            help="REST API",
            description="Device's REST API (TCP)",
            formatter_class=self.parser.formatter_class)

        sub_grp = subp.add_mutually_exclusive_group()
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
            "-o", "--outfile",
            help=f"store known commands to file (default: {self.commands_pickle_name})",
            const=self.commands_pickle_name,
            nargs="?",
            default=argparse.SUPPRESS,
            type=str)

        # commands' commands

        subp = sub_parsers.add_parser(
            "commands",
            help="known device commands",
            description="known device commands",
            formatter_class=self.parser.formatter_class)
        sub_grp = subp.add_mutually_exclusive_group()
        sub_grp.add_argument(
            "-i", "--infile",
            help="Commands file",
            default=self.commands_pickle_name,
            type=str)
        sub_grp.add_argument(
            "-l", "--list",
            help="List all known commands from file",
            action="store_true")

        self.args: argparse.Namespace | None = None

    @staticmethod
    def get_file_path_name(outfile: str) -> str:
        if not os.path.isabs(outfile):
            # assume relative to ./cli_args.py
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), outfile)
        else:
            return outfile

    def parse(self) -> argparse.Namespace:
        self.args: argparse.Namespace = self.parser.parse_args()

        if self.args.command == "device":
            usb_url = device_usb_url(self.id_vendor, self.id_product, self.my_serial_nr)
            self.args.url = usb_url if not hasattr(self.args, "url") else self.args.url

        return self.args
