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

import os
import urllib.parse
import urllib.request

import pyvisa_py as _pyvisa_py
from pyvisa import Resource  # noqa

from pygnova.cli_args import CliArgs
from pygnova.instrument import Instrument
from pygnova.known_commands import (
    load_commands_tree_from_file,
    nested_json_from_delimited_items,
    print_nested_json_tree,
    store_commands_tree_to_file,
    is_known_command,
    command_from_cmd_with_args
)

pyvisa_py = _pyvisa_py


def interpret_device_args(arg_parser: CliArgs) -> int:
    args = arg_parser.args

    if not args.read and not args.write:
        arg_parser.device_parser.print_help()
        return -1

    print(f"device: {args.url}")
    command = args.read if args.read else args.write

    # sanity check

    if not args.nocheck:
        commands_file = arg_parser.get_commandsfile_path()
        commands_tree = load_commands_tree_from_file(commands_file)
        if not is_known_command(command, commands_tree):
            print(f"error: no such {command=}")
            return -1

    try:
        with Instrument(args.url) as instrument:
            cmd = command_from_cmd_with_args(command)
            if args.read:
                if cmd != command:
                    print(f"warning: stripped command from={command} to={cmd} ")
                instrument.read(cmd)
            elif args.write:
                instrument.write(command)
            else:
                print("error: no command specified")
    except ValueError as e:
        print(f"error: {e}")
        return -1
    return 0


def interpret_rest_args(arg_parser: CliArgs) -> int:
    args = arg_parser.args
    source_url = f"http://{args.address}:{args.port}/{args.dir}"
    request = urllib.request.Request(source_url, headers={"Accept": "text/html"})

    with urllib.request.urlopen(request) as data:
        tree = nested_json_from_delimited_items(data.read())
        print_nested_json_tree(tree)
        if hasattr(args, "commandsfile"):
            commands_file = arg_parser.get_commandsfile_path()
            print(f"storing {source_url} -> {commands_file} ...")
            store_commands_tree_to_file(commands_file, tree)

    return 0


def interpret_commands_args(arg_parser: CliArgs) -> int:
    args = arg_parser.args
    if args.list:
        commands_file = arg_parser.get_commandsfile_path()
        if not os.path.isfile(commands_file):
            print(f"error: {commands_file} does not exist, fetch with \"rest -o\" first")
            return -1
        tree = load_commands_tree_from_file(str(commands_file))
        print_nested_json_tree(tree)
        return 0
    else:
        arg_parser.parser.print_help()
        return -1


def main() -> int:
    arg_parser = CliArgs()
    cli_args = arg_parser.parse()

    known_commands = [
        ("device", interpret_device_args),
        ("rest", interpret_rest_args),
        ("commands", interpret_commands_args),
    ]

    if cli_args.command not in [cmd for cmd, _func in known_commands]:
        arg_parser.parser.print_help()
        return -1

    return [implementation(arg_parser) for name, implementation in known_commands if name == cli_args.command][0]


if __name__ == "__main__":
    main()
