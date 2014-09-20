#!/usr/bin/env python2
'''This is the main program which orchestrates notification actions.'''

import datetime
import os
import sys
import threading
import time

import first_setup # Automatically runs for lack of established function (lazy)
import notifier_settings

import cull
import email_
import test_server
import update_local_db
import populate_choices

current_working_directory = os.getcwd()
sys.path.insert(0, current_working_directory)

def main():
    # Need to better parrallelize
    global server_thread
    server_thread = test_server.Server_Thread()
    server_thread.start()
    ########### Update loop
    while True:
        # Daily update
        update_local_db.synchronize()
        populate_choices.to_local_db()
        email_.daily_spool()
        # Daily email batch (includes daily and weekly)
        email_.send()
        # Wait until next 11am
        now = datetime.datetime.now()
        if now.weekday() == 5:
            cull.cull()
        eleven_am_today = datetime.datetime(now.year,
                                            now.month,
                                            now.day,
                                            11, 0, 0, 0)
        one_day = datetime.timedelta(1)
        if now > eleven_am_today:
            time_until_next_11_am = eleven_am_today - now + one_day
        else:
            time_until_next_11_am = eleven_am_today - now
        print 'Sleeping until next runtime.'
        time.sleep(time_until_next_11_am.seconds)
        
if __name__ == '__main__':
    main()

