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
cp -r $SRCDIR/debian/ . 
cp -r $SRCDIR/share/ .

	
fakeroot dpkg-buildpackage -us -uc -sa

lintian -i ../kvalobs-model-populate_0.3.0_all.deb ../kvalobs-model-populate_0.3.0.dsc 
