"""Replace multi byte characters

Replace multi-byte characters like Japanese characters 
for enabling programs handle texts containing multi-byte characters

Usage
-----
1. As Python class
```
converter = replace_multibyte.MultiByteConverter
restorer = replace_multibyte.MultiByteRestorer
```
2. As command line tool
```
python -m multibyte-resolver
```
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path


class MultiByteConverter:
    code_regex = re.compile("[!\"#$%&'\\\\()*+,-./:;<=>?@[\\]^_`{|}~]")

    def __init__(self, prefix: str = "MBC", avoid_chars: list[str] = []) -> None:
        self._prefix = prefix
        if avoid_chars:
            self.replace_map = {c: None for c in avoid_chars}
        else:
            self.replace_map = {}

    def convert(self, string: str) -> str:
        """Convert string contains multi-byte characters.

        Parameters
        ----------
        string : str
            Any string

        Returns
        -------
        str
            Converted string if multi-byte characters are in input string, otherwise original string.
        """
        # if string in "ヾ":
        #     print("YES", string)
        #     print(self._get_reprchar(string))
        #     exit()
        reprchar = self._get_reprchar(string)
        if reprchar is not None:
            # print(f"reprchar={reprchar}")
            return reprchar
        else:
            r = self.__make_reprchar(string)
            # print(f"r={r}")
            return r

    def export_mapping(self, path: Path | str) -> None:
        with open(path, mode="w", encoding="UTF-8") as file:
            for original, reprchar in self.replace_map.items():
                file.write(f"{original} -> {reprchar}\n")
        return

    def _get_reprchar(self, string):
        special_chars = str.maketrans({"“": '"', "”": '"', "！": "!", "？": "?", "　": " "})
        string = string.translate(special_chars)
        if re.sub("[a-zA-Z0-9 ]*", "", string) == "":
            if string == "ヾ":  # todo
                # print(string == "ヾ")
                exit()
            return string
        elif string in self.replace_map:
            return self.replace_map[string]
        else:
            roman = "".join([r["passport"] for r in self.kakasi.convert(string)])
            rroman = roman
            if string == "ヾ":
                return self.__make_reprchar(string, True)
            elif roman == "":
                brackets = str.maketrans({"「": "(", "」": ")"})
                roman = string.translate(brackets)
                # roman = self.special_char_to_x(roman)
                # print(f"nothing, string='{string}', return={roman}")
                return roman
            elif roman.isdigit() or self.code_regex.sub("", roman) == "":
                # print(f"rroman={rroman}, string={string}, self.kakasi.convert(string)={self.kakasi.convert(string)}")
                return rroman
            else:
                # print(f"KeyNotFound: {string}")
                return None

    def __get_roman(self, string):
        roman = "".join([r["passport"] for r in self.kakasi.convert(string)])
        roman = self.fullwidth_char_to_x(roman)
        return roman

    def __make_reprchar(self, string, special=False):
        # print(string)
        if not special:
            roman = self.__get_roman(string)
            rroman = roman
            if roman.isdigit() or self.code_regex.sub("", roman) == "":
                print("convert2alphabet.py:39 was called.")
                return rroman
            roman = re.sub(r"\W", "x", roman)
            roman = roman.capitalize()
            reprchar = "JaWord" + roman
        else:
            reprchar = "JaWordX"
        if reprchar in self.replace_map.values():
            i = 1
            while True:
                new_reprchar = reprchar + str(i)
                if new_reprchar in self.replace_map.values():
                    i += 1
                else:
                    break
            reprchar = new_reprchar
        self.replace_map[string] = reprchar
        return reprchar

    def _reset_map(self, prefix: str | None = None):
        """Reset current replace map

        Parameters
        ----------
        prefix : str | None, optional
            New prefix string, current prefix string will be used if None is specified, by default None
        """
        self.replace_map.clear()
        if prefix is not None:
            self._prefix = prefix

    def _add_avoid_strings(self, avoid_strings: list[str]):
        """Add avoid strings

        CAUTION: Strings that already converted will not be changed.

        Parameters
        ----------
        avoid_strings : list[str]
            Extra strings that convert function will avoid replacing string to from next time.
        """
        for s in avoid_strings:
            self.replace_map[s] = None

    def fullwidth_char_to_x(self, string):
        ret = ""
        for c in string:
            if unicodedata.east_asian_width(c) != "Na":
                ret += "x"
            else:
                ret += c
        return ret


class MultiByteRestorer:
    def __init__(self, replace_map: Mapping | Path | str) -> None:
        """Restore strings converted by MultiByteConverter to original strings

        Parameters
        ----------
        replace_map : Mapping | str
            Path to map file exported by MultiByteConverter.export_mapping function or Mapping object.

        Note
        ----
        When using Mapping object as replace_map, object follows the following structure.
        {
            OriginalString: ReplaceString
            ...
        }
        """
        if isinstance(replace_map, (Path, str)):
            self.replace_map = {}
            with open(file=replace_map, mode="r", encoding="UTF-8") as file:
                for i, l in enumerate(file.readlines(), start=1):
                    try:
                        original, reprchar = l.strip().split(" -> ")
                    except ValueError:
                        raise BrokenMappingFile(str(replace_map), i)
                    else:
                        self.replace_map[original] = reprchar
        elif replace_map is not str:
            self.replace_map = replace_map
        # Reverse key & value of replace_map
        self.replace_map = {v: k for k, v in self.replace_map.items()}

    def restore(self, string):
        try:
            return self.replace_map[string]
        except KeyError:
            return string


class BrokenMappingFile(Exception):
    def __init__(self, file: str, line: int) -> None:
        self.file = str
        self.line = line

    def __str__(self) -> str:
        return f"Unexpected format is found on line {self.line} of mapping file ({self.file}.)"


def cmd():
    parser = argparse.ArgumentParser(
        prog="multibyte-resolver",
        description="Convert string that contains multi-byte characters to string consists of general alphanumeric characters",
        epilog="Example: multibyte-resolver convert ja.txt",
    )
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "target_file", type=argparse.FileType(mode="r", encoding="UTF-8"), help="Each words are splitted by delimiter"
    )
    parent_parser.add_argument(
        "--delimiter",
        "-d",
        type=str,
        default=" ",
        help='String that splits each tokens, by default " "(half-width blank).',
    )
    subparsers = parser.add_subparsers(required=True)
    parser_convert = subparsers.add_parser(
        "convert",
        help="Replace string that contains multi-byte characters to string consists of general alphanumeric characters",
        parents=[parent_parser],
    )
    parser_convert.set_defaults(op="convert")
    # help="Convert multi-byte string or restore original multi-byte string from mapping file.")
    parser_restore = subparsers.add_parser(
        "restore",
        help="Restore original string that contains multi-byte characters from mapping file",
        parents=[parent_parser],
    )
    parser_restore.add_argument(
        "mapping_file",
        type=argparse.FileType(mode="r", encoding="UTF-8"),
        help="Mapping file exported by convert command.",
    )
    parser_restore.set_defaults(op="restore")
    try:
        args = parser.parse_args()
    except TypeError:
        parser.print_help()
        return
    if args.op == "convert":
        converter = MultiByteConverter()
        lines = args.target_file.readlines()
        output_filepath = Path(args.target_file.name + ".convert").resolve()
        mapping_filepath = Path(str(output_filepath) + ".map").resolve()
        with open(output_filepath, mode="w", encoding="UTF-8") as outfile:
            for line in [l.strip("\n") for l in args.target_file.readlines()]:
                outfile.write(args.delimiter.join([converter.convert(t) for t in line.split(args.delimiter)]) + "\n")
        print(f"Converted text is exported to {output_filepath}.")
        converter.export_mapping(mapping_filepath)
        print(f"Mapping file is exported to {mapping_filepath}.")
    elif args.op == "restore":
        output_filepath = Path(args.target_file.name + ".restore").resolve()
        # Import mapping data
        mapping = {orig: repr for l in args.mapping_file.readlines() for orig, repr in l.strip().split(" -> ")}
        restorer = MultiByteRestorer(replace_map=mapping)
        with open(output_filepath, mode="w", encoding="UTF-8") as outfile:
            for line in [l.strip("\n") for l in args.target_file.readlines()]:
                outfile.write(args.delimiter.join([restorer.restore(t) for t in line.split(args.delimiter)]) + "\n")
        print(f"Restored text is exported to {output_filepath}.")
    return


if __name__ == "__main__":
    cmd()
