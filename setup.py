#!/usr/bin/env python
#
# kvalobs_model_populate
#
# Copyright (C) 2011 met.no
#
# Contact information:
# Norwegian Meteorological Institute
# Box 43 Blindern
# 0313 OSLO
# NORWAY
# E-mail: post@met.no
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA

from setuptools import setup, find_packages

setup(
    name="kvalobs_model_populate",
    version="0.3.13",
    packages=find_packages(),
    scripts=["kvmodelpopulate"],
    description="Populate a kvalobs database with data from api.met.no",
    license="gpl2",
    requires=["psycopg"],
)
