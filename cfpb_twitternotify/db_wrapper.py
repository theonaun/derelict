'''Meant to be run as:
   python -i /path/db_wrapper.py'''

import os
import sqlite3
import sys

# Add local directory to path for local imports and debugging purposes
APP_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(APP_DIR)

class Complaint():
    def __init__(self,
                 primary_key = None,
                 product = None,
                 sub_product = None,
                 company = None,
                 date_sent_to_company = None,
                 consumer_disputed = None,
                 date_received = None,
                 complaint_id = None,
                 state = None,
                 timely_response = None,
                 submitted_via = None,
                 issue = None,
                 company_response = None,
                 zip_code = None,
                 date_pulled = None):
        self.primary_key = primary_key
        self.product = product
        self.sub_product = sub_product
        self.company = company
        self.date_sent_to_company = date_sent_to_company
        self.consumer_disputed = consumer_disputed
        self.date_received = date_received
        self.complaint_id = complaint_id
        self.state = state
        self.timely_response = timely_response
        self.submitted_via = submitted_via
        self.issue = issue
        self.company_response = company_response
        self.zip_code = zip_code
        self.date_pulled = date_pulled

complaint_pool = []

try:
    conn = sqlite3.connect(os.path.join(APP_DIR,
                                        'data',
                                        'local_cfpb.db'))
    cursor = conn.cursor()
    for row in cursor.execute('SELECT * FROM local_cfpb_db'):
        complaint = Complaint(primary_key=row[0],
                              product=row[1],
                              sub_product=row[2],
                              company=row[3],
                              date_sent_to_company=row[4],
                              consumer_disputed=row[5],
                              date_received=row[6],
                              complaint_id=row[7],
                              state=row[8],
                              timely_response=row[9],
                              submitted_via=row[10],
                              issue=row[11],
                              company_response=row[12],
                              zip_code=row[13],
                              date_pulled=row[14])
        complaint_pool.append(complaint)
       
except sqlite3.Error as err:
    conn.rollback()
    conn.close()
    print err.__class__.__name__ + ': ' + err.message
    raise Exception(sqlite3.Error)


        

