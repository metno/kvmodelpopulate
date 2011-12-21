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

from distutils.core import setup

import sys
sys.path.insert(0, 'src/')
import kvalobs_model_populate


setup(name='kvalobs-model-populate',
      description = 'Populate a kvalobs database with data from api.met.no',
      version = kvalobs_model_populate.version,
      url = 'https://kvalobs.wiki.met.no/',

      author = 'Vegard Bones',
      author_email = 'vegard.bones@met.no',
      
      license = 'gpl2',
      
      requires = ['pgdb'],
      
      package_dir = {'': 'src'},
      packages = ['kvalobs_model_populate', 'kvalobs_model_populate.yr'],
      scripts = ['kvalobs_model_populate']
     )

