
import datetime
import os
import sqlite3
import time
import traceback
import urllib

from multiprocessing import Process
from multiprocessing import Queue

import tweepy

from notifier_settings import settings_dict

class Pusher_Process(Process):
    '''Push tweets, create text files.'''
    def __init__(self, fielder_to_pusher_queue):
        Process.__init__(self)
        self.APP_DIR = os.path.dirname(os.path.dirname(\
                           os.path.realpath(__file__)))
        self.DATA_DIR = os.path.join(self.APP_DIR, 'data')
        self.DB_PATH = os.path.join(self.DATA_DIR, 'push_data.db')
        self.my_access_key = settings_dict['access_key']
        self.my_access_secret = settings_dict['access_secret']
        self.auth = tweepy.OAuthHandler(settings_dict['consumer_key'],
                                        settings_dict['consumer_secret'])
        self.fielder_to_pusher_queue = fielder_to_pusher_queue
        self.api = tweepy.API(self.auth)
        self.running = True

    def run(self):
        print 'Starting Pusher Process ...'
        self.create_db_if_not_existing()
        while self.running == True:
            self.add_list_to_db()
            spool_list = self.spool_tweets()
            # Skip sending tweets if list is empty.
            if spool_list:
                self.send_tweets(spool_list)
            time.sleep(60)

    def kill(self):
        self.running == False
        self.join()
        
    def spool_tweets(self):
        '''Spool tweets for sending.'''
        # Create data containers
        new_complaints_in_memory = []
        req_db_in_memory = []
        tweets_to_post = []
        # Local copy of db to memory
        try:
            conn = sqlite3.connect(os.path.join(self.DATA_DIR, 
                                                'local_cfpb.db'))
            cursor = conn.cursor()
            # Get new items
            date_obj = datetime.datetime.now()
            date_str = ''.join([str(date_obj.year),
                       '-',
                       str(date_obj.month).zfill(2),
                       '-',
                       str(date_obj.day).zfill(2)])
            for row in cursor.execute('SELECT * FROM local_cfpb_db '
                                      'WHERE pull_date=?', (date_str,)):
                new_complaints_in_memory.append(row)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            traceback.print_exc()
            raise(e)
        finally:
            conn.close()
        # Get requests
        try:
            conn = sqlite3.connect(os.path.join(self.DATA_DIR, 
                                                'push_data.db'))
            cursor = conn.cursor()
            for row in cursor.execute('SELECT * FROM push_data'):
                req_db_in_memory.append(row)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            traceback.print_exc()
            raise(e)
        finally:
            conn.close()
        # For each request , check local db.
        for request in req_db_in_memory:
            #req_key = request[0]
            #req_twitter_id = request[1]
            req_screen_name = request[2]
            req_company = request[3]
            req_product = request[4]
            req_issue = request[5]
            #req_unix_timestamp = request[6]
            #req_confirmation_status = request[7]
            #req_push_status = request[8]
            #req_callback_url = request[9]
            #req_access_token = request[10]
            #req_access_verifier = request[11]
            req_access_key = [12]
            req_access_secret = [13]
            #req_last_run_date = [14]
            for complaint in new_complaints_in_memory:
                #com_key = complaint[0]
                com_product = complaint[1]
                com_sub_product = complaint[2]
                com_company = complaint[3]
                #com_date_sent_to_company = complaint[4]
                #com_consumer_disputed = complaint[5]
                #com_date_received = complaint[6]
                com_complaint_id = complaint[7]
                #com_state = complaint[8]
                #com_timely_response = complaint[9]
                #com_submitted_via = complaint[10]
                com_issue = complaint[11]
                #com_company_response = complaint[12]
                #com_zip_code = complaint[13]
                com_pull_date = complaint[14]
                # Match 
                if req_company == com_company:
                    if req_product == 'All' or req_product == com_product:
                        if req_issue == 'All' or req_issue == com_issue:  
                            print str('Spooling ' +  str(com_complaint_id))
                            tweets_to_post.append([req_screen_name,
                                                   req_access_key,
                                                   req_access_secret,
                                                   req_company,
                                                   req_product,
                                                   req_issue])
        return tweets_to_post                    
                                                                         
    def send_tweets(self, tweets_to_post):
        tweet_screen_name = tweets_to_post[0]
        tweet_access_key = tweets_to_post[1]
        tweet_access_secret = tweets_to_post[2]
        tweet_company = tweets_to_post[3]
        tweet_product = tweets_to_post[4]
        tweet_issue = tweets_to_post[5]
        for tweet in tweets_to_post:
            self.auth = tweepy.OAuthHandler(settings_dict['consumer_key'],
                                            settings_dict['consumer_secret'])
            self.auth.set_access_token(tweet_access_key,
                                       tweet_access_secret)
            self.api = tweepy.API(self.auth)
            self.api.update_status(''.join(['New complaints for your request: ',
                                            tweet_company,
                                            ':',
                                            tweet_product,
                                            ':',
                                            tweet_issue,
                                            '\n\nGenerously underwritten by ',
                                            'absolutely no one.']))
    '''
    For dynamic table generation (TODO)
    '\n\n',
                                            'http://www.theonaunheim.com/',
                                            'reporting',
                                            '?',
                                            'company='
                                            urllib.quote(tweet_company),
                                            '&',
                                            'product='
                                            urllib.quote(tweet_product),
                                            '&',
                                            'issue='
                                            urllib.quote(tweet_issue),
   '''
        
    def add_list_to_db(self):
        while self.fielder_to_pusher_queue.qsize() > 0:
            passed_list = self.fielder_to_pusher_queue.get()
            key = passed_list[0]
            twitter_id = passed_list[1]
            screen_name = passed_list[2]
            company = passed_list[3]
            product = passed_list[4]
            issue = passed_list[5]
            unix_timestamp = passed_list[6]
            confirmation_status = passed_list[7]
            push_status = passed_list[8]
            callback_url = passed_list[9]
            access_token = passed_list[10]
            access_verifier = passed_list[11]
            access_key = passed_list[12]
            access_secret = passed_list[13]
            try:
                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute('INSERT INTO push_data VALUES '
                               '(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                               (twitter_id, screen_name, company, product,
                                issue, unix_timestamp, confirmation_status,
                                push_status, callback_url, access_token,
                                access_verifier, access_key, access_secret,
                                None))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                traceback.print_exc()
                raise(e)
            finally:
                conn.close()

    def create_db_if_not_existing(self):
        # if database does not exist, create
        if not os.path.exists(os.path.join(self.DATA_DIR, 
                                           'push_data.db')):
            try:
                conn = sqlite3.connect(os.path.join(self.DATA_DIR, 
                                                    'push_data.db'))
                cursor = conn.cursor()
                cursor.execute('CREATE TABLE push_data (key INTEGER '
                               'PRIMARY KEY, twitter_id TEXT, '
                               'screen_name TEXT, company TEXT, product TEXT, '
                               'issue TEXT, unix_timestamp TEXT, '
                               'confirmation_status TEXT, push_status TEXT, '
                               'callback_url TEXT, access_token TEXT, '
                               'access_verifier_TEXT, access_key TEXT, '
                               'access_secret TEXT, last_run_date TEXT)')                      
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


