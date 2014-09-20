import os
import pickle
import sqlite3

def to_local_db():
    home_dir = os.getenv("HOME")
    os.chdir(os.path.join(home_dir, '.cfpb_notifier'))
    try:
        conn = sqlite3.connect(os.path.join(home_dir,
                                            '.cfpb_notifier',
                                            'notify.db'))
        cursor = conn.cursor()
        # Change cursor items to lists
        cursor_companies = cursor.execute('SELECT DISTINCT company FROM '
                                          'local_cfpb_db')
        list_companies = [ row for row in cursor_companies ]
        cursor_products = cursor.execute('SELECT DISTINCT product FROM '
                                         'local_cfpb_db')
        list_products = [ row for row in cursor_products ]
        # format Subproduct (product)
        cursor_subproducts = cursor.execute('SELECT DISTINCT product,'
                                            ' sub_product FROM'
                                            ' local_cfpb_db')
        # Cursor object to basic list of tuples
        list_subproducts = [ tuple_ for tuple_ in cursor_subproducts ]
        # Coerce Nonetype to 'None' string
        list_subproducts = [ (tuple_[0], 'None') if tuple_[1] == None \
                             else (tuple_[0], tuple_[1]) \
                             for tuple_ in list_subproducts ]
        # Tuples to combined string
        list_subproducts = [ str('(' + tuple_[0] + ')' + ':' 
                             + tuple_[1]) for tuple_ in list_subproducts ]
        conn.close()        
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
    # If pickle fails, allow fatal error to shut it down
    pickle.dump(list_companies, open('company.p', 'wb'))
    pickle.dump(list_products, open('product.p', 'wb'))
    pickle.dump(list_subproducts, open('sub_product.p', 'wb'))
