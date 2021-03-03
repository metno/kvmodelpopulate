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

import urllib.request, urllib.parse, urllib.error
import time
import logging

from . import locationforecast
   
log = logging.getLogger('logger')


def getLocationForecast(location, user_agent_string):
    url = '%s/?lat=%f&lon=%f' % (locationforecast.base_url, location['lat'], location['lon'])
        
    log.debug('Getting data: %s', url)
    
    for timeout in range(1,16):
        try:
            return locationforecast.getData(url, user_agent_string)
        except urllib.HTTPError as e:
            log.warn('Error on URL ' + url)
            if e.code == 503:
                log.info('Got 503: Service Unavailable from server. Retrying in %d seconds'% (timeout,))
                time.sleep(timeout)
                continue
            else:
                raise e
            
    # last attempt
    return locationforecast.getData(url, user_agent_string)
