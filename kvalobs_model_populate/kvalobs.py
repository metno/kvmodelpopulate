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
import pgdb

log = logging.getLogger('logger')
query_log = logging.getLogger('queries')


class ModelConnection(object):
    
    def __init__(self, model_name, connect_options):
        
        connect_host = connect_options.host
        if connect_options.port:
            connect_host = '%s:%d' % (connect_host, connect_options.port)
        if not connect_host:
            connect_host = None
        
        try:
            
            log.debug('Connecting to database: database=%s host=%s user=%s ' % (connect_options.database, connect_host, connect_options.user))
            self._connection = pgdb.connect(database = connect_options.database, 
                                            host = connect_host, 
                                            user = connect_options.user,
                                            password=connect_options.password)
        except pgdb.DatabaseError:
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


    def commit(self):
        query_log.info('COMMIT')
        self._connection.commit()

    def get_station_locations(self, station_list = None):
        cursor = self._connection.cursor()
        
        query = "SELECT stationid, lat, lon FROM station WHERE lat IS NOT NULL AND lon IS NOT NULL"
        #query += ' LIMIT 1'
        
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
            
        return ret


    def delete_model_data(self, from_time = None, to_time = None):
        # Remove old data 
        # A transaction is running, so it will be back if the operation fails somehow
        query = "DELETE FROM model_data WHERE modelid=%d" % (self.modelid,) 
        if from_time is not None and to_time is not None:
            query += "AND obstime BETWEEN '%s' AND '%s'" % (from_time, to_time)
        
        query_log.info(query)
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        
    
    def save_model_data(self, station, forecasts):
        cursor = self._connection.cursor()
        try:    
            # Save each row        
            for time, parameters in forecasts.items():
                for parameter, value in parameters.items():
                    
                    insert_statement = \
                    '''INSERT INTO 
                    model_data (stationid, obstime, paramid, level, modelid, original) 
                    VALUES 
                    (%d, '%s', (SELECT paramid FROM param WHERE name='%s'), 0, %d, %f)''' % \
                    (station, time, parameter, self.modelid, value)

                    if math.isnan(value):
                        log.warn('Skipping insert of NaN value: ' + insert_statement) 
                        continue

                    query_log.info(insert_statement)
                    cursor.execute(insert_statement)
        except:
            self._connection.rollback()
            raise
