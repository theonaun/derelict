import datetime
import json
import os
import sqlite3  
import time
import urllib2
from collections import defaultdict

import notifier_settings

def synchronize():
    '''sync_local_db checks the log, and syncs with the CFPB database'''
    # Check 'log' table for last update, as indicated by 'Pull' field.
    try:
        APP_DIR = os.path.dirname(os.path.realpath(__file__))
        # Not really appdir
        APP_DIR = os.path.dirname(APP_DIR)
        conn = sqlite3.connect(os.path.join(APP_DIR,
                                            'data',
                                            'local_cfpb.db'))
        cursor = conn.cursor()
        # Get last pull date
        cursor.execute('SELECT max(key) FROM log WHERE event_type=\'Pull\'')
        last_pull_key = str(cursor.fetchone()[0])
        # Comma required at end of tuple to prevent unpacking
        cursor.execute('SELECT date from log WHERE key=?', (last_pull_key,))
        last_pull_date = str(cursor.fetchone()[0])
        # 2011-07-20 00:00:00.000001 to object
        last_pull_date = last_pull_date.replace('-',':')
        last_pull_date = last_pull_date.replace(' ',':')
        last_pull_date = last_pull_date.replace('.',':')
        last_pull_date = last_pull_date.split(':')
        last_pull_date = map(lambda x: int(x), last_pull_date)
        # Make into list, expand list
        last_pull_date_object = datetime.datetime(*last_pull_date)
        # last_pull_date_object = datetime.datetime(2014,1,20) # debug
        today_date_object = datetime.datetime.now()
        # Set up delta for incrementaiton \
        one_day_increment = datetime.timedelta(1)
        # Get items from settings.txt
        base_website = notifier_settings.settings_dict['base_website']
        #  If already has been run today, return True and short circuit.
        if (today_date_object - last_pull_date_object) < one_day_increment:
            print 'Last pull less than 24 hours ago. Stopping pull loop.'
            conn.commit()
            return True
        # Pull loop
        while today_date_object >= last_pull_date_object:
            date_string = ''.join([str(last_pull_date_object.year),
                                  '-',
                                  str(last_pull_date_object.month).zfill(2),
                                  '-',
                                  str(last_pull_date_object.day).zfill(2),
                                  'T00:00:00'])
            print ''.join([str(datetime.datetime.now()),
                          ': Pulling data for ',
                           date_string])
            # Formatted query looks like this: http://data.consumerfinance.gov/
            #resource/x94z-ydhh.json?date_received=2012-10-10T00:00:00'
            url = ''.join([notifier_settings.settings_dict['base_website'],
                          date_string])
            # Get raw data from CFPB's restful API
            try:
                web_request = urllib2.urlopen(url)
                web_response = web_request.read()
                web_request.close()
            except urllib2.URLError as err:
                print 'Bad pull. Waiting and repulling ...'
                time.sleep(30)
                web_request = urllib2.urlopen(url)
                web_response = web_request.read()
                web_request.close()
            loaded_json = json.loads(web_response)
            for complaint in loaded_json:
                # Complaints prior to December 2011 have no sub_product.
                # Insert 'Null'
                complaint = defaultdict(lambda: None, complaint)
                cursor.execute('INSERT INTO local_cfpb_db VALUES' +
                               '(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,' +
                               '?, ?, ?, ?)', 
                               [
                               complaint['product'],
                               complaint['sub_product'],
                               complaint['company'],
                               complaint['date_sent_to_company'],
                               complaint['consumer_disputed'],
                               complaint['date_received'],
                               complaint['complaint_id'],
                               complaint['state'],
                               complaint['timely_response'],
                               complaint['submitted_via'],
                               complaint['issue'],
                               complaint['company_response'],
                               complaint['zip_code'],
                               str(str(datetime.datetime.now().year) + 
                                   '-' +
                                   str(datetime.datetime.now().month).zfill(2) +
                                   '-' +
                                   str(datetime.datetime.now().day).zfill(2)
                                   )
                               ])
            conn.commit()
            # Increment by one day
            cursor.execute('INSERT INTO log VALUES (NULL, ?, ?, ?)',
                           (str(last_pull_date_object),
                           'Pull',
                           'Pull date: ' + str(today_date_object)))
            # Daily commit (put in for debugging)
            conn.commit()
            last_pull_date_object += one_day_increment
        # Check last 20 day, pull new items

############################
        ram_db_last_20 = []
        today_date_object = datetime.datetime.now()
        # Set up delta for incrementaiton \
        one_day_increment = datetime.timedelta(1)
        old_date_object = today_date_object - one_day_increment*20
        for x in range(0,20):
            date_string = ''.join([str(old_date_object.year),
                                  '-',
                                  str(old_date_object.month).zfill(2),
                                  '-',
                                  str(old_date_object.day).zfill(2),
                                  'T00:00:00'])
            print ''.join([str(datetime.datetime.now()),
                          ': Rechecking data for ',
                           date_string])
            url = ''.join([notifier_settings.settings_dict['base_website'],
                          date_string])
            # Get raw data from CFPB's restful API
            try:
                web_request = urllib2.urlopen(url)
                web_response = web_request.read()
                web_request.close()
            except sqlite3.Error as err:
                raise Exception(''.join(['Error: ', err.args[0]]))
            loaded_json = json.loads(web_response)
            for complaint in loaded_json:
                # Complaints prior to December 2011 have no sub_product.
                # Insert 'Null'
                complaint = defaultdict(lambda: None, complaint)
                ram_db_last_20.append([complaint['product'],
                                       complaint['sub_product'],
                                       complaint['company'],
                                       complaint['date_sent_to_company'],
                                       complaint['consumer_disputed'],
                                       complaint['date_received'],
                                       complaint['complaint_id'],
                                       complaint['state'],
                                       complaint['timely_response'],
                                       complaint['submitted_via'],
                                       complaint['issue'],
                                       complaint['company_response'],
                                       complaint['zip_code'],
                                       str(str(datetime.datetime.now().year) + 
                                       '-' +
                                       str(datetime.datetime.now().month).\
                                       zfill(2) +
                                       '-' +
                                       str(datetime.datetime.now().day).zfill(2)
                                       )
                                      ])
            # Increment date
            old_date_object += one_day_increment
        # Check new items against DB. If new, place in db with new datetime
        dates_to_pull = []
        today_obj = datetime.datetime.now()
        one_day = datetime.timedelta(1)
        # While day is less than 20 days ago
        marker = today_obj-(one_day*20)
        while today_obj > marker:
            dates_to_pull.append(str(marker.year) + '-' +
                                 str(marker.month) + '-' +
                                 str(marker.day))
            marker += one_day 
        items_to_add = []
        local_complaint_numbers = []
        # Put all the complaint numbers for last 20 days in a list
        for date_str in dates_to_pull:
            for row in cursor.execute('SELECT * FROM local_cfpb_db '
                                      'WHERE pull_date=?', (date_str,)):
                local_complaint_numbers.append(row[7])
        # Compare numbers in last 20 days to ram_db_last_20
        for item in ram_db_last_20:
            if item[6] not in local_complaint_numbers:
                items_to_add.append(item)
        # After we have a list of items to add to the local db, add them
        for item in items_to_add:
            cursor.execute('INSERT INTO local_cfpb_db VALUES' +
                           '(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,' +
                           '?, ?, ?, ?)', item)
################################
        # Remove duplicates
        cursor.execute('DELETE FROM local_cfpb_db WHERE key NOT IN (SELECT '
                       'MAX(key) FROM local_cfpb_db GROUP BY complaint_id)')
        conn.commit()
    # Rollback if error         
    except NameError:#sqlite3.Error as err:
        conn.rollback()
        raise Exception(''.join(['Error: ', err.args[0]]))
