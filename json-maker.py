#!/usr/bin/env python3

import json
import argparse
import collections
import zipfile
import re
import os


def getGameInfo(installer, argname, argbranch, argarch, archdata):
    gameinfo = {}
    with zipfile.ZipFile(installer, 'r') as myzip:
        with myzip.open('data/noarch/gameinfo') as myfile:
            tmplist = myfile.read().decode('utf-8').split('\n')
            gameinfo['name'] = re.sub(r'[^\w]', '', tmplist[0])
            gameinfo['gogversion'] = tmplist[1]
            gameinfo['version'] = tmplist[2]
            if gameinfo['version'] == 'na':
                gameinfo['version'] = '1.0'
            gameinfo['branch'] = gameinfo['version']

    if argname != 'auto':
        gameinfo['name'] = argname
    if argbranch != 'auto':
        gameinfo['branch'] = argbranch

    if argarch == 'auto':
        gameinfo['arch'] = archdata.get(gameinfo['name'])
    else:
        gameinfo['arch'] = argarch

    return gameinfo


def main():
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
        default="com.gog.Template.json")
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
        help="Additional installers to run (e.g. DLC). Can be used multiple times.")
    parser.add_argument(
        '--branch',
        help="Branch version. Use 'auto' to use the game version.",
        default='master')
    parser.add_argument(
        '--arch',
        help="Arch to suggest when building.",
        default='auto',
        choices=['auto', 'i386', 'x86_64'])
    parser.add_argument(
        '--output',
        help="File to write json data to.",
        default='auto')
    args = parser.parse_args()

    with open('archlist.json', 'r') as archfile:
        archdata = json.load(archfile)

    gameinfo = getGameInfo(
            args.installer,
            args.name,
            args.branch,
            args.arch,
            archdata)

    jsondata = json.load(
        args.template, object_pairs_hook=collections.OrderedDict)

    jsondata['app-id'] = "com.gog.{}".format(gameinfo['name'])
    jsondata['branch'] = gameinfo['branch']
    jsondata['modules'][0]['sources'][0]['path'] = args.installer

    startoverride = args.startoverride
    configureoverride = args.configureoverride
    if startoverride == 'auto':
        startoverride = "overrides/starter-{}".format(gameinfo['name'])
    if configureoverride == 'auto':
        configureoverride = "overrides/configure-{}".format(gameinfo['name'])

    if os.path.isfile(startoverride):
        jsondata['modules'][0]['sources'].append(
            collections.OrderedDict([
                ("type", "file"),
                ("path", startoverride)
            ])
        )
    if os.path.isfile(configureoverride):
        jsondata['modules'][0]['sources'].append(
            collections.OrderedDict([
                ("type", "file"),
                ("path", configureoverride),
                ("dest-filename", "configure")
            ])
        )

    for i, v in enumerate(args.extra):
        jsondata['modules'][0]['sources'].append(
            collections.OrderedDict([
                ("type", "file"),
                ("path", v),
                ("dest-filename", "installer-{}.sh".format(i+1))
            ])
        )

    if not gameinfo['arch']:
        print(
            "WARNING: Arch not specified, and not found in archlist.json - "
            "defaulting to x86_64!")
        gameinfo['arch'] = 'x86_64'
    if gameinfo['arch'] == 'i386+x86_64':
        gameinfo['arch'] = 'x86_64'

    outname = ("gen_com.gog.{}.json".format(gameinfo['name'])
               if args.output == 'auto' else args.output)

    with open(outname, 'w') as outfile:
        json.dump(jsondata, outfile, indent=4)

    print("JSON written to {0}\n"
          "You can build and install it thus:\n\n"
          "flatpak-builder --user --install build {0}/{1} --force-clean "
          "--arch {2}".format(os.getcwd(), outname, gameinfo['arch']))

if __name__ == '__main__':
    main()
