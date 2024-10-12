#!/usr/bin/env python3
"""
Quick and dirty helper to read/write VISA compatible SCPI commands to Magnova (Batronix oscilloscope).

Note: add udev rule to allow libusb (pyvisa) access to device
```bash
   ╭─foo@host /etc/udev/rules.d
   ╰─$ cat 95-batronix-magnova.rules

   # Batronix: idVendor==0x19b2 | Magnova: idProduct=0x0030
   ACTION=="add", SUBSYSTEMS=="usb", ATTRS{idVendor}=="19b2", ATTRS{idProduct}=="0030", MODE="660", GROUP="users"
```

Note: ensure user belongs to group "users"
```bash
   ╭─foo@host ~/pytronix
   ╰─$ groups
   foo dialout cdrom sudo users docker
```
"""

import argparse
import json
import os
import pickle
import urllib.parse
import urllib.request
from typing import Dict

import pyvisa
import pyvisa_py as _pyvisa_py
from pyvisa import Resource  # noqa
from pyvisa import constants

pyvisa_py = _pyvisa_py


def device_tcp_url(my_ip_address: str, default_tcp_scpi_port: int) -> str:
    return f"TCPIP::{my_ip_address}::{default_tcp_scpi_port}::SOCKET"


def device_usb_url(id_vendor: int, id_product: int, my_serial_nr: str) -> str:
    return f"USB::0x{id_vendor:x}::0x{id_product:x}::{my_serial_nr}::INSTR"


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
            help="known scpi commands (from file)",
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

    def parse(self) -> argparse.Namespace:
        self.args: argparse.Namespace = self.parser.parse_args()

        if self.args.command == "device":
            usb_url = device_usb_url(self.id_vendor, self.id_product, self.my_serial_nr)
            self.args.url = usb_url if not hasattr(self.args, "url") else self.args.url

        return self.args


def interpret_device_args(args: argparse.Namespace):
    print(f"device: {args.url}")
    rm = pyvisa.ResourceManager("@py")

    try:
        x: Resource = rm.open_resource(
            args.url,
            access_mode=constants.AccessModes.exclusive_lock,
            open_timeout=1)

        x.write_termination = "\n"
        x.read_termination = "\n"

        if args.read:
            # examples:
            # - "*IDN"
            # - "MEASurement:VPPReshoot:REMove"
            # - "DIGItal1:STATe"
            print(x.query(f"{args.read}?"))  # noqa
        elif args.write:
            # examples:
            # - ":single"
            # - ":run"
            # - ":stop"
            # - "DIGItal1:STATe OFF"
            print(x.write(args.write))  # noqa

    except ValueError as e:
        print(f"error: {e}")


def nested_json_from_delimited_items(items: str):
    tree = {}
    for item in json.loads(items):
        t = tree
        for part in item.split(':'):
            t = t.setdefault(part, {})
    return tree


def print_tree_level(dct, level=0):
    for key, value in dct.items():
        print(
            "   " * (level - 1),
            "-> " if level else "",
            key,
            sep="")
        print_tree_level(value, level + 1)


def interpret_rest_args(args: argparse.Namespace):
    source_url = f"http://{args.address}:{args.port}/{args.dir}"
    current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tmp/")

    request = urllib.request.Request(source_url, headers={"Accept": "text/html"})
    with urllib.request.urlopen(request) as data:
        tree = nested_json_from_delimited_items(data.read())
        print_tree_level(tree)
        if hasattr(args, "outfile"):
            dest_out_file_path = os.path.join(current_path, args.outfile)
            with open(dest_out_file_path, 'wb') as out_file:
                print(f"storing {source_url} -> {dest_out_file_path} ...")
                pickle.dump(tree, out_file)
                print(f"stored scpi-def to {out_file.name}")


def load_commands_from_file(file_path_name: str) -> Dict:
    with open(file_path_name, 'rb') as in_file:
        print(f"loading commands from {file_path_name} ...")
        tree = pickle.load(in_file)
        return tree


def interpret_commands_args(args: argparse.Namespace):
    if args.list:
        current_path = os.path.dirname(os.path.abspath(__file__))
        in_file_path = os.path.join(current_path, args.infile)
        if not os.path.isfile(in_file_path):
            print(f"error: {in_file_path} does not exist, fetch with \"rest -o\" first")
            return
        tree = load_commands_from_file(str(in_file_path))
        print_tree_level(tree)


def main():
    cli_args = CliArgs().parse()

    if not cli_args.command:
        print("error: no command specified")

    [cmd(cli_args) for name, cmd in [
        ("device", interpret_device_args),
        ("rest", interpret_rest_args),
        ("commands", interpret_commands_args),
    ] if name == cli_args.command]


if __name__ == "__main__":
    main()
