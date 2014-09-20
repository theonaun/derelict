#!/usr/bin/env python2
'''This is the main program which orchestrates notification actions.'''

# Regular Modules
import datetime
import multiprocessing
import os
import sys
import time

# Setup items, automatic run. Lazy, bad Python.
import first_setup
from notifier_settings import settings_dict

# Database functions
from db_functions import cull
from db_functions import update_local_db
from db_functions import populate_choices

# Communication processes 
from communication import emailer
from communication import twitter_push
from communication.twitter_pull import Puller_Process
from communication.twitter_callback import Authentication_Fielder
from communication.twitter_server import Authentication_Server
from communication.twitter_push import Pusher_Process

# Other
from other import sleep_til_11

# Add local directory to path for local imports and debugging purposes
APP_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(APP_DIR)

def main():
    ########### Update loop
    while True:
        # Update local db
        print "Synchronize."
        update_local_db.synchronize()
        # Create csv files of all db fields
        print "Populate choices."
        populate_choices.to_local_csv()
        # Daily email batch (includes daily and weekly)
        if settings_dict['email_notifications'].lower() == 'on':
            print "Emailing."
            emailer.send()
        else:
            print "Email functionality is off."
        # Daily tweet
        if settings_dict['twitter_notifications'].lower() == 'on':
            print "Twitter functionality is on."
        else:
            print "Twitter functionality is off."
        # Cull db on a weekly basis
        now = datetime.datetime.now()
        print "Cull turned off for debug purposes. notifier_daemon.py line 57."
        '''
        if now.weekday() == 5:
            cull.cull()
        '''
        # Sleep til 11am tomorrow
        sleep_til_11.sleep()
        
if __name__ == '__main__':
    if settings_dict['twitter_notifications'].lower() == 'on':
        # Queues for interprocess communication
        puller_to_fielder_queue = multiprocessing.Queue()
        server_to_fielder_queue = multiprocessing.Queue()
        fielder_to_pusher_queue = multiprocessing.Queue()
        # Start processes
        Puller_Process(puller_to_fielder_queue).start()
        Pusher_Process(fielder_to_pusher_queue).start()
        Authentication_Fielder(puller_to_fielder_queue, 
                               server_to_fielder_queue,
                               fielder_to_pusher_queue).start()
        Authentication_Server(server_to_fielder_queue).start()
    main()


