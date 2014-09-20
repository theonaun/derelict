'''first_setup.py sets up a number of items required for the notifier to work.

   first_setup.py performs the following actions:
   1. Sets up an sqlite database;
   2. Fills the database with information from the CFPB complaint database; and,
   3. Manages the setup of a number of ancillary items.
   
'''

import datetime
import os
import sqlite3
import sys

APP_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(APP_DIR)

# Make data folder
if not os.path.exists(os.path.join(APP_DIR, 'data')):
    os.mkdir(os.path.join(APP_DIR, 'data'))
# Make sqlite3 database if not already in place
if not os.path.exists(os.path.join(APP_DIR, 'data', 'local_cfpb.db')):
    conn = sqlite3.connect(os.path.join(APP_DIR, 
                                        'data',
                                        'local_cfpb.db'))
    cursor = conn.cursor()
    # 'local_cfpb_db' is a local copy of the main CFPB compalint database
    cursor.execute('CREATE TABLE local_cfpb_db(key INTEGER PRIMARY KEY, '
                   'product TEXT, sub_product TEXT, '
                   'company TEXT, date_sent_to_company TEXT, '
                   'consumer_disputed TEXT, date_received TEXT, '
                   'complaint_id INTEGER, state TEXT, '
                   'timely_response TEXT, submitted_via TEXT, '
                   'issue TEXT, company_response TEXT, zip_code TEXT, '
                   'pull_date TEXT)')                     
    # 'log' stores a list of major database actions                
    cursor.execute('CREATE TABLE log(key INTEGER PRIMARY KEY, '
                   'date TEXT, event_type TEXT, sub_event_type TEXT)')
    # This is important as it lets us know how far back we need to get data.
    day_before_CFPB_database_inception = str(datetime.datetime(2011, 7, 20,
                                                               0, 0, 0, 1))
    # Place CFPB Complaints Database inception database in log.
    # This is important as it lets us know how far back we need to get data.
    day_before_CFPB_database_inception = str(datetime.datetime(2011, 7, 20,
                                                               0, 0, 0, 1))
    cursor.execute('INSERT INTO log VALUES (NULL,?,?,?)',
                  (day_before_CFPB_database_inception, 
                   'Pull', 'CFPB database created'))   
    conn.commit()
    conn.close()
# Settings file.
if not os.path.exists(os.path.join(APP_DIR, 'data', 'settings.txt')):
    with open(os.path.join(APP_DIR, 
                           'data', 
                           'settings.txt'),"w+") as settings_file:
        # Write base website, universal view, and search prefix to file                   
        settings_file.write('twitter_notifications:off\n' +
                            'email_notifications:off\n' +
                            'base_website:http://data.consumerfinance.gov/' +
                            'resource/x94z-ydhh.json?date_received=\n' +
                            'username:username_here\n' +
                            'password:password_here\n' +
                            'outbound_server:server.com\n' +
                            'outbound_port:587\n' +
                            'sender_name:username@server.com\n' +
                            'consumer_key:key\n' +
                            'consumer_secret:secret\n' +
                            'access_key:key\n' +
                            'access_secret:secret\n' +
                            'twitter_read_account:account_name\n' +
                            'twitter_callback_url:' +
                            'http://www.theonaunheim.com/auth/\n')
# CSV file
if not os.path.exists(os.path.join(APP_DIR, 'data', 'requests.csv')):
    with open(os.path.join(APP_DIR, 
                           'data', 
                           'requests.csv'),"w+") as req_file:
        req_file.write('\"Email\",\"Company\",\"Product\",\"Issue\"')




