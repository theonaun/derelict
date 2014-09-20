'''Confirmation object. Needs to be instantiated in same namespace as email.'''

import datetime
import hashlib
import os
import smtplib
import sqlite3
import threading
import time

import notifier_settings
import request

class Confirmation_Timer(threading.Thread):
    def __init__(self, email):
        threading.Thread.__init__(self)
        self.running = True
        self.email = email
        self.list_of_requests = []
        self.blacklist_hash = None
        print "Confirmation timer for email " + self.email      
        self.start()
    def run(self):
        try:
            home_dir = os.getenv("HOME")
            conn = sqlite3.connect(os.path.join(home_dir,
                                                '.cfpb_notifier',
                                                'notify.db'))
            cursor = conn.cursor()
            # Check if blacklisted
            cursor.execute('SELECT blacklist FROM users WHERE email=?',
                          (self.email,))
            try:
                blacklist_int = cursor.fetchone()[0]
                if blacklist_int == 1:
                    print 'Blacklisted email. Not sending.'
                    return 0
            except (TypeError, IndexError):
                pass
            try:
                cursor.execute('SELECT COUNT(email) FROM requests WHERE '
                               'email=?', (self.email,))
                request_count = int(cursor.fetchone()[0])
                if request_count > 10:
                    print 'Requester already has 10 requests. Cancelling.'
                    return 0
            except (TypeError, IndexError):
                pass
        except (sqlite3.Error, smtplib.SMTPConnectError) as err:
             conn.rollback()
             conn.close()
             raise Exception(''.join(['Error: '], err.args[0]))
        self.gen_blacklist_hash()
        # Webpage says 10 min.
        killswitch = threading.Timer(600.00, self.send_and_kill)
        killswitch.start()
        while self.running == True:
           time.sleep(0)
        return 0
    def send_and_kill(self):
        # Only 10 requests allowed (20 with workaround)
        self.list_of_requests = self.list_of_requests[:10]
        print 'Sending confirmations to ' + self.email
        try:
            home_dir = os.getenv("HOME")
            conn = sqlite3.connect(os.path.join(home_dir,
                                                '.cfpb_notifier',
                                                'notify.db'))
            cursor = conn.cursor()
            username = notifier_settings.settings_dict['username']
            password = notifier_settings.settings_dict['password']
            outbound_server = notifier_settings.settings_dict['outbound_server']
            outbound_port = notifier_settings.settings_dict['outbound_port']
            sender_name = notifier_settings.settings_dict['sender_name']
            conn.commit()
            email_head = ''.join(['From: ', sender_name, '<', sender_name, '>',
                                  '\n',
                                  'To: ', self.email, '<', self.email, '>',
                                  '\n',
                                  'Subject: Tuzigoot Confirmation\n'])
            email_body = str('Your request has been processed.\n\n' +
                             'Frequency; Company; Product; Subproduct\n\n')
            server = smtplib.SMTP()
            server.set_debuglevel(0)
            server.connect(str(outbound_server), int(outbound_port))
            server.starttls()
            server.login(username, password)
            for table_hash in self.list_of_requests:
                cursor.execute('SELECT * FROM requests WHERE new_hash=?',
                               (table_hash,))
                row = cursor.fetchone()
                # No implicit conversion for none type, convert manually.
                row = [ 'None' if x==None else x for x in row ]
                row = [ str(x) for x in row ]
                # 2 3 4 4
                frequency = row[2]
                company = row[3]
                product = row[4]
                sub_product = row[5]
                table_hash = row[6]
                request_data = str(frequency + '; ' +
                                   company + '; ' +
                                   product + '; ' + 
                                   sub_product + 
                                   '\n\n')
                email_body += str(request_data)
                hashes = '&'.join(self.list_of_requests)
            email_body +='\n\n'
            email_body += str('To confirm, click here: ' +
                              notifier_settings.settings_dict['webhost'] +
                              'confirmation/' + hashes)
            email_body +='\n\n'
            email_body += str('To never receieve emails from Tuzigoot: ' +
                              notifier_settings.settings_dict['webhost'] +
                              'blacklist/' + str(self.email) + '&' +
                              str(self.blacklist_hash))
            message = email_head + email_body
            server.sendmail(sender_name, self.email, message)
        except IOError:#(sqlite3.Error, smtplib.SMTPConnectError) as err:
             conn.rollback()
             conn.close()
             raise Exception(''.join(['Error: '], err.args[0]))
        for item in request.confirmation_pool:
            if item.email == self.email:
                request.confirmation_pool.remove(item)
        self.running = False
        self.join()
        return 0
    def add_request(self, table_hash):
        print 'Adding request to confirmation timer: ' + self.email
        self.list_of_requests.append(table_hash)
    def gen_blacklist_hash(self):
        try:
            home_dir = os.getenv("HOME")
            conn = sqlite3.connect(os.path.join(home_dir,
                                                '.cfpb_notifier',
                                                'notify.db'))
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email=?', (self.email,))
            row = cursor.fetchone()
            try:
                if row[2]:
                    self.blacklist_hash = row[2]
            except TypeError:
                # If doesn't exist, index
                hash_base = ''.join([str(datetime.datetime.now()),
                                     str(os.urandom(2)),
                                     str(self.email)])
                self.blacklist_hash = hashlib.sha256(hash_base).hexdigest()
                print self.blacklist_hash
                conn.execute('INSERT INTO users VALUES (NULL, ?, ?, ?, ?, ?)',
                             (self.email, self.blacklist_hash, 1, 0, None))  
                conn.commit()   
        except (sqlite3.Error, smtplib.SMTPConnectError) as err:
             conn.rollback()
             conn.close()
             raise Exception(''.join(['Error: '], err.args[0]))
