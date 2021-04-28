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

from datetime import timedelta, datetime
import time
import sys
import os.path
import logging
import logging.handlers

import kvalobs_model_populate.kvalobs as kvalobs
import kvalobs_model_populate.yr as yr

log = logging.getLogger('logger')
status_log = logging.getLogger('status')
query_log = logging.getLogger('queries')


def _progress_indicator(max_count):
    progress_list = ('\r-', '\r\\', '\r|', '\r/')
    entries = len(progress_list)
    index = 1
    while True:
        nextLine = '\r%s [%d%%] - %d/%d    ' % (
            progress_list[index % entries], (float(index)/max_count) * 100, index, max_count)
        yield nextLine
        index += 1


def extractWantedData(forecast, from_first_time):
    first_time = min(forecast.keys())

    offset = (first_time.hour + 6) % 12
    if from_first_time:
        refereence_point = first_time - timedelta(hours=offset)
    elif offset != 0:
        refereence_point = first_time + timedelta(hours=12 - offset)
    else:
        refereence_point = first_time

    key_times = []
    for h in range(0, 25, 6):
        key_times.append(refereence_point + timedelta(hours=h))

    ret = {}

    current_time = max(first_time, refereence_point)
    while current_time < key_times[2]:
        if current_time in forecast:
            ret[current_time] = forecast[current_time]
            #log.debug('time ' + current_time.isoformat())
        current_time += timedelta(hours=1)

    try:
        RR_12 = (
            forecast[key_times[1]]['RR_6'] + forecast[key_times[2]]['RR_6'],
            forecast[key_times[3]]['RR_6'] + forecast[key_times[3]]['RR_6'])
        RR_24 = sum(RR_12)

        ret[key_times[2]] = {'RR_12': RR_12[0]}
        ret[key_times[4]] = {'RR_24': RR_24}
    except KeyError as e:
        log.warn(
            'Error when creating RR data aggregates: object was not reported from yr: ' + str(e),)

    try:
        last_time = refereence_point
        for t in range(3, 13, 3):
            working_time = refereence_point + timedelta(hours=t)
            if last_time in forecast:
                ret[working_time]['PP'] = forecast[last_time]['PR'] - \
                    forecast[working_time]['PR']
            last_time = working_time
    except KeyError as e:
        log.warn(
            'Error when creating PP data aggregates: object was not reported from yr: ' + str(e),)

    return ret


def timed_yielder(original_list, seconds_between_each):

    ideal_time = time.time()

    missed_deadlines = 0

    for element in original_list:

        ideal_time += seconds_between_each
        now = time.time()
        time_left_to_return = ideal_time - now

        if time_left_to_return > 0:
            time_to_sleep = time_left_to_return
        else:
            # if we spent more than our allotted time, sleep some
            # more to relieve some pressure from server
            time_to_sleep = seconds_between_each
            ideal_time = now + seconds_between_each
            missed_deadlines += 1

        time.sleep(time_to_sleep)

        yield element


def populate_kvalobs(options):
    nOk = 0
    connection = kvalobs.ModelConnection(options.model_name, options)
    stations = connection.get_station_locations(options.station_list)

    if len(stations) == 0:
        log.warn('No stations returned from query')
        status_log.info("SUMARY 0/0, no stations returned from query")
        return

    log.info('Fetching model data from yr to kvalobs')

    stations_without_coordinates = []
    for station, location in stations.items():
        if location['lat'] is None or location['lon'] is None:
            stations_without_coordinates.append(station)

    if stations_without_coordinates:
        for s in stations_without_coordinates:
            del stations[s]
            log.debug(
                "Ignoring station %d, since we haven't got its coordinates" % (station,))

    sorted_stations = list(stations.keys())
    sorted_stations.sort()

    if options.enable_progress_bar:
        progress = _progress_indicator(len(sorted_stations))
    else:
        progress = None
   
    for i in range(3):
        failed = []
        for station in timed_yielder(sorted_stations, options.sleep):
            log.debug('Station %d' % (station,))
            location = stations[station]

            try:
                locationforecast = yr.getLocationForecast(
                    location, 'met.no kvalobs model fetcher')
                nOk += 1
            except:
                log.warning('failed attempt station %d', station)
                failed.append(station)
                continue

            if progress is not None:
                sys.stderr.write(next(progress))

            forecast = extractWantedData(locationforecast,
                                         options.from_first_time)
            connection.save_model_data(station, forecast)
        if not failed:
            break
        sorted_stations = failed
        if len(failed) > 100:
            time.sleep(300)

    if failed:
        log.error('Unable to fetch data for the following stations: ' + str(failed))

    # connection.commit()
    if options.enable_progress_bar:
        sys.stderr.write('\n')

    log.info('Done fetching data')

    nStations = len(stations)
    if nOk == nStations:
        status_log.info("SUMARY %d/%d, fetched all stations" %
                        (nOk, nStations))
    elif nOk == 0:
        status_log.error(
            "SUMARY %d/%d, failed to fetch any stations" % (nOk, nStations))
    else:
        status_log.warning(
            "SUMARY %d/%d, failed to get some stations" % (nOk, nStations))


def _get_kvalobs_connection_info(config_file):

    ret = {}

    kvalobs_config_file = config_file
    if os.path.exists(kvalobs_config_file):

        f = open(kvalobs_config_file)
        for line in f:
            try:
                key, value = line.split('=', 1)
                if key.strip() == 'dbconnect':
                    value = value.strip('" \'\n')
                    pairs = value.split()
                    for pair in pairs:
                        key, value = pair.split('=', 1)
                        ret[key.strip()] = value.strip()
            except ValueError:
                pass
        f.close()

    return ret


def add_to_options(options, config_file):

    for key, value in _get_kvalobs_connection_info(config_file).items():
        if key == 'user' and not options.user:
            options.user = value
        elif key == 'dbname' and not options.database:
            options.database = value
        elif key == 'password':
            options.password = value
        elif key == 'host' and not options.host:
            options.host = value
        elif key == 'port' and not options.port:
            options.port = int(value)


def main():

    import optparse

    parser = optparse.OptionParser(
        description='Populate model data in kvalobs',
        usage='Usage: %prog [OPTIONS]', conflict_handler='resolve')

    database_options = optparse.OptionGroup(
        parser, 'Database options', 'Options for kvalobs database access')
    database_options.add_option('-m', '--model-name',
                                metavar='MODEL_NAME',
                                default='yr',
                                help='Use the given name in the kvalobs database'
                                )
    database_options.add_option('-d', '--database',
                                default='kvalobs',
                                metavar='DATABASE',
                                help='database name (default %default)')
    database_options.add_option('-h', '--host',
                                metavar='HOSTNAME',
                                help='database server host or socket directory')
    database_options.add_option('-p', '--port',
                                type='int',
                                metavar='PORT',
                                help='database server port')
    database_options.add_option('-U', '--username',
                                metavar='USERNAME',
                                dest='user',
                                help='database user name')
    database_options.add_option('', '--password',
                                metavar='PASSWORD',
                                dest='password',
                                help='database password')
    parser.add_option_group(database_options)

    logging_options = optparse.OptionGroup(
        parser, 'Logging options', 'Options for controlling logging')
    logging_options.add_option('', '--status-file',
                               metavar='STATUSFILE',
                               dest='statusfile',
                               #default='/var/log/kvalobs/kvalobs_model_populate_status.log',
                               help='Write status messages to file. Format: timestamp status #expected #failed, where status is OK, WARN or FAILED.'
                               )
    logging_options.add_option('-l', '--log-file',
                               metavar='LOGFILE',
                               dest='logfile',
                               #default = 'kvalobs_model_populate.log',
                               help='Write log messages to the given file'
                               )
    logging_options.add_option('', '--log-level',
                               metavar='LEVEL',
                               default='warning',
                               help='Only log messages of the given severity or higher. Allowed values: debug, info, warning, error, fatal. Default is %default.'
                               )
    logging_options.add_option('', '--log-queries',
                               action='store_true',
                               default=False,
                               help='Log all database queries')
    logging_options.add_option('', '--no-progress-bar',
                               action='store_false',
                               default=True,
                               dest='enable_progress_bar',
                               help='Disable the progress bar')
    parser.add_option_group(logging_options)

    parser.add_option('-s', '--sleep',
                      type='float',
                      default='0.2',
                      metavar='SECONDS',
                      help='Sleep for the given number of seconds between each api.met.no query'
                      )
    parser.add_option('', '--station',
                      metavar='STATIONID',
                      type='int',
                      action='append',
                      dest='station_list',
                      help='Only process the stations given here'
                      )
    parser.add_option('', '--from-first-time',
                      action='store_true',
                      help='Instead of starting data save from the next of 6 or 18 hours, save data starting now, until 6 or 18 hours.'
                      )

    options, args = parser.parse_args()

    add_to_options(options, '/etc/kvalobs/kvalobs.conf')

    if not len(args) == 0:
        print('Unrecognized argument(s):', args, file=sys.stderr)
        sys.exit(1)

    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    try:
        log.setLevel(LEVELS[options.log_level])
    except KeyError:
        print('Invalid value for log-level: <%s>. Using <info> instead.' % (
            options.log_level,), file=sys.stderr)
        log.setLevel(logging.INFO)

    if options.logfile:
        handler = logging.handlers.RotatingFileHandler(
            options.logfile, maxBytes=4*1024*1024, backupCount=10)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s"))
        log.addHandler(handler)
        if options.log_queries:
            query_log.addHandler(handler)
            query_log.setLevel(logging.INFO)

    stderrLogger = logging.StreamHandler(sys.stderr)
    if options.logfile:
        stderrLogger.setLevel(logging.CRITICAL)
    else:
        stderrLogger.setLevel(LEVELS[options.log_level])
    log.addHandler(stderrLogger)

    if options.log_queries:
        query_log.addHandler(stderrLogger)
        query_log.setLevel(logging.INFO)

    if options.statusfile:
        statusHandler = logging.handlers.RotatingFileHandler(
            options.statusfile, maxBytes=4*1024*1024, backupCount=1)
        statusHandler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s"))
        status_log.addHandler(statusHandler)
        status_log.setLevel(logging.INFO)

    try:
        status_log.info("START")
        populate_kvalobs(options)
        status_log.info("STOP")
    except Exception as msg:
        log.fatal(msg)
        status_log.fatal(msg)
        status_log.info("STOP")
        raise


if __name__ == '__main__':
    main()
