'''emailer.py handles email construction and email sending.'''

import datetime
import email
import os
import smtplib
import sqlite3
import time

import notifier_settings

def send():
    try:
        print 'Running daily email.'
        # Check for last run
        APP_DIR = os.path.dirname(os.path.realpath(__file__))
        # Not really appdir
        APP_DIR = os.path.dirname(APP_DIR)
        conn = sqlite3.connect(os.path.join(APP_DIR,
                                            'data',
                                            'local_cfpb.db'))
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
        requests_in_memory = []
        with open(os.path.join(APP_DIR, 'data', 'requests.csv'), 'r') as f:
            lines = f.readlines()
            # Make a list of all emails
            all_emails = [line.split(',')[0] for line in lines]
            # remove quotations
            all_emails = [email.replace('\"','') for email in all_emails ]
            # Remove 'email' from csv heading
            all_emails.remove('Email')
            # Remove duplicates
            unique_emails = list(set(all_emails))
            # Move items to requests in memory.
            for line in lines:
                line = line.rstrip()
                req_email = line.split(',')[0].replace('\"','')
                req_company = line.split(',')[1].replace('\"','')
                req_product = line.split(',')[2].replace('\"','')
                req_issue = line.split(',')[3].replace('\"','')
                requests_in_memory.append([req_email,
                                           req_company,
                                           req_product,
                                           req_issue])

        # Main container
        #data_by_email = {key: [] for key in unique_emails}
        # Python 2.6.6 Compatability
        dict((key, []) for key in unique_emails)
        # New items that meet the conditions
        date_obj = datetime.datetime.now()#DEBUG-datetime.timedelta(1)
        date_str = ''.join([str(date_obj.year),
                            '-',
                            str(date_obj.month).zfill(2),
                            '-',
                            str(date_obj.day).zfill(2)])
        # Check each local_cfpb_db for each request in list for particular day
        complaints_in_memory = []
        for row in cursor.execute('SELECT * FROM local_cfpb_db WHERE ' +
                                  'pull_date=?', (date_str,)):
            complaints_in_memory.append(row)
        # complaints in memory / requests in memory / data by email
        # FOR EACH COMPLAINT FLIP THIS SO REQUEST THEN COMPLAINT
        for complaint in complaints_in_memory:
            #primary_key = row[0]
            com_product = complaint[1]
            #sub_product = row[2]
            com_company = complaint[3]
            #date_sent_to_company = row[4]
            #consumer_disputed = row[5]
            #date_received = row[6]
            com_complaint_id = complaint[7]
            #state = row[8]
            #timely_response = row[9]
            #submitted_via = row[10]
            com_issue = complaint[11]
            #company_response = row[12]
            #zip_code = row[13]
            last_pull = complaint[14]
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
            # FOR EACH COMPLAINT EACH REQUEST
            # Requests ['Email', 'Company', 'Product', 'Issue']
            # Remove first header request
            for request in requests_in_memory[1:]:
                if request[1] == com_company:
                    if request[2] == 'All' or request[2] == com_product:
                        if request[3] == 'All' or request[3] == com_issue:  
                            print str('Spooling ' +  str(com_complaint_id))
                            # request and to email dict
                            data_by_email[unicode(request[0])].append([\
                                com_company, com_product, com_issue,\
                                com_complaint_id])       
        # Put into spool table
        cursor.execute('INSERT INTO log VALUES (NULL, ?, ?, ?)',
                           (str(datetime.datetime.now()),
                           'Spool',
                           'Spool date: ' + str(datetime.datetime.now())))
                                                                 
        conn.commit()
        conn.close()
    # Rollback if error         
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))     
    print "Running daily send."
    # Load email settings from settings.txt
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
        print "Did you setup email parameters in settings.txt?"
        raise Exception(err)
    try:
        conn = sqlite3.connect(os.path.join(APP_DIR,
                                            'data',
                                            'local_cfpb.db'))
        cursor = conn.cursor()
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
#########
    try:
        # {email:[4 element list],[4 element list]
        # For each email do the special sort.
        # Remove quotations
        for email_address in data_by_email.keys():
            email = email.replace('\"','')
            # If no complaints in list, go to next
            if len(data_by_email[email]) == 0:
                continue
            complaint_list = []
            # Get list of lists for that email.
            orig_data = data_by_email[email_address]
            for complaint in orig_data:
                company = complaint[0]
                product = complaint[1]
                issue = complaint[2]
                complaint_id = complaint[3]
                if issue == None:
                    issue = ''
                    '''
                    # WHAT IS THIS? WHY IS THIS HERE? TODO
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
                        pass.
                    '''
                sort_format = [company, product, issue, complaint_id]
                complaint_list.append(sort_format)
                complaint_list.sort()
            # Look up cascade, plug in labels
            last_row = [None, None, None, None]
            complaint_list.append(last_row)
                # Complaint text to start
            complaint_text = str('\n'
                                 'Company\n'
                                 '----Product\n'
                                 '--------Issue\n'
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
            formatted_date = str(datetime.date.today().strftime('%A, %B %d'))
            header = ''.join(['From: ', sender_name, '<', sender_name, '>',
                              '\n',
                              'To: ', str(email_address), 
                              '<', str(email_address), '>',
                              '\n',
                              'Subject: New CFPB Complaints for',
                              ' ',
                              formatted_date])
            # CONNECT EMAIL
            message = ''.join([header, complaint_text])
            print 'Sending email to ' + str(email_address)
            server.sendmail(sender_name, str(email_address), message)
    # Rollback if error         
    except IOError:#TODOsqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))


