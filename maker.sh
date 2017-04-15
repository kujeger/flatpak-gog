#!/bin/bash

set -euo pipefail

SRCPATH=${1}
FILENAME=$(basename "${SRCPATH}")
NAME=${FILENAME%.*}
TMPDIR="${HOME}/tmp/gogextract"
TARDIR="${TMPDIR}/tarballs"
TARBALL="${TARDIR}/${NAME}.tar"
ARCH=$(flatpak --default-arch)
MAKEROPTS=""

mkdir -p ${TMPDIR}
mkdir -p ${TARDIR}

if [ ! -d ${TMPDIR}/${NAME} ] && [ ! -f ${TARBALL} ]
then
    echo "Extracting installer."
    unzip -q ${SRCPATH} -d ${TMPDIR}/${NAME} || true
    head -n 1 ${TMPDIR}/${NAME}/data/noarch/gameinfo | sed 's/[^[:alpha:][:digit:]]//g' > ${TARBALL}.name
    head -n 2 ${TMPDIR}/${NAME}/data/noarch/gameinfo | tail -n 1 | sed 's/[^[:alpha:][:digit:]\.]//g' > ${TARBALL}.gogversion
    tail -n 1 ${TMPDIR}/${NAME}/data/noarch/gameinfo | sed 's/[^[:alpha:][:digit:]\.]//g' > ${TARBALL}.gameversion
fi

GAMENAME=$(cat ${TARBALL}.name)
GOGVERSION=$(cat ${TARBALL}.gogversion)
GAMEVERSION=$(cat ${TARBALL}.gameversion)
if [ ${GAMEVERSION} == "na" ]
then
    GAMEVERSION=0
fi

if [ ! -f ${TARBALL} ]
then
    mkdir -p ${TARDIR}
    echo "Creating tarball from game."
    cd ${TMPDIR}
    tar -cf ${TARBALL} ${NAME}
    cd -
fi

if [ ! -f ${TARBALL}.sha ]
then
    sha256sum ${TARBALL} | awk '{print $1}' > ${TARBALL}.sha
fi

if [ -d ${TMPDIR}/${NAME} ]
then
    echo "Cleaning up extracted files."
    rm -r ${TMPDIR}/${NAME}
fi

SHASUM=$(cat ${TARBALL}.sha)
MAKEROPTS="${TARBALL} --name ${GAMENAME} --sha ${SHASUM} --branch ${GOGVERSION}-${GAMEVERSION}"

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

if jq .${GAMENAME} archlist.json >> /dev/null
then
    GAMEARCH=$(jq .${GAMENAME} archlist.json | sed 's/"//g')
    if [ ${GAMEARCH} != "i386+x86_64" ]
    then
        ARCH=${GAMEARCH}
    fi
fi

./json-maker.py ${MAKEROPTS} > gen_com.gog.${GAMENAME}.json
echo "Generation complete. You can build with something like

flatpak-builder build/${GAMENAME} gen_com.gog.${GAMENAME}.json --force-clean --arch ${ARCH} --repo ~/FlatPak/gog-repo"
