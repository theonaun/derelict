'''email.py handles email construction and email sending.'''

import datetime
import email
import os
import smtplib
import sqlite3
import time

import notifier_settings

# Warning: this presumes that you have a valid SMTP server on this machine.

def daily_spool():
    '''Takes 'request' rules and turns them into info for 'spool' table.'''
    try:
        print 'Running daily spool.'
        requests_in_memory = []
        home_dir = os.getenv('HOME')
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()    
        # Get last spool date
        try:
            cursor.execute('SELECT max(key) FROM log WHERE '
                           'event_type=\'Spool\'')
            last_spool_key = str(cursor.fetchone()[0])
            # Comma required at end of tuple to prevent unpacking
            cursor.execute('SELECT date from log WHERE key=?', 
                           (last_spool_key,))
            last_spool_date = str(cursor.fetchone()[0])
            print "Last spool " + last_spool_date
            # 2011-07-20 00:00:00.000001 to object
            last_spool_date = last_spool_date.replace('-',':')
            last_spool_date = last_spool_date.replace(' ',':')
            last_spool_date = last_spool_date.replace('.',':')
            last_spool_date = last_spool_date.split(':')
            last_spool_date = map(lambda x: int(x), last_spool_date)
            # Make into list, expand list
            last_spool_object = datetime.datetime(*last_spool_date)
            now = datetime.datetime.now()
            if (last_spool_object.year, 
                last_spool_object.month, 
                last_spool_object.day) == (now.year, now.month, now.day):
                # Short circuit spool
                print 'Last spool occurred today. No spool required.'
                return 0                 
        except (TypeError, IndexError, sqlite3.Error):
            # Index error means no spools have ever occured (possibly)
            pass
        # Convert requests to spooled emails.
        # For each item in 'requests' load into memory (list of lists)
        for row in cursor.execute('SELECT * FROM requests'):
            req_email = row[1]
            req_frequency = row[2]
            req_company = row[3]
            req_product = row[4]
            req_sub_product = row[5]
            req_hash = row[6]
            req_date_last_run = row[7]
            req_confirmed = row[8]
            # If they have not confirmed by email, do not spool. Next row.
            if req_confirmed == 0:
                continue
            requests_in_memory.append([req_email,
                                       req_frequency,
                                       req_company,
                                       req_product,
                                       req_sub_product,
                                       req_hash,
                                       req_date_last_run,
                                       req_confirmed])
        cursor.execute('UPDATE requests SET date_last_run=?',
                       (datetime.datetime.now(),))
        ram_spool = []
        date_obj = datetime.datetime.now()-datetime.timedelta(1)
        date_str = ''.join([str(date_obj.year),
                            '-',
                            str(date_obj.month).zfill(2),
                            '-',
                            str(date_obj.day).zfill(2)])
        # Check each local_cfpb_db for each request in list for particular day
        for row in cursor.execute('SELECT * FROM local_cfpb_db WHERE ' +
                                  'pull_date=?', (date_str,)):
            primary_key = row[0]
            product = row[1]
            sub_product = row[2]
            company = row[3]
            date_sent_to_company = row[4]
            consumer_disputed = row[5]
            date_received = row[6]
            complaint_id = row[7]
            state = row[8]
            timely_response = row[9]
            submitted_via = row[10]
            issue = row[11]
            company_response = row[12]
            zip_code = row[13]
            last_pull = row[14]
            last_pull_year, dash, remainder= last_pull.partition('-')
            last_pull_month, dash, remainder = remainder.partition('-')
            last_pull_day, dash, remainder = remainder.partition('-')
            last_pull_year = int(last_pull_year)
            last_pull_month = int(last_pull_month)
            last_pull_day = int(last_pull_day)
            # If more than 3 days old, do not spool
            now_obj = datetime.datetime.now()
            last_pull_obj = datetime.datetime(last_pull_year,
                                              last_pull_month,
                                              last_pull_day)
            if (now_obj - datetime.timedelta(2)) > last_pull_obj:
                continue
            for request in requests_in_memory:
                if request[2] == company:
                    if request[3] == 'All' or request[3] == product:
                        if request[4] == 'All' or request[4] == sub_product:  
                            print str('Spooling ' +  str(complaint_id))
                            # KEY, EMAIL, ID, COMPANY, PROD, SUBPROD, FREQ
                            ram_spool.append([None,
                                              request[0],
                                              complaint_id,
                                              company,
                                              product,
                                              sub_product,
                                              request[1]])     
        # Put into spool table
        for item in ram_spool:
            cursor.execute('INSERT INTO spool VALUES(?,?,?,?,?,?,?)', item)
            complaint_id = item[2]
        # Log
        cursor.execute('INSERT INTO log VALUES (NULL, ?, ?, ?)',
                           (str(datetime.datetime.now()),
                           'Spool',
                           'Spool date: ' + str(datetime.datetime.now())))
        # Daily commit (put in for debugging)                                                                    
        conn.commit()
        conn.close()
    # Rollback if error         
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))   
      
def send():
    '''Sends email to each recipient.'''
    print "Running daily send."
    # Load email settings from settings.txt
    home_dir = os.getenv('HOME')
    with open(os.path.join(home_dir, 
                           '.cfpb_notifier', 
                           'settings.txt'),"r") as settings_file:
        username = notifier_settings.settings_dict['username']
        password = notifier_settings.settings_dict['password']
        outbound_server = notifier_settings.settings_dict['outbound_server']
        outbound_port = notifier_settings.settings_dict['outbound_port']
        sender_name = notifier_settings.settings_dict['sender_name']
    server = smtplib.SMTP()
    server.set_debuglevel(0)
    try:
        server.connect(str(outbound_server), int(outbound_port))
        server.starttls()
        server.ehlo()
        print "TLS handshake and login ..."
        server.login(username, password)
    except smtplib.SMTPConnectError as err:
        raise Exception(''.join(['Error: '], err.args[0]))
    try:
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
        # Repeat code fix.
    unique_daily_emails = []
        # Add unique email address to daily emails.
#########
    try:
        for row in cursor.execute('SELECT DISTINCT email FROM spool'):          
            unique_daily_emails.append(row[0])
            # Loop through email by email
        # Meaningless try loop for identation
        try:
            for email_address in unique_daily_emails:
                complaint_list = []
                # Get all data for email address
                for row in cursor.execute('SELECT * FROM spool WHERE email=?',
                                          (email_address,)):
                    # adjustment for none in row[5]
                    subproduct = row[5]
                    if subproduct == None:
                        subproduct = ''
                    else:
                        pass
                    confirmed = row[0]
                    email = row[1].replace(u'\x85','\n')
                    complaint_id = row[2].replace(u'\x85','\n')
                    company = row[3].replace(u'\x85','\n')
                    product = row[4].replace(u'\x85','\n')
                    subproduct = subproduct.replace(u'\x85','\n')
                    frequency = row[6].replace(u'\x85','\n')
                    # adjustment for none in row[5]
                    if subproduct == None:
                        subproduct = ''
                    else:
                        pass
                    sort_format = [company, product, subproduct, complaint_id]
                    email = row[1]
                    id_ = row[0]
                    complaint_list.append(sort_format)
                complaint_list.sort()
                # Look up cascade, plug in labels
                last_row = [None, None, None, None]
                # Complaint text to start
                complaint_text = str('\n'
                                     'Company\n'
                                     '----Product\n'
                                     '--------Subproduct\n'
                                     '------------ComplaintID\n')
                for formatted_complaint in complaint_list:
                    if last_row[0] < formatted_complaint[0]:
                        complaint_text = ''.join([complaint_text,
                                                 '\n',
                                                 str(formatted_complaint[0]),
                                                 '\n',
                                                 '----',
                                                 str(formatted_complaint[1]), 
                                                 '\n',
                                                 '--------',
                                                 str(formatted_complaint[2]), 
                                                 '\n',
                                                 '------------',
                                                 str(formatted_complaint[3]), 
                                                 '\n'])
                    else:
                        if last_row[1] < formatted_complaint[1]:
                            complaint_text = ''.join([complaint_text, 
                                             '----',
                                             str(formatted_complaint[1]), 
                                             '\n',
                                             '--------',
                                             str(formatted_complaint[2]), 
                                             '\n',
                                             '------------',
                                             str(formatted_complaint[3]), 
                                             '\n'])
                        else:
                            if last_row[2] < formatted_complaint[2]:
                                complaint_text = ''.join([complaint_text, 
                                                 '--------',
                                                 str(formatted_complaint
                                                 [2]), 
                                                 '\n',
                                                 '------------',
                                                 str(formatted_complaint
                                                 [3]), 
                                                 '\n'])
                            else:
                                if last_row[3] < formatted_complaint[3]:
                                    complaint_text = ''.join([complaint_text, 
                                                     '------------',
                                                     str(formatted_complaint
                                                     [3]), 
                                                     '\n'])
                # Reset last row, so current row can be compared to it.
                    last_row = formatted_complaint
                header = ''.join(['From: ', sender_name, '<', sender_name, '>',
                                  '\n',
                                  'To: ', email, '<', email, '>',
                                  '\n',
                                  'Subject: New CFPB Complaints for',
                                  ' ',
                                  str(datetime.date.today().strftime('%A, '
                                      '%B %d'))])
                # Last minute add links
                hash_list = []
                unsub_links =  str('\nData from https://data.consumerfinance.gov/' +
                                   'dataset/Consumer-Complaints/x94z-ydhh?\n\n' +
                                    'To unsubscribe, click the links below.\n\n' +
                                    '_____________________________________\n\n')
                for row in cursor.execute('SELECT * FROM requests WHERE email=?',
                                           (email,)):
                    unsub_links += str(row[1] + '; ' + 
                                       row[2] + '; ' +
                                       row[3] + '; ' +
                                       row[4] + '; ' +
                                       row[5] + ': ' +
                                       notifier_settings.settings_dict['webhost'] +
                                       'unsubscribe/' + row[6] + '\n\n')
                    hash_list.append(row[6])
                unsub_links += str('Unsubscribe from all: ' + 
                                   notifier_settings.settings_dict['webhost'] +
                                   'unsubscribe/' + '&'.join(hash_list))
                message = ''.join([header, complaint_text, unsub_links])
                print 'Sending email to ' + email
                server.sendmail(sender_name, email, message)
                # Remove sent items from spool
        except Exception:
            pass
        cursor.execute('DELETE FROM spool WHERE frequency="Daily"')
    # Commit
        conn.commit()
        conn.close()
    # Rollback if error         
    except IOError:#TODOsqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))

