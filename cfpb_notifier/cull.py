'''Cull removes old items that have been removed from the CFPB db.'''

import datetime
import json
import os
import sqlite3
import urllib2

import notifier_settings

def cull():
    '''Main function in this module.'''
    # Check 'log' table for last update, as indicated by 'Pull' field.
    # Get website data
    print ''.join([str(datetime.datetime.now()), 
                   ': Pulling data for validation of local db.'])
    home_dir = os.getenv('HOME')
    try:
        home_dir = os.getenv('HOME')
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        init_date = datetime.datetime(2011, 7, 20)
        today = datetime.datetime.now()
        one_day_delta = datetime.timedelta(1)
        complaints_in_mem = []
        while today >= init_date:
            date_string = ''.join([str(init_date.year),
                                  '-',
                                  str(init_date.month).zfill(2),
                                  '-',
                                  str(init_date.day).zfill(2),
                                  'T00:00:00'])
            # Formatted query looks like this: http://data.consumerfinance.gov/
            #resource/x94z-ydhh.json?date_received=2012-10-10T00:00:00'
            url = ''.join([notifier_settings.settings_dict['base_website'],
                          date_string])
            # Get raw data from CFPB's restful API
            try:
                web_request = urllib2.urlopen(url)
                web_response = web_request.read()
                web_request.close()
                json_data = json.loads(web_response)
            except IOError:
                print "Failure to pull for " + date_string
            for item in json_data:
                complaints_in_mem.append(str(item['complaint_id']))
            # DEBUG  init_date += one_day_delta*90
            init_date += one_day_delta
        print 'Number of entries in current db: ' + str(len(complaints_in_mem))
        # Done with loop
        conn.close()
    except (sqlite3.Error, IndexError) as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
    # Delete log tail
    try:
        print ''.join([str(datetime.datetime.now()), 
                      ': Cull recently deleted complaints.'])
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        count = int(cursor.execute('SELECT COUNT(key) FROM log').fetchone()[0])
        if count > 5000:
            number_to_cut = count - 5000
            cursor.execute('DELETE FROM log ORDER BY key LIMIT ' +
                           str(number_to_cut))
            print 'Chopping log length to 5000'
        conn.commit()
        conn.close()
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
    try:
        print ''.join([str(datetime.datetime.now()), 
                      ': Cull recently deleted complaints.'])
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        local_db_ids = []
        for row in cursor.execute('SELECT DISTINCT complaint_id FROM '
                                  'local_cfpb_db'):
            local_db_ids.append(str(cursor.fetchone()[0]))
        # Ensure ints
        local_db_ids = [ int(item) for item in local_db_ids ]
        complaints_in_mem = [ int(item) for item in complaints_in_mem ]
        for complaint in complaints_in_mem:
            if complaint not in local_db_ids:
                cursor.execute('DELETE FROM local_cfpb_db WHERE complaint_id=?',
                               (complaint,))
                print 'Culling item: ' + str(complaint)
        conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
    # If no items
    except TypeError:
        pass
    print ''.join([str(datetime.datetime.now()), 
                   ': Culling process complete.'])
