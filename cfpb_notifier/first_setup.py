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

# Make home directory if not already in place
home_dir = os.getenv('HOME')
if not os.path.exists(os.path.join(home_dir, '.cfpb_notifier')):
    os.mkdir(os.path.join(home_dir, '.cfpb_notifier'))
# Make sqlite3 database if not already in place
if not os.path.exists(os.path.join(home_dir, '.cfpb_notifier', 'notify.db')):
    conn = sqlite3.connect(os.path.join(home_dir, 
                                        '.cfpb_notifier',
                                        'notify.db'))
    cursor = conn.cursor()
if not os.path.exists(os.path.join(home_dir, '.cfpb_notifier', 'settings.txt')):
    with open(os.path.join(home_dir, 
                           '.cfpb_notifier', 
                           'settings.txt'),"w+") as settings_file:
        # Write base website, universal view, and search prefix to file                   
        settings_file.write('base_website:http://data.consumerfinance.gov/' +
                            'resource/x94z-ydhh.json?date_received=\n' +
                            'username:username\n' +
                            'password:password\n' +
                            'outbound_server:smtpserver\n' +
                            'outbound_port:3325\n' +
                            'sender_name:sendername\n' +
                            'application_dir:directory\n' +
                            'webhost:http://www.webpage.com/tuzigoot/')
    try:
        # 'local_cfpb_db' is a local copy of the main CFPB compalint database
        cursor.execute('CREATE TABLE local_cfpb_db(key INTEGER PRIMARY KEY, '
                       'product TEXT, sub_product TEXT, '
                       'company TEXT, date_sent_to_company TEXT, '
                       'consumer_disputed TEXT, date_received TEXT, '
                       'complaint_id INTEGER, state TEXT, '
                       'timely_response TEXT, submitted_via TEXT, '
                       'issue TEXT, company_response TEXT, zip_code TEXT, '
                       'pull_date TEXT)')                     
        # 'requests' stores client's request criteria 
        cursor.execute('CREATE TABLE requests(key INTEGER PRIMARY KEY, '
                       'email TEXT, frequency TEXT, company TEXT, '
                       'product TEXT, sub_product TEXT, new_hash TEXT, '
                       'date_last_run TEXT, confirmed INTEGER)')
        # 'spool' stores a list of the outgoing items
        cursor.execute('CREATE TABLE spool(key INTEGER PRIMARY KEY, '
                       'email TEXT, complaintID TEXT, company TEXT, '
                       'product TEXT, sub_product TEXT, frequency TEXT)') 
        # 'log' stores a list of major database actions                
        cursor.execute('CREATE TABLE log(key INTEGER PRIMARY KEY, '
                       'date TEXT, event_type TEXT, sub_event_type TEXT)')
        # This is important as it lets us know how far back we need to get data.
        day_before_CFPB_database_inception = str(datetime.datetime(2011, 7, 20,
                                                                   0, 0, 0, 1))
        # 'users' has a list of all users
        cursor.execute('CREATE TABLE users(key INTEGER PRIMARY KEY, '
                       'email TEXT, blacklist_hash TEXT, is_active INTEGER, '
                       'blacklist INTEGER, user_since TEXT)')
        # Place CFPB Complaints Database inception database in log.
        # This is important as it lets us know how far back we need to get data.
        day_before_CFPB_database_inception = str(datetime.datetime(2011, 7, 20,
                                                                   0, 0, 0, 1))
        cursor.execute('INSERT INTO log VALUES (NULL,?,?,?)',
                      (day_before_CFPB_database_inception, 
                       'Pull', 'CFPB database created'))                                 
        # Commit changes
        conn.commit()
        conn.close()
    # Rollback if error         
    except IndexError:#sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))

