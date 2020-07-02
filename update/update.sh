#!/bin/bash

lang=""
export lang
TOPDIR=/home/fa/udisk/update
SRC_SCREENDIR=${TOPDIR}/screen
SRC_OCTODIR=${TOPDIR}/octoprint
DST_SCREENDIR=/home/fa/qtEmbedded/bin
DST_OCTODIR=/home/fa/oprint/lib/python2.7/site-packages/OctoPrint-1.2.13-py2.7.egg
WEB_SOCKET=/home/fa/oprint/lib/python2.7/site-packages/websocket_client-0.13.0-py2.7.egg/websocket

FA_DoExec() {
	echo "${@}"
	eval $@ || exit $?
}

FA_DoExec "cd ${SRC_SCREENDIR}"
FA_DoExec "find ./ -type f -print0 | xargs -0 md5sum | sort > ${TOPDIR}/screen.md5"
FA_DoExec "cd ${SRC_OCTODIR}"
FA_DoExec "find ./ -type f -print0 | xargs -0 md5sum | sort > ${TOPDIR}/octoprint.md5"

if [ -d ${TOPDIR}/screen-bak ]; then
	FA_DoExec "rm -r ${TOPDIR}/screen-bak"
fi

if [ -d ${TOPDIR}/octoprint-bak ]; then
	FA_DoExec "rm -r ${TOPDIR}/octoprint-bak"
fi

FA_DoExec "cp ${DST_SCREENDIR}/screen ${TOPDIR}/screen-bak -rf"
FA_DoExec "cp ${DST_OCTODIR}/octoprint ${TOPDIR}/octoprint-bak -rf"

[ -d ${SRC_SCREENDIR} ] || { echo "Error: ./${SRC_SCREENDIR}: not found"; exit 1; }
[ -d ${SRC_OCTODIR} ] || { echo "Error: ./${SRC_OCTODIR}: not found"; exit 1; }

killall -9 octoprint

if [ -d /home/fa/.octoprint ]; then
	rm /home/fa/.octoprint -rf
fi

if [ -d /home/fa/.localserver ]; then
	rm /home/fa/.localserver -rf
fi

FA_DoExec "rm ${DST_SCREENDIR}/screen -rf"
FA_DoExec "cp ${SRC_SCREENDIR} ${DST_SCREENDIR} -arf"
FA_DoExec "cd ${DST_SCREENDIR}/screen"
FA_DoExec "find ./ -type f -print0 | xargs -0 md5sum | sort > ${TOPDIR}/screen_dst.md5"
screen_file1=${TOPDIR}/screen.md5
screen_file2=${TOPDIR}/screen_dst.md5
diff $screen_file1 $screen_file2 > /dev/null
if [ $? == 0 ]; then
	echo "check screen success!"
	FA_DoExec "rm -r ${TOPDIR}/screen-bak"
#	FA_DoExec "rm ${TOPDIR}/screen.md5 ${TOPDIR}/screen_dst.md5"
else
	echo "check screen failed!"
	FA_DoExec "rm ${DST_SCREENDIR}/screen -rf"
	FA_DoExec "cp ${TOPDIR}/screen-bak ${DST_SCREENDIR}/screen -rf"
#	FA_DoExec "rm ${TOPDIR}/screen.md5 ${TOPDIR}/screen_dst.md5"
fi


FA_DoExec "rm ${DST_OCTODIR}/octoprint -rf"
FA_DoExec "cp ${SRC_OCTODIR} ${DST_OCTODIR} -arf"
FA_DoExec "cd ${DST_OCTODIR}/octoprint"
FA_DoExec "find ./ -type f -print0 | xargs -0 md5sum | sort > ${TOPDIR}/octoprint_dst.md5"
octoprint_file1=${TOPDIR}/octoprint.md5
octoprint_file2=${TOPDIR}/octoprint_dst.md5
diff $octoprint_file1 $octoprint_file2 > /dev/null
if [ $? == 0 ]; then
	echo "check octoprint success!"
	FA_DoExec "rm -r ${TOPDIR}/octoprint-bak"
#	FA_DoExec "rm ${TOPDIR}/octoprint.md5 ${TOPDIR}/octoprint_dst.md5"
else
	echo "check octoprint failed!"
	FA_DoExec "rm ${DST_OCTODIR}/octoprint -rf"
	FA_DoExec "cp ${TOPDIR}/octoprint-bak ${DST_OCTODIR}/octoprint -rf"
#	FA_DoExec "rm ${TOPDIR}/octoprint.md5 ${TOPDIR}/octoprint_dst.md5"
fi

FA_DoExec "cp ${TOPDIR}/__init__.py ${WEB_SOCKET}/__init__.py"

FW_PRINTENV=${TOPDIR}/tools/fw_printenv
FW_SETENV=${TOPDIR}/tools/fw_setenv
ENV_CONF=${TOPDIR}/tools/env.conf

FA_DoExec "${FW_SETENV} -s ${ENV_CONF}"

echo "update success!"
reboot
exit 0
