
import os
import sqlite3
import time
import traceback

from multiprocessing import Process
from multiprocessing import Queue
from Queue import Empty

import tweepy

from notifier_settings import settings_dict

class Authentication_Fielder(Process):
    '''First request goes through. Then token goes through.'''
    def __init__(self, puller_to_fielder_queue, 
                       server_to_fielder_queue,
                       fielder_to_pusher_queue):
        Process.__init__(self)
        self.running = True
        self.puller_to_fielder_queue = puller_to_fielder_queue
        self.server_to_fielder_queue = server_to_fielder_queue
        self.fielder_to_pusher_queue = fielder_to_pusher_queue
        self.APP_DIR = os.path.dirname(os.path.dirname(\
                           os.path.realpath(__file__)))
        self.DATA_DIR = os.path.join(self.APP_DIR, 'data')
        self.DB_PATH = os.path.join(self.DATA_DIR, 'twitter_data.db')
        self.my_access_key = settings_dict['access_key']
        self.my_access_secret = settings_dict['access_secret']
        self.auth = tweepy.OAuthHandler(settings_dict['consumer_key'],
                                        settings_dict['consumer_secret'],
                                        settings_dict['twitter_callback_url'])
        self.api = tweepy.API(self.auth)

    def run(self):
        self.create_db_if_not_existing()
        while self.running == True:
            # queue to db
            self.commit_queue_data()
            self.shift_to_pusher()
            time.sleep(60)
    
    def shift_to_pusher(self):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            for row in cursor.execute('SELECT R.key, R.twitter_id, '
                           'R.screen_name, '
                           'R.company, R.product, R.issue, R.unix_timestamp, '
                           'R.confirmation_status, R.push_status '
                           ' FROM requests AS R JOIN auth_credentials as A ON '
                           'R.screen_name=R.screen_name'):
                if row[7] == 'yes' and row[8] == 'no':
                    self.fielder_to_pusher_queue.put(row)
                    cursor.execute('UPDATE requests SET push_status=yes '
                                   'WHERE key=?', (row[0],))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            traceback.print_exc()
            raise(e)
        finally:
            conn.close()
    
    def commit_queue_data(self):
        # Pull request
        try:
            request = self.puller_to_fielder_queue.get_nowait() 
        except Empty:
            request = None
        # Pull auth
        try:
            authorization = self.server_to_fielder_queue.get_nowait()
        except Empty:
            authorization = None
        # Commit changes to DB
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            if request:
                # Insert request in to tables
                cursor.execute('INSERT INTO requests VALUES '
                               '(NULL,?,?,?,?,?,?,?,?)',
                               (request['twitter_id'],
                                request['screen_name'],
                                request['company'],
                                request['product'],
                                request['issue'],
                                int(time.time()),
                                'no'))
                #If no token in authorization table, add.
                cursor.execute('SELECT * FROM auth_credentials WHERE '
                               'screen_name=?', (request['screen_name'],))
                data = cursor.fetchone()
                # If no row exists with screenname, none returned.
                # generate access token and create new auth entry
                if not data:
                    self.auth.set_access_token(self.my_access_key,
                                               self.my_access_secret)
                    callback_url = auth.get_authorization_url()
                    token = callback_url.partition('?')[2].partition(':')[2]
                    cursor.execute('INSERT INTO auth_credentials VALUES '
                                   '(NULL,?,?,?,?,?,?)',
                                    (request['screen_name'],
                                     callback_url,
                                     token,
                                     None,
                                     None,
                                     None))
                # Send DM with link to requester.
                message = ''.join(['If you would like automatic updates ',
                                   ' related to ', 
                                   str(request['company']),
                                   ', please click this link: ',
                                   str(callback_url)])
                self.api.send_direct_message(request['screen_name'],
                                             message)
            if authorization:
                # Get auth token and verifier (dict)
                try:
                # Get key and secrett
                    self.auth.get_access_token(authorization['oauth_verifier'])
                except tweepy.TweepError as e:
                    print traceback.print_exc()
                # EXCHANGE FOR TOKEN AND PUT INTO SYSTEM
                cursor.execute('UPDATE auth_credentials SET '
                               'oauth_verifier=?, '
                               'access_key=?, '
                               'access_secret=?'
                               ' WHERE oauth_token=?',
                               (authorization['oauth_verifier'],
                                self.auth.access_token.key,
                                self.auth.access_token.secret,
                                authorization['oauth_token']))
                # Figure out screen name that goes with token
                cursor.execute('SELECT * FROM requests WHERE oauth_token=?',
                               (authorization['oauth_token'],))
                screen_name_string = cursor.fetchone()[1]
                #   
                cursor.execute('UPDATE requests SET '
                               'confirmation_status=yes, '
                               ' WHERE screen_name=?',
                               (screen_name_text,))
                # Change confirmation status to yes for screen name.
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            traceback.print_exc()
            raise(e)
        finally:
            conn.close()
    
    def create_db_if_not_existing(self):
        # if database does not exist, create
        if not os.path.exists(self.DB_PATH):
            try:
                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute('CREATE TABLE auth_credentials(key INTEGER '
                               'PRIMARY KEY, screen_name TEXT, '
                               'callback_url TEXT, access_token TEXT '
                               'access_verifier TEXT, access_key TEXT, '
                               'access_secret TEXT)')
                cursor.execute('CREATE TABLE requests(key INTEGER '
                               'PRIMARY KEY, twitter_id TEXT, screen_name TEXT,'
                               ' company TEXT, product TEXT, issue TEXT, '
                               'unix_timestamp INTEGER, confirmation_status '
                               'TEXT, push_status TEXT)')
                cursor.execute('CREATE TABLE log(key INTEGER PRIMARY KEY, '
                               'date INTEGER, event_type TEXT, '
                               'sub_event_type TEXT)')
                cursor.execute('INSERT INTO log VALUES (NULL,?,?,?)',
                               (int(time.time()), 'DB', 'DB creation'))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                traceback.print_exc()
                raise(e)
            finally:
                conn.close()
        # If database exists
        else:
            pass

    def kill(self):
        self.running == False
        self.join()



