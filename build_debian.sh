#!/bin/sh

set -e

SRCDIR=`pwd`
BUILDDIR=build_debian

rm -rf $BUILDDIR
mkdir $BUILDDIR

python2 setup.py sdist --dist-dir $BUILDDIR

cd $BUILDDIR
tar xvzf kvalobs_model_populate-*.tar.gz
cd kvalobs_model_populate*
	
fakeroot dpkg-buildpackage -us -uc -sa

lintian -i ../kvalobs-model-populate_*_all.deb ../kvalobs-model-populate_*.dsc 
