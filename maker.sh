#!/bin/bash

set -euo pipefail

SRCPATH=${1}
FILENAME=$(basename "${SRCPATH}")
NAME=${FILENAME%.*}
TMPDIR="${HOME}/tmp/gogextract"
TARDIR="${TMPDIR}/tarballs"
TARBALL="${TARDIR}/${NAME}.tar"

if [ ! -d ${TMPDIR}/${NAME} ]
then
    echo "Extracting installer."
    mkdir -p ${TMPDIR}
    unzip -q ${SRCPATH} -d ${TMPDIR}/${NAME} || true
fi

GAMENAME=$(head -n 1 ${TMPDIR}/${NAME}/data/noarch/gameinfo | sed 's/[^[:alpha:][:digit:]]//g')
mkdir -p tarballs

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

SHASUM=$(cat ${TARBALL}.sha)

./json-maker.py ${TARBALL} --name ${GAMENAME} --sha ${SHASUM} > generated/com.gog.${GAMENAME}.json
