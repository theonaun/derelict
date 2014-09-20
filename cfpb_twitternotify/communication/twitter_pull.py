import difflib
import os
import pickle
import time

from multiprocessing import Process

import tweepy

from notifier_settings import settings_dict

class Puller_Process(Process):
    def __init__(self, puller_to_fielder_queue):
        Process.__init__(self)
        self.running = True
        self.CONSUMER_KEY = settings_dict['consumer_key']
        self.CONSUMER_SECRET = settings_dict['consumer_secret']
        self.ACCESS_KEY = settings_dict['access_key']
        self.ACCESS_SECRET = settings_dict['access_secret']
        self.READ_ACCOUNT_NAME = settings_dict['twitter_read_account']
        self.puller_to_fielder_queue = puller_to_fielder_queue
        APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        DATA_DIR = os.path.join(APP_DIR, 'data')
        self.data_path = DATA_DIR

    def run(self):
        '''TODO: Break this down into separate functions for D.R.Y.'''
        print "Puller_Process starting."
        auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        auth.set_access_token(self.ACCESS_KEY, self.ACCESS_SECRET)
        self.api = tweepy.API(auth)
        user = self.api.get_user(settings_dict['twitter_read_account'])
        while self.running == True:
            # Check every 5 minutes rate limiting.
            time.sleep(300)
            # Try to get csv files. If non-existant, keep looping until they do
            try:
                issue_path = os.path.join(self.data_path, 'issues.csv')
                issue_list = open(issue_path).read().replace('\"','').split('\n')
                comp_path = os.path.join(self.data_path, 'companies.csv')
                comp_list = open(comp_path).read().replace('\"','').split('\n')               
                prod_path = os.path.join(self.data_path, 'products.csv')
                prod_list = open(prod_path).read().replace('\"','').split('\n')
            except IOError:
                print "No csv files, line 43 twitter_pull.py. Continue."
                continue
            # Get last pulled number. Create if nonexistant.
            try:
                file_path = os.path.join(self.data_path, 'last_tweet.p')
                last_pulled = pickle.load(open(file_path, 'rb'))
            except IOError: #NameError:
                last_pulled = 471010602681647105
                pickle.dump(last_pulled, open(file_path, 'wb'))
            # Pull statuses based on last pulled number. IndexError = no new.
            # format is 471010602681647105.
            try:
                # Enough for one every 30 seconds
                mentions = self.api.mentions_timeline(count=10)
                # Remove items older than last pulled.
                mentions = filter(lambda x: x.id > last_pulled, mentions)
                # Get most recent tweet number. If no new, last pulled.
                try:
                    newest = max(map(lambda x: x.id, mentions))
                except ValueError:
                    newest = last_pulled
                file_path = os.path.join(self.data_path, 'last_tweet.p')
                pickle.dump(newest, open(file_path, 'wb'))
            # No new, restart loop.
            except (IndexError, tweepy.TweepError) as e:
                print e
                continue
            # For each new status, put in queue as tuple(screen_name, text)
            for status in mentions:
                # Rate limit
                time.sleep(60)
                # Update last_pulled for newer item to prevent 
                if int(status.id) > last_pulled:
                    last_pulled = status.id
                # Needs to be followers so they can be sent things.
                screen_name = status.user.screen_name
                # Ignore own tweets
                twit_id = status.user.id
                text = status.text
                # Comptonents should be request:company:product:issue
                text_components = text.split(':')
                # FIX FOR D.R.Y.
                if not twit_id in self.api.followers_ids():
                    try:
                        self.api.update_status(''.join(['@',
                                               screen_name,
                                               ' ',
                                               'Error. You must be a follower ',
                                               'to properly authenticate.']))
                        continue
                    except tweepy.TweepError as e:
                        print e
                        continue
                if not 'request' in text_components[0].lower().lstrip():
                    try:
                        self.api.update_status(''.join(['@',
                                               screen_name,
                                               ' ',
                                               'Error. You must be a follower ',
                                               'and request format is: ',
                                               'request:company_here:',
                                               'product_here:issue_here']))
                        continue
                    except tweepy.TweepError as e:
                        print e
                        continue
                #
                item_list = [

                             (text_components[1],
                              comp_list, 
                              screen_name, 
                              'companies.csv'),

                             (text_components[2], 
                              prod_list, 
                              screen_name,
                              'products.csv'),

                             (text_components[3],
                              issue_list, 
                              screen_name, 
                              'issues.csv')

                            ]
                # CHeck validity of inputs. If invalid, inform poster and
                # continue loop
                reset_toggle = []
                for item in item_list:
                    reset_toggle.append(self.text_check(*item))
                if 'post made' in reset_toggle:
                    print "Bad request ..."
                    continue
                
                # If it makes it this far, finally add to queue as dict
                self.puller_to_fielder_queue.put({'twitter_id':twit_id,
                                                  'screen_name':screen_name,
                                                  'company':text_components[1],
                                                  'product':text_components[2],
                                                  'issue':text_components\
                                                  [3].rstrip()}) 
            # Last pulled to file.
            file_path = os.path.join(self.data_path, 'last_tweet.p')
            pickle.dump(last_pulled, open(file_path, 'wb'))
            print 'Ln150_pull qsize ' +  
                  str(self.puller_to_fielder_queue.qsize())
            

    def text_check(self,
                   text_component,
                   split_list,
                   screen_name,
                   csv_file_name):
        if not text_component in split_list:
            try:
                guess = difflib.get_close_matches(text_component,
                                                  split_list)[0]
                try:
                    self.api.update_status(''.join(['@',
                                                    screen_name,
                                                    ' ',
                                                    'no match for \"',
                                                    text_component,
                                                    '\". Did you mean \"',
                                                    guess,
                                                    '\"?']))
                    return 'post made'
                except tweepy.TweepError as e:
                    print e
            except IndexError:
                try:
                    self.api.update_status(''.join(['@',
                                           screen_name,
                                           ' \"',
                                           text_component,
                                           '\" is not a valid choice. '
                                           'Try http://www.theonaunheim.com/',
                                           csv_file_name]))
                    return 'post made'
                except tweepy.TweepError as e:
                    print e                                     
                   
    def kill(self):
        self.running == False
        self.join()
 


