#!/usr/bin/env sh

TMPD=`mktemp -d`
env PROMETHEUS_MULTIPROC_DIR=$TMPD python -m unittest tests/it_multiprocess.py
EC=$?
rm -rf $TMPD
exit $EC
