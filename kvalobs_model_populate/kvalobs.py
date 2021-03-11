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


import logging
import math
import psycopg2

log = logging.getLogger('logger')
query_log = logging.getLogger('queries')


class ModelConnection(object):
    
    def __init__(self, model_name, connect_options):
        connection_string = 'dbname=' + connect_options.database
        if connect_options.user:
            connection_string += ' user=' + connect_options.user
        if connect_options.host:
            connection_string += ' host=' + connect_options.host
        if connect_options.port:
            connection_string += ' port=' + str(connect_options.port)
        log.debug('Connecting to database: ' + connection_string)
        if connect_options.password:
            connection_string += ' password=' + connect_options.password        
        try:
            self._connection = psycopg2.connect(connection_string)
        except:
            raise RuntimeError('Unable to connect to database')

        # Find model id
        cursor = self._connection.cursor()
        query = "SELECT modelid FROM model WHERE name='%s'" % (model_name,)
        query_log.info(query)
        cursor.execute(query)
        result = cursor.fetchone()
        if result is None:
            raise RuntimeError('model type <%s> have not been defined in kvalobs' % (model_name,))
        self.modelid = result[0]
        self._connection.commit()

    def commit(self):
        query_log.info('COMMIT')
        self._connection.commit()

    def rollback(self):
        query_log.info('ROLLBACK')
        self._connection.rollback()
        
    def get_station_locations(self, station_list = None):
        cursor = self._connection.cursor()
        
        query = "SELECT stationid, lat, lon FROM station WHERE lat IS NOT NULL AND lon IS NOT NULL"
        #query = "SELECT stationid, lat, lon FROM station WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY stationid limit 10"
        
        if station_list is not None and len(station_list) > 0:
            if len(station_list) == 1:
                query += ' AND stationid=%d' % (station_list[0],)
            else:
                query += ' AND stationid IN %s' % (tuple(station_list),)
        
        query_log.info(query)
        cursor.execute(query)
        
        ret = {}

        row = cursor.fetchone()
        while row:
            ret[row[0]] = {'lat': row[1], 'lon': row[2]}
            row = cursor.fetchone()
        self.commit()
        return ret

    
    def save_model_data(self, station, forecasts):
        cursor = self._connection.cursor()
        try:    
            # Save each row       
            for time, parameters in forecasts.items():
                for parameter, value in parameters.items():
                    if math.isnan(value):
                        log.warn('Skipping insert of NaN value: ' + insert_statement) 
                        continue
                    
                    insert_statement = '''INSERT INTO model_data (stationid, obstime, paramid, level, modelid, original) VALUES (%d, '%s', (SELECT paramid FROM param WHERE name='%s'), 0, %d, %f) ON CONFLICT ON CONSTRAINT model_data_stationid_obstime_paramid_level_modelid_key DO UPDATE SET original=EXCLUDED.original;''' % (station, time, parameter, self.modelid, value)
                    query_log.info(insert_statement)
                    cursor.execute(insert_statement)
            self.commit()
        except:
            self.rollback()
            raise
