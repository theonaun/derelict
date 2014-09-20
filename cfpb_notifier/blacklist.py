'''Blacklist.'''

import os
import sqlite3

import notifier_settings

def scratch(email, hash_):
    home_dir = os.getenv('HOME')
    try:
        conn = sqlite3.connect(os.path.join(home_dir, 
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        print "Blacklisting: " + email
        cursor.execute(('SELECT * FROM users WHERE email=?'), (email,))
        actual_hash = cursor.fetchone()[2]
        if str(actual_hash) == str(hash_):
            cursor.execute('UPDATE users SET blacklist=1 WHERE email=?',
                           (email,))
        # Commit changes
        conn.commit()
        conn.close()
        return 'valid'
    # Rollback if error         
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
