#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import zipfile
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, List, Mapping, Optional, TextIO

from typing_extensions import Literal

logging.basicConfig(format="%(levelname)s: %(message)s")

DEFAULT_TEMPLATE = "com.gog.Template.json"
I386_COMPAT_TEMPLATE = "com.gog.i386-compat.Template.json"

MOJO_GAMEMODULE = "modules/game-mojo.Template.json"

Json = OrderedDict  # [str, Any]
Transform = Callable[[Json], Json]
Arch = Literal["i386", "i386+x86_64", "x86_64"]
InstallerType = Literal["mojo"]


@dataclass
class GameInfo:
    origname: str
    gogversion: str
    version: str
    # arch parameter requires Optional, but arch attribute doesn't
    _arch: Optional[Arch] = field(repr=False, compare=False, hash=False)
    gogversiondate: str
    typ: InstallerType
    name: str = field(init=False)
    appid: str = field(init=False)
    arch: Arch = field(init=False)

    def __post_init__(self) -> None:
        argname = args.name if args.name != "auto" else None
        argarch = args.arch if args.arch != "auto" else None
        self.origname = argname or self.origname
        self.name = sanitizedName(self.origname)
        self.appid = appIDFromName(self.origname)
        self.arch = argarch or self._arch or self._lookupArch(self.name)

    @staticmethod
    def fromMojoSetup(installer: str) -> "GameInfo":
        """Get game info from the Mojo Setup format used by GOG Linux installers."""
        with zipfile.ZipFile(installer, 'r') as myzip:
            with myzip.open('data/noarch/gameinfo') as myfile:
                tmplist = myfile.read().decode('utf-8').split('\n')
                name = tmplist[0]
                gogversion = tmplist[1]
                version = tmplist[2]
                if version == 'na':
                    version = '1.0'
            filedatetime = myzip.getinfo('data/noarch/gameinfo').date_time
        gogversiondate = "{0}-{1}-{2}".format(*filedatetime)

        return GameInfo(name, gogversion, version, None, gogversiondate, "mojo")

    @staticmethod
    def _lookupArch(gamename: str) -> Arch:
        with open('archlist.json', 'r') as archfile:
            archdata = json.load(archfile)

        arch = archdata.get(gamename)
        if not arch:
            logging.warning(
                "Arch not specified, and not found in archlist.json - "
                "defaulting to x86_64!"
            )
            arch = "x86_64"
        return arch


def sanitizedName(name: str) -> str:
    """Sanitize name, so it can be used in filenames."""
    # Remove whitespace
    return re.sub(r'[^\w]', '', name)


def appIDFromName(name: str) -> str:
    """Returns a valid AppID for a given name."""
    # Converts name to CamelCase.
    namecc = sanitizedName(name)
    # app-id cannot start with a digit. Add an underscore if needed.
    if namecc[0].isdigit():
        return 'com.gog._' + namecc
    else:
        return 'com.gog.' + namecc


class Template:
    """Flatpak builder template based on gameinfo data.

    Rendering the template loads JSON data from a template file, applies all
    given transforms and replaces placeholders with data from gameinfo.
    """

    def __init__(self, gameinfo: GameInfo, transforms: List[Transform] = []) -> None:
        self.gameinfo = gameinfo
        # Last transform is the string replacement
        self.transforms = transforms + [self._render]
        self.replace_dict: Mapping[str, str] = {
            "APPID": self.gameinfo.appid,
            "GAMENAME": self.gameinfo.name,
            "REPLACELONGNAME": self.gameinfo.origname,
            "REPLACESHORTNAME": self.gameinfo.name,
            "REPLACEVERSIONSTRING": self.gameinfo.gogversion,
            "REPLACEVERSIONDATE": self.gameinfo.gogversiondate,
        }

    def transform(self, transform: Transform) -> "Template":
        """Returns a new template with the transform applied on top."""
        return Template(self.gameinfo, self.transforms[:-1] + [transform])

    def render(self) -> Json:
        """Returns a rendered JSON object.

        The returned JSON object has all transformations applied to the template
        and all placeholder strings replaced by their real values.
        """
        jsondata = self._loadTemplateFromFile(self.gameinfo.arch)
        transformed = self._applyTransforms(jsondata)
        return transformed

    def _applyTransforms(self, jsondata: Json) -> Json:
        for t in self.transforms:
            jsondata = t(jsondata)
        return jsondata

    def _render(self, x: Any) -> Any:
        """Returns a JSON object with every replacement applied to every string."""

        def replace_all(s: str) -> str:
            for k, v in self.replace_dict.items():
                s = s.replace(k, v)
            return s

        if isinstance(x, dict):
            return OrderedDict((k, self._render(v)) for k, v in x.items())
        if isinstance(x, list):
            return [self._render(k) for k in x]
        if isinstance(x, str):
            return replace_all(x)
        return x

    @staticmethod
    def _loadTemplateFromFile(arch: Arch) -> Json:
        if args.template:
            return json.load(args.template, object_pairs_hook=OrderedDict)

        filename = I386_COMPAT_TEMPLATE if (arch == "i386") else DEFAULT_TEMPLATE
        with open(filename, "r") as file:
            return json.load(file, object_pairs_hook=OrderedDict)


class Installer:
    """Provides GameInfo and a Template for the given installer file.

    Inheriting classes can override `gamemodule_template` and `getTemplate()` to
    customize template generation.
    """

    installer: str
    gamemodule_template: TextIO
    gameinfo: GameInfo

    def getTemplate(self) -> Template:
        return Template(self.gameinfo)

    @staticmethod
    def newInstance(installer: str) -> "Installer":
        if installer.endswith(".sh"):
            return MojoSetupInstaller(installer)
        raise ValueError(f"Unknown file extension '{os.path.splitext(installer)[1]}'")

    def getGamemodule(self) -> Json:
        """Generate the game module and insert it into the template's JSON."""
        startoverride = args.startoverride
        configureoverride = args.configureoverride
        if startoverride == 'auto':
            startoverride = f"overrides/starter-{self.gameinfo.name}"
        if configureoverride == 'auto':
            configureoverride = f"overrides/configure-{self.gameinfo.name}"

        moduledata = json.load(
            args.gamemodule or self.gamemodule_template, object_pairs_hook=OrderedDict
        )

        moduledata['sources'][0]['path'] = self.installer

        if os.path.isfile(startoverride):
            moduledata['sources'].append(
                OrderedDict([
                    ("type", "file"),
                    ("path", startoverride)
                ])
            )

        if os.path.isfile(configureoverride):
            moduledata['sources'].append(
                OrderedDict([
                    ("type", "file"),
                    ("path", configureoverride),
                    ("dest-filename", "configure")
                ])
            )

        for i, v in enumerate(args.extra):
            moduledata['sources'].append(
                OrderedDict([
                    ("type", "file"),
                    ("path", v),
                    ("dest-filename", "installer-{}.sh".format(i+1))
                ])
            )

        return moduledata


class MojoSetupInstaller(Installer):
    """Linux GOG installer."""

    def __init__(self, installer: str) -> None:
        self.installer = installer
        self.gameinfo = GameInfo.fromMojoSetup(installer)
        self.gamemodule_template = open(MOJO_GAMEMODULE, "r")

    # @override
    def getTemplate(self) -> Template:
        def addGamemodule(jsondata: Json) -> Json:
            moduledata = self.getGamemodule()
            jsondata["modules"].append(moduledata)
            return jsondata

        return Template(self.gameinfo).transform(addGamemodule)


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'installer',
        help="Game installer.")
    parser.add_argument(
        '--name',
        default='auto',
        help="Name of game.")
    parser.add_argument(
        '--template',
        help="Template json to use for game setup.",
        type=argparse.FileType('r'),
        default=None)
    parser.add_argument(
        '--gamemodule',
        help="Template json of the game module.",
        type=argparse.FileType('r'),
        default=None)
    parser.add_argument(
        '--startoverride',
        help="Start script to override default.",
        default='auto')
    parser.add_argument(
        '--configureoverride',
        help="Additional configure script to add.",
        default='auto')
    parser.add_argument(
        '--extra',
        action='append',
        default=[],
        help="Additional installers to run (e.g. DLC). " +
             "Can be used multiple times.")
    parser.add_argument(
        '--arch',
        help="Arch of game.",
        default='auto',
        choices=['auto', 'i386', 'x86_64'])
    parser.add_argument(
        '--output',
        help="File to write json data to.",
        default='auto')
    parser.add_argument(
        '--verbose',
        '-v',
        default=0,
        action='count')
    return parser.parse_args()

args = parseArgs()


def main() -> None:
    installer = Installer.newInstance(args.installer)
    gameinfo = installer.gameinfo

    def moduleOverride(jsondata: Json) -> Json:
        modulesoverride = f"overrides/modules-{gameinfo.name}.json"
        if os.path.isfile(modulesoverride):
            with open(modulesoverride, "r") as f:
                moduledata = json.load(f, object_pairs_hook=OrderedDict)

            for module in moduledata:
                jsondata["modules"].append(module)
        return jsondata

    template = installer.getTemplate().transform(moduleOverride)

    outname = ("gen_{}.json".format(gameinfo.appid)
               if args.output == 'auto' else args.output)

    with open(outname, 'w') as outfile:
        json.dump(template.render(), outfile, indent=4)

    if args.verbose > 0:
        print("JSON written to {1}\n"
              "You can build and install it thus:\n\n"
              "flatpak-builder --user --install build {0}/{1} --force-clean "
              "--arch x86_64".format(os.getcwd(), outname))
    else:
        print("flatpak-builder --user --install build {0}/{1} --force-clean "
              "--arch x86_64".format(os.getcwd(), outname))

if __name__ == '__main__':
    main()
