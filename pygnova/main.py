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
import os
import urllib.parse
import urllib.request

import pyvisa
import pyvisa_py as _pyvisa_py
from pyvisa import Resource  # noqa
from pyvisa import constants

from pygnova.cli_args import CliArgs
from pygnova.commands import load_commands_from_file, to_nested_json_from_delimited_items, print_nested_json_tree, store_to_file, is_known_command, command_from_cmd_with_args

pyvisa_py = _pyvisa_py


def interpret_device_args(args: argparse.Namespace) -> int:
    print(f"device: {args.url}")
    rm = pyvisa.ResourceManager("@py")

    # sanity check

    file_path_name = CliArgs.get_file_path_name(args.commandsfile)
    commands_tree = load_commands_from_file(file_path_name)
    command = args.read if args.read else args.write
    if not is_known_command(command, commands_tree):
        print(f"error: no such {command=}")
        return -1

    try:
        r: Resource = rm.open_resource(
            args.url,
            access_mode=constants.AccessModes.exclusive_lock,
            open_timeout=10
        )

        r.write_termination = "\n"
        r.read_termination = "\n"
        r.timeout = 1000

        if args.read:
            # examples:
            # - "*IDN"
            # - "MEASurement:VPPReshoot:REMove"
            # - "DIGItal1:STATe"
            # print(r.query(f"{args.read}?"))  # noqa
            cmd = command_from_cmd_with_args(args.read)
            if cmd != command:
                print(f"warning: stripped command from={command} to={cmd} ")
            print(r.write(f"{cmd}?"))  # noqa
            print(r.read())  # noqa
        elif args.write:
            # examples:
            # - ":single"
            # - ":run"
            # - ":stop"
            # - "DIGItal1:STATe OFF"
            print(r.write(args.write))  # noqa
        else:
            print("error: no command specified")
            r.close()
            return -1
        r.close()

    except ValueError as e:
        print(f"error: {e}")
        return -1


def interpret_rest_args(args: argparse.Namespace) -> int:
    source_url = f"http://{args.address}:{args.port}/{args.dir}"
    request = urllib.request.Request(source_url, headers={"Accept": "text/html"})

    with urllib.request.urlopen(request) as data:
        tree = to_nested_json_from_delimited_items(data.read())
        print_nested_json_tree(tree)
        if hasattr(args, "outfile"):
            file_path_name = CliArgs.get_file_path_name(args.outfile)
            print(f"storing {source_url} -> {file_path_name} ...")
            store_to_file(file_path_name, tree)

    return 0


def interpret_commands_args(args: argparse.Namespace) -> int:
    if args.list:
        current_path = os.path.dirname(os.path.abspath(__file__))
        in_file_path = os.path.join(current_path, args.infile)
        if not os.path.isfile(in_file_path):
            print(f"error: {in_file_path} does not exist, fetch with \"rest -o\" first")
            return -1
        tree = load_commands_from_file(str(in_file_path))
        print_nested_json_tree(tree)
    return 0


def main() -> int:
    cli_args = CliArgs().parse()

    if not cli_args.command:
        print("error: no command specified")

    return [cmd(cli_args) for name, cmd in [
        ("device", interpret_device_args),
        ("rest", interpret_rest_args),
        ("commands", interpret_commands_args),
    ] if name == cli_args.command][0]


if __name__ == "__main__":
    main()
