import json
import os.path
import pickle
import re
import urllib.error
import urllib.request
from typing import Dict, Optional

from pygnova.instrument_url import RestUrl

CommandsDict = Dict[str, "CommandsDict"]


class KnownCommandsRestReader:

    def __init__(self, url: RestUrl, headers: Dict[str, str] | None = None):
        self._source_url: str = url.to_str_url()
        headers = {"Accept": "text/html"} if headers is None else headers
        self.request: urllib.request.Request = urllib.request.Request(self.source_url, headers=headers)
        self._open_context_manager = None

    @property
    def source_url(self):
        return self._source_url

    def __enter__(self):
        if self._open_context_manager is None:
            self._open_context_manager = urllib.request.urlopen(self.request)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._open_context_manager is not None:
            print(f"closing reader={self.source_url}")
            self._open_context_manager.close()
            self._open_context_manager = None
        return False

    def load_known_commands(self) -> CommandsDict:
        try:
            return self._nested_json_from_delimited_items(self._open_context_manager.read())
        except urllib.error.HTTPError as e:
            print(f"error: {e}")

    @staticmethod
    def _nested_json_from_delimited_items(items: str, delimiter=":") -> CommandsDict:
        tree: CommandsDict = {}
        for item in json.loads(items):
            t = tree
            for part in item.split(delimiter):
                t = t.setdefault(part, {})
        return tree


def print_nested_json_tree(tree: CommandsDict):
    return _traverse_nested_json_tree({"*": tree}, prefix="")


def _traverse_nested_json_tree(tree: CommandsDict, prefix: str = ""):
    for idx, (key, value) in enumerate(tree.items()):
        is_last = idx + 1 == len(tree.items())
        is_first = idx == 0
        has_children = len(value) != 0

        line = prefix
        if is_first and is_last and not has_children:
            line += "╰─" + key
        elif is_first and is_last and has_children:
            line += key + "─╮"
        elif has_children and not is_last:
            line += "├─╮" + key
        elif has_children and is_last:
            line += "╰─╮" + key
        elif is_last:
            line += "╰•" + key
        else:
            line += "├•" + key
        print(line)

        _traverse_nested_json_tree(tree[key], prefix=prefix + ("  " if is_last else "│ "))


def strip_args_from_cmd(command_with_optional_args: str) -> str:
    r = re.compile(r"[? ]+.*$")
    return r.sub("", command_with_optional_args)  # without args or "?"


class KnownCommandsFileReader:

    def __init__(self, path_name: str, file_name: str):
        self.path_name: str = path_name
        self.file_name: str = file_name
        self._commands_tree: Optional[CommandsDict] = None

    @property
    def file_path(self):
        return os.path.relpath(os.path.join(self.path_name, self.file_name))

    def load_commands(self) -> Optional[CommandsDict]:
        try:
            with open(self.file_path, 'rb') as in_file:
                print(f"loading commands from file=\"{self.file_path}\" ...")
                self._commands_tree = pickle.load(in_file)
                return self._commands_tree
        except Exception:  # noqa
            return None

    @property
    def commands(self) -> Optional[dict]:
        return self._commands_tree

    @commands.setter
    def commands(self, new_commands_tree: CommandsDict):
        self._commands_tree = new_commands_tree

    def store_commands(self):
        with open(self.file_path, 'wb') as out_file:
            if self.commands is not None:
                print(f"storing commands to file=\"{out_file.name}\" ...")
                pickle.dump(self.commands, out_file)

    def _is_known_command(self, command: str, command_tree: Dict[str, Dict]) -> bool:
        for key, value in command_tree.items():
            if command.lower() == key.lower():
                return True
            elif not self._is_known_command(command, value):
                pass

        return False

    def is_known_command(self, command: str, ) -> bool:
        if self.commands is not None:
            return self._is_known_command(strip_args_from_cmd(command), self.commands)
        else:
            print(f"error: no commands loaded from file=\"{self.file_path}\"")
            return False
