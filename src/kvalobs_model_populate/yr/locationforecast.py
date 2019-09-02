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

import urllib2
import xml.sax.handler
import time
import datetime
import logging


log = logging.getLogger('logger')

base_url = 'https://api.met.no/weatherapi/locationforecast/1.9'


_handlers = {('precipitation', datetime.timedelta(hours = 6)): ('RR_6', 'value'),
            ('pressure', datetime.timedelta()): ('PR', 'value'),
            ('windDirection', datetime.timedelta()): ('DD', 'deg'),
            ('windSpeed', datetime.timedelta()): ('FF', 'mps'),
            ('humidity', datetime.timedelta()): ('UU', 'value'),
            ('temperature', datetime.timedelta()): ('TA', 'value')
            }


def getData(url, user_agent_string):

    request = urllib2.Request(url, headers = {'User-Agent': user_agent_string}) 
    data = urllib2.urlopen(request)

    try:
        if data.code == 203:
            log.warning('The requested url has been deprecated.')
    except AttributeError:
        # data.code seems to be undocumented, so we ensure that we don't die 
        # if the variable is removed from that class in later python versions
        pass    

    doc = ContentHandler()
    xml.sax.parse(data, doc)
    return doc.getdata()


class ContentHandler(xml.sax.handler.ContentHandler):

    def __init__(self):
        self._data = {}
        
    def getdata(self):
        return self._data
    
    def startDocument(self):
        self._data = {}
        self.time = None
        self.duration = None
        
    def endDocument(self):
        self._data.update(self._data)
        
    def startElement(self, name, attrs):
        if name == 'time':
            # Newer python versions:
            #from_ = datetime.datetime.strptime(attrs.getValue('from'), '%Y-%m-%dT%H:%M:%SZ')
            #to = datetime.datetime.strptime(attrs.getValue('to'), '%Y-%m-%dT%H:%M:%SZ')
            from_ = datetime.datetime.fromtimestamp(time.mktime(time.strptime(attrs.getValue('from'), '%Y-%m-%dT%H:%M:%SZ')))
            to = datetime.datetime.fromtimestamp(time.mktime(time.strptime(attrs.getValue('to'), '%Y-%m-%dT%H:%M:%SZ')))

            self.duration = to - from_

            try:
                self.time = self._data[to]
            except KeyError:
                self.time = {}
                self._data[to] = self.time
        else:
            try:
                # Parse parameters, which are defined in the _handlers map
                param_data = _handlers[(name, self.duration)]
                if self.time.has_key(param_data[0]):
                    log.warning('Duplicate key in data: ' + param_data[0])
                self.time[param_data[0]] = float(attrs.getValue(param_data[1]))
            except KeyError:
                pass
            
    def endElement(self, name):
        if name == 'time':
            self.time = None
            self.duration = None
            