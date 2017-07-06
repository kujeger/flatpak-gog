#!/usr/bin/env python3

import json
import argparse
import collections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'installer',
        help="Game installer.")
    parser.add_argument(
        '--name',
        required=True,
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
        help="Branch version.",
        default="master")
    args = parser.parse_args()

    jsondata = json.load(
        args.template, object_pairs_hook=collections.OrderedDict)

    jsondata['app-id'] = "com.gog.{}".format(args.name)
    jsondata['branch'] = args.branch
    archivedata = jsondata['modules'][0]['sources'][0]
    archivedata['path'] = args.installer

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
