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

import pyvisa_py as _pyvisa_py
from pyvisa import Resource  # noqa

from pygnova.cli_args import CliArgs
from pygnova.instrument import get_instrument_from_url
from pygnova.instrument_url import url_from_str, RestUrl
from pygnova.known_commands import (
    print_nested_json_tree, KnownCommandsFileReader, strip_args_from_cmd, KnownCommandsRestReader,
)

pyvisa_py = _pyvisa_py


def interpret_device_command(arg_parser: CliArgs) -> int:
    args = arg_parser.args

    if not args.get and not args.set:
        arg_parser.device_parser.print_help()
        return -1

    print(f"device: {args.url}")
    command = args.get if args.get else args.set

    if not args.nocheck:
        try:
            cmd_reader = KnownCommandsFileReader(args.datadir, args.commandsfile)
            cmd_reader.load_commands()
            if not cmd_reader.is_known_command(command):
                print(f"error: no such {command=}")
                return -1
        except FileNotFoundError as e:
            print(f"error: {e}")
            return -1

    try:
        with get_instrument_from_url(args.url) as instrument:
            cmd = strip_args_from_cmd(command)
            if args.get:
                if cmd != command:
                    print(f"warning: stripped command from={command} to={cmd} ")
                instrument.read(cmd)
            elif args.set:
                instrument.write(command)
            else:
                print("error: no command specified")
    except ValueError as e:
        print(f"error: {e}")
        return -1
    except Exception as e:
        print(f"error: {e}")
        return -1

    return 0


def interpret_commands_command(arg_parser: CliArgs) -> int:
    args = arg_parser.args

    if args.list:
        commands_file = arg_parser.get_commands_file_path()
        if not os.path.isfile(commands_file):
            print(f"error: {commands_file} does not exist, fetch with \"rest -o\" first")
            return -1
        cmd_reader = KnownCommandsFileReader(args.datadir, args.commandsfile)
        cmd_reader.load_commands()
        print_nested_json_tree(cmd_reader.commands)
        return 0

    elif args.get:
        url = url_from_str(args.url)
        if type(url) is not RestUrl:
            arg_parser.commands_parser.print_help()
            return -1
        with KnownCommandsRestReader(url) as cmd_reader:
            commands_tree = cmd_reader.load_known_commands()
            if commands_tree is not None:
                print_nested_json_tree(commands_tree)
                if hasattr(args, "commandsfile"):
                    cmd_writer = KnownCommandsFileReader(args.datadir, args.commandsfile)
                    cmd_writer.commands = commands_tree
                    print(f"storing {cmd_reader.source_url} -> {cmd_writer.file_path} ...")
                    cmd_writer.store_commands()
            else:
                return -1
    else:
        arg_parser.commands_parser.print_help()
        return -1


def main() -> int:
    arg_parser = CliArgs()
    cli_args = arg_parser.parse()

    known_commands = [
        ("device", interpret_device_command),
        ("commands", interpret_commands_command),
    ]

    if cli_args.command not in [cmd for cmd, _impl in known_commands]:
        arg_parser.parser.print_help()
        return -1

    return [impl(arg_parser) for name, impl in known_commands if name == cli_args.command][0]


if __name__ == "__main__":
    main()
