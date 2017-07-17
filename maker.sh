#!/bin/bash

set -euo pipefail

SRCPATH=${1}
FILENAME=$(basename "${SRCPATH}")
NAME=${FILENAME%.*}
TMPDIR="/tmp/"
ARCH=$(flatpak --default-arch)
MAKEROPTS=""

mkdir -p ${TMPDIR}

echo "Extracting gameinfo."
unzip -q ${SRCPATH} data/noarch/gameinfo -d ${TMPDIR}/${NAME} || true
GAMENAME=$(head -n 1 ${TMPDIR}/${NAME}/data/noarch/gameinfo | sed 's/[^[:alpha:][:digit:]]//g')

if [ -d ${TMPDIR}/${NAME} ]
then
    echo "Cleaning up extracted files."
    rm -r ${TMPDIR}/${NAME}
fi

MAKEROPTS="${SRCPATH} --name ${GAMENAME}"

if [ -e overrides/starter-${GAMENAME} ]
then
    echo "Starter override found."
    MAKEROPTS="${MAKEROPTS} --startoverride overrides/starter-${GAMENAME}"
fi

if [ -s overrides/configure-${GAMENAME} ]
then
    echo "Configure override found."
    MAKEROPTS="${MAKEROPTS} --configureoverride overrides/configure-${GAMENAME}"
fi

if [ $(jq .${GAMENAME} archlist.json) != "null" ]
then
    GAMEARCH=$(jq .${GAMENAME} archlist.json | sed 's/"//g')
    if [ ${GAMEARCH} != "i386+x86_64" ]
    then
        ARCH=${GAMEARCH}
    fi
else
    echo "WARNING! Could not find arch of game, please add to archlist.json!"
fi

./json-maker.py ${MAKEROPTS} > gen_com.gog.${GAMENAME}.json
echo "Generation complete. You can build with something like

flatpak-builder build/${GAMENAME} gen_com.gog.${GAMENAME}.json --force-clean --arch ${ARCH} --repo ~/FlatPak/gog-repo"
