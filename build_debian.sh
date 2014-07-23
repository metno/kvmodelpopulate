#!/bin/sh

set -e

SRCDIR=`pwd`
BUILDDIR=build_debian

rm -rf $BUILDDIR
mkdir $BUILDDIR

python setup.py sdist --dist-dir $BUILDDIR

cd $BUILDDIR
tar xvzf kvalobs-model-populate-*.tar.gz
cd kvalobs-model-populate*
	
fakeroot dpkg-buildpackage -us -uc -sa

lintian -i ../kvalobs-model-populate_0.3.5_all.deb ../kvalobs-model-populate_0.3.5.dsc 
