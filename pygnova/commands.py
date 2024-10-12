import json
import pickle
import re
from typing import Dict


def to_nested_json_from_delimited_items(items: str):
    tree = {}
    for item in json.loads(items):
        t = tree
        for part in item.split(':'):
            t = t.setdefault(part, {})
    return tree


def print_nested_json_tree(tree, level=0):
    for key, value in tree.items():
        print(
            "   " * (level - 1),
            "-> " if level else "",
            key,
            sep="")
        print_nested_json_tree(value, level + 1)


def load_commands_from_file(file_path_name: str) -> Dict:
    with open(file_path_name, 'rb') as in_file:
        print(f"loading commands from {file_path_name} ...")
        tree = pickle.load(in_file)
        return tree


def store_to_file(file_path_name: str, tree: Dict):
    with open(file_path_name, 'wb') as out_file:
        pickle.dump(tree, out_file)
        print(f"stored scpi-def to {out_file.name}")


def command_from_cmd_with_args(command_with_optional_args: str) -> str:
    r = re.compile(r"[? ]+.*$")
    return r.sub("", command_with_optional_args)  # without args or "?"


def _is_known_command(command: str, command_tree: Dict[str, Dict]) -> bool:
    for key, value in command_tree.items():
        if command.lower() == key.lower():
            return True
        elif not _is_known_command(
                command, value):
            pass

    return False


def is_known_command(command: str, command_tree: Dict[str, Dict]) -> bool:
    return _is_known_command(command_from_cmd_with_args(command), command_tree)
