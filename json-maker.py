#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import zipfile
from collections import OrderedDict
from typing import Dict, Mapping, Optional, Sequence, TextIO

logging.basicConfig(format="%(levelname)s: %(message)s")

DEFAULT_TEMPLATE = "com.gog.Template.json"
I386_COMPAT_TEMPLATE = "com.gog.i386-compat.Template.json"


def getGameInfo(installer, argname, argbranch, argarch, archdata):
    gameinfo = {}
    with zipfile.ZipFile(installer, 'r') as myzip:
        with myzip.open('data/noarch/gameinfo') as myfile:
            tmplist = myfile.read().decode('utf-8').split('\n')
            gameinfo['orig-name'] = tmplist[0]
            gameinfo['gogversion'] = tmplist[1]
            gameinfo['version'] = tmplist[2]
            gameinfo['branch'] = argbranch
        gogversiondate = myzip.getinfo('data/noarch/gameinfo').date_time
        gameinfo['gogversiondate'] = "{}-{}-{}".format(gogversiondate[0], gogversiondate[1], gogversiondate[2])

    gameinfo['name'] = sanitizedName(gameinfo['orig-name'])
    gameinfo['app-id'] = appIDFromName(gameinfo['orig-name'])

    if argname != 'auto':
        gameinfo['name'] = argname

    if argarch == 'auto':
        gameinfo['arch'] = archdata.get(gameinfo['name'])
        if not gameinfo['arch']:
            logging.warning(
                "Arch not specified, and not found in archlist.json - "
                "defaulting to x86_64!"
            )
            gameinfo['arch'] = 'x86_64'
    else:
        gameinfo['arch'] = argarch
    if gameinfo['arch'] == 'i386+x86_64':
            gameinfo['arch'] = 'x86_64'

    return gameinfo


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
        default="modules/game.Template.json")
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
        '--branch',
        help="Branch name.",
        default='master')
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


def getGameModule(
    gamemodule_template: TextIO,
    gameinfo: Mapping[str, str],
    installer: str,
    startoverride: str,
    configureoverride: str,
    extra: Sequence[str],
) -> OrderedDict:
    """Generate the game module to be included in the output file."""
    moduledata = json.load(gamemodule_template, object_pairs_hook=OrderedDict)

    moduledata['sources'][0]['path'] = installer

    buildcommands = moduledata['build-commands']
    for idx, item in enumerate(buildcommands):
        newstring = item.replace("REPLACELONGNAME", gameinfo['orig-name'])
        newstring = newstring.replace("REPLACESHORTNAME", gameinfo['name'])
        newstring = newstring.replace("REPLACEVERSIONSTRING", gameinfo['gogversion'])
        newstring = newstring.replace("REPLACEVERSIONDATE", gameinfo['gogversiondate'])
        buildcommands[idx] = newstring

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

    for i, v in enumerate(extra):
        moduledata['sources'].append(
            OrderedDict([
                ("type", "file"),
                ("path", v),
                ("dest-filename", "installer-{}.sh".format(i+1))
            ])
        )

    return moduledata


def readTemplate(arch: str, template: Optional[TextIO]) -> Dict:
    """Read the content of the JSON template.

    Notes:
        - If arch is i386 the compatibility template is used.
        - The template can always be overridden by `template`.
    """
    if template:
        return json.load(template, object_pairs_hook=OrderedDict)
    else:
        filename = I386_COMPAT_TEMPLATE if (arch == "i386") else DEFAULT_TEMPLATE
        with open(filename, 'r') as file:
            return json.load(file, object_pairs_hook=OrderedDict)


def main() -> None:
    args = parseArgs()

    with open('archlist.json', 'r') as archfile:
        archdata = json.load(archfile)

    gameinfo = getGameInfo(
            args.installer,
            args.name,
            args.branch,
            args.arch,
            archdata)

    jsondata = readTemplate(gameinfo['arch'], args.template)

    jsondata['app-id'] = gameinfo['app-id']
    jsondata['branch'] = gameinfo['branch']

    startoverride = args.startoverride
    configureoverride = args.configureoverride
    modulesoverride = 'auto'
    if startoverride == 'auto':
        startoverride = "overrides/starter-{}".format(gameinfo['name'])
    if configureoverride == 'auto':
        configureoverride = "overrides/configure-{}".format(gameinfo['name'])
    if modulesoverride == 'auto':
        modulesoverride = "overrides/modules-{}.json".format(gameinfo['name'])

    gamemodule = getGameModule(
        args.gamemodule,
        gameinfo,
        args.installer,
        startoverride,
        configureoverride,
        args.extra,
    )
    jsondata['modules'].insert(0, gamemodule)

    if os.path.isfile(modulesoverride):
        moduledata = "{}"
        with open(modulesoverride, 'r') as f:
            moduledata = json.load(f, object_pairs_hook=OrderedDict)

        for module in moduledata:
            jsondata['modules'].append(module)

    outname = ("gen_{}.json".format(gameinfo['app-id'])
               if args.output == 'auto' else args.output)

    with open(outname, 'w') as outfile:
        json.dump(jsondata, outfile, indent=4)

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
