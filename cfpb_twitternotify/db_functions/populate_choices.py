import os
import pickle
import sqlite3

def to_local_csv():
    APP_DIR = os.path.dirname(os.path.realpath(__file__))
    # Not really appdir
    APP_DIR = os.path.dirname(APP_DIR)
    os.chdir(os.path.join(APP_DIR,
                          'data'))
    try:
        conn = sqlite3.connect(os.path.join(APP_DIR,
                                            'data',
                                            'local_cfpb.db'))
        cursor = conn.cursor()
        # Change cursor items to lists
        cursor_companies = cursor.execute('SELECT DISTINCT company FROM '
                                          'local_cfpb_db')
        list_companies = [ row for row in cursor_companies ]
        cursor_products = cursor.execute('SELECT DISTINCT product FROM '
                                         'local_cfpb_db')
        list_products = [ row for row in cursor_products ]
        # format Subproduct (product)
        cursor_issues = cursor.execute('SELECT DISTINCT issue'
                                       ' FROM local_cfpb_db')
        # Cursor object to basic list of tuples
        list_issues = [ tuple_ for tuple_ in cursor_issues ]
        conn.close()        
    except sqlite3.Error as err:
        conn.rollback()
        conn.close()
        raise Exception(''.join(['Error: ', err.args[0]]))
    # Write companies, products, and subproducts to csv. csv module no unicode
    with open('companies.csv', 'w+') as f:
        # Change to formatted text
        list_companies = map(lambda x: '\"' + x[0] + '\"', list_companies)
        list_companies.insert(0, '\"Companies\"')
        f.write('\n'.join(list_companies).encode('utf-8'))
    with open('products.csv', 'w+') as f:
        list_products = map(lambda x: '\"' + x[0] + '\"', list_products)
        list_products.insert(0, '\"Products\"')
        f.write('\n'.join(list_products).encode('utf-8'))
    with open('issues.csv', 'w+') as f:
        # Filter not working. Kludge
        final_list_issues = []
        for item in list_issues:
            if item[0] is not None:
                final_list_issues.append('\"' + item[0] + '\"')
        final_list_issues.insert(0, '\"Issues\"')
        f.write('\n'.join(final_list_issues).encode('utf-8'))

        
