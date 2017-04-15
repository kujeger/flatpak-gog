#!/bin/bash

set -euo pipefail

SRCPATH=${1}
FILENAME=$(basename "${SRCPATH}")
NAME=${FILENAME%.*}
TMPDIR="${HOME}/tmp/gogextract"
TARDIR="${TMPDIR}/tarballs"
TARBALL="${TARDIR}/${NAME}.tar"
MAKEROPTS=""

mkdir -p ${TMPDIR}
mkdir -p ${TARDIR}

if [ ! -d ${TMPDIR}/${NAME} ] && [ ! -f ${TARBALL} ]
then
    echo "Extracting installer."
    unzip -q ${SRCPATH} -d ${TMPDIR}/${NAME} || true
    head -n 1 ${TMPDIR}/${NAME}/data/noarch/gameinfo | sed 's/[^[:alpha:][:digit:]]//g' > ${TARBALL}.name
fi

GAMENAME=$(cat ${TARBALL}.name)

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
MAKEROPTS="${TARBALL} --name ${GAMENAME} --sha ${SHASUM}"

if [ -e overrides/starter-${GAMENAME} ]
then
    echo "Starter override found."
    MAKEROPTS="${MAKEROPTS} --startoverride overrides/starter-${GAMENAME}"
fi

./json-maker.py ${MAKEROPTS} > gen_com.gog.${GAMENAME}.json
