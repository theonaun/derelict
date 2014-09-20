import datetime  
import time

def sleep():
    now = datetime.datetime.now()
    # Wait until next 11am
    eleven_am_today = datetime.datetime(now.year,
                                        now.month,
                                        now.day,
                                        11, 0, 0, 0)
    one_day = datetime.timedelta(1)
    if now > eleven_am_today:
        time_until_next_11_am = eleven_am_today - now + one_day
    else:
        time_until_next_11_am = eleven_am_today - now
    print 'Update loop sleeping until next runtime.'
    time.sleep(time_until_next_11_am.seconds)
