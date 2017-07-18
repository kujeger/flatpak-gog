#!/usr/bin/env python3

import json
import argparse
import collections
import zipfile
import re


def getGameInfo(installer, argname, argbranch):
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
        help="Start script to override default.")
    parser.add_argument(
        '--configureoverride',
        help="Additional configure script to add.")
    parser.add_argument(
        '--extra',
        nargs='*',
        help="Additional installers to run (e.g. DLC)")
    parser.add_argument(
        '--branch',
        help="Branch version. Use 'auto' to use the game version.",
        default='master')
    parser.add_argument(
        '--output',
        help="File to write json data to.",
        default='auto')
    args = parser.parse_args()

    gameinfo = getGameInfo(
            args.installer,
            args.name,
            args.branch)

    jsondata = json.load(
        args.template, object_pairs_hook=collections.OrderedDict)

    jsondata['app-id'] = "com.gog.{}".format(gameinfo['name'])
    jsondata['branch'] = gameinfo['branch']
    jsondata['modules'][0]['sources'][0]['path'] = args.installer

    if args.startoverride:
        jsondata['modules'][0]['sources'].append(
            collections.OrderedDict([
                ("type", "file"),
                ("path", args.startoverride)
            ])
        )

    if args.configureoverride:
        jsondata['modules'][0]['sources'].append(
            collections.OrderedDict([
                ("type", "file"),
                ("path", args.configureoverride),
                ("dest-filename", "configure")
            ])
        )

    if args.extra:
        for i, v in enumerate(args.extra):
            jsondata['modules'][0]['sources'].append(
                collections.OrderedDict([
                    ("type", "file"),
                    ("path", v),
                    ("dest-filename", "installer-{}.sh".format(i+1))
                ])
            )

    print(json.dumps(jsondata, indent=4))


if __name__ == '__main__':
    main()
