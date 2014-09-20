import datetime
import random
import hashlib
import os
import sqlite3
import threading
import time

import confirmation

global confirmation_pool
confirmation_pool = []

def create_local_request(email, frequency, company, product, sub_product):
    '''This function adds to the 'request' and 'hashes' tables.'''
    home_dir = os.getenv('HOME')
    # Request hash
    new_hash, hash_timestamp = request_hash(email,
                                            frequency,
                                            company,
                                            product)
    # Confirmation emails ... after 10 minutes garbage collection
    # check if a Confirmation object exists for current email, if not create
    # If empty create
    emails_in_pool = [ conf.email for conf in confirmation_pool ]
    print emails_in_pool
    if email in emails_in_pool:
        conf_object = confirmation_pool[emails_in_pool.index(email)]
    else:
        confirmation_pool.append(confirmation.Confirmation_Timer(email))
        emails_in_pool = [ conf.email for conf in confirmation_pool ]
    confirmation_pool[emails_in_pool.index(email)].add_request(new_hash)

    try:
        # Add to database
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        # Check if blacklisted
        blacklist_toggle = cursor.execute('SELECT blacklist FROM users WHERE'
                                           ' email=?', (email,))
        if blacklist_toggle == 1:
            try:
                cursor.execute('INSERT INTO log VALUES (NULL,?,?,?)',
                               (str(datetime.datetime.now()), 
                               'Attempt to add blacklisted email',
                               str(email)))
                return 0
            except sqlite3.Error:
                return 0
        date_last_run = 'Null'
        # Insert entry into 'requests' table
        cursor.execute('INSERT INTO requests VALUES (NULL,?,?,?,?,?,?,?,?)',
                          (email, frequency, company, product, sub_product,
                           new_hash, str(datetime.datetime.now()), 0))
        new_request_id = int(cursor.lastrowid)
        # Insert record into 'log' table.
        cursor.execute('INSERT INTO log VALUES (NULL,?, ?, ?)',
                       (str(datetime.datetime.now()),
                       'Request entered-req_id:hash',
                       ''.join([str(new_request_id), ':', new_hash])))            
        conn.commit()   
    except IndexError as err:
        conn.rollback()
        raise Exception(''.join(['Error: ', err.args[0]]))
        
def delete_local_request(delete_hash):
    '''Deletes a local hash.'''
    home_dir = os.getenv('HOME')
    try:
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        # Lookup hash to get id in hash table. Delete from requests table.
        cursor.execute('SELECT key FROM requests WHERE \
                        new_hash=?', (delete_hash,))
        row_key = cursor.fetchone()[0]
        cursor.execute('DELETE FROM requests WHERE key=?', (row_key,))
        conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        raise Exception(''.join(['Error: ', err.args[0]]))
    return True
        
def request_hash(email, frequency, company, product):
    home_dir = os.getenv('HOME')
    hash_timestamp = str(datetime.datetime.now())
    hash_base = ''.join([hash_timestamp,
                        email,
                        frequency,
                        company,
                        product,
                        # /dev/urandom salt
                        os.urandom(1)])
    new_hash = hashlib.sha256(hash_base).hexdigest()
    return new_hash, hash_timestamp
       
def confirm_request(confirmation_hash):
    '''Takes a hash, and turns makes a request entry spool-able.'''
    print 
    home_dir = os.getenv('HOME')
    try:
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        # Update confirmation status in request table
        cursor.execute('UPDATE requests SET confirmed=1 WHERE new_hash=?',
                       (str(confirmation_hash),))
        cursor.execute('INSERT INTO log VALUES (NULL,?,?,?)',
                      (str(datetime.datetime.now()), 
                       'Confirmation', confirmation_hash))                                 
        # Commit changes
        conn.commit()
        conn.close()
    except TypeError:#sqlite3.Error as err:
        conn.rollback()
        raise Exception(''.join(['Error: ', err.args[0]]))
    return True
