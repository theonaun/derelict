'''Sample server with wsgiref interface.'''

import os
import pickle
import re
import sqlite3
import threading
import time
from cgi import parse_qs, escape
from wsgiref.simple_server import make_server

import blacklist
import request
from notifier_settings import settings_dict

def error_404(environ, start_response):
    '''No match. 404 error.'''
    start_response('404 NOT FOUND', [('Content-Type', 'text/html'),
                                     ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [str(open(os.path.join(settings_dict['application_dir'],
                                  'error_404_page.html')).read())]

def index(environ, start_response):
    '''Index is mounted at '/'.'''
    start_response('200 OK', [('Content-Type', 'text/html'), 
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [str(open(os.path.join(settings_dict['application_dir'],
                                  'index_page.html')).read())]

def tuzigoot(enviorn, start_response):
    '''This is the main notification interface, mounted at '/tuzigoot'.'''
    # Unpickle lists for webpage
    os.chdir(os.path.join(os.getenv('HOME'),'.cfpb_notifier'))
    try:
        company_set = pickle.load(open('company.p', 'rb'))
        product_set = pickle.load(open('product.p', 'rb')) 
        subprod_set = pickle.load(open('sub_product.p', 'rb'))
    except IOError:
        # On failure, use empty list
        company_set = product_set = subprod_set = ['None']
    for item in [company_set, product_set, subprod_set]:
        item.sort()
    select_string_company = [''.join([''.join(['<option value=','\"', 
                                               company[0].encode('utf-8'), 
                                               '\"', '>', 
                                               company[0].encode('utf-8'),
                                               '</option>'])
                                               for company in company_set])]
    select_string_product = [''.join([''.join(['<option value=','\"',
                                               product[0].encode('utf-8'),
                                               '\"', '>', 
                                               product[0].encode('utf-8'),
                                               '</option>'])
                                               for product in product_set])]
    select_string_subprod = [''.join([''.join(['<option value=','\"', 
                                               subprod.encode('utf-8'),
                                               '\"', '>', 
                                               subprod.encode('utf-8'),
                                               '</option>'])
                                               for subprod in subprod_set])]

    # Head
    tuzigoot_head = ('<html><body bgcolor="#000000">'
                     '<img src="/image/tuzigoot_logo.png"><p>'
                     '</p><p></p>')
    # Middle
    tuzigoot_middle = ('<font face=helvetica color="white">'
                       'Please select your notification criteria.'
                       '</font><p></p>'
                                        
                       '<form name="submission_form" method="post"'
                       ' action="tuzigoot/submit">'
                       '<p></p>'
                       
                       '<font face=helvetica color="white">'
                       'Company:'
                       '</font>'
                       
                       '<select name=\"Company\">'
                       + ''.join(select_string_company) +
                       '</select>'
                       '<p></p>' 
                       
                       '<font face=helvetica color="white">'
                       'Product:'
                       '</font>'
                       
                       '<select name=\"Product\">'
                       '<option value=\"All\">All</option>'
                       + ''.join(select_string_product) +
                       '</select>'
                       '<p></p>'
                       
                       '<font face=helvetica color="white">'
                       'Subproduct:'
                       '</font>'
                       
                       '<select name=\"Subprod\">'
                       '<option value=\"All\">All</option>'
                       + ''.join(select_string_subprod) +
                       '</select>'
                       '<p></p>'
                       
                       '<font face=helvetica color="white">'
                       'Frequency:'
                       '</font>'
                   
                       '<select name=\"Frequency\">'
                       '<option value="Daily">Daily</option>'
                      # '<option value="Weekly">Weekly</option>'
                       '</select>'
                       '<p></p>'
                       
                       '<font face=helvetica color="white">'
                       'Please input your U.S. Bank email address.'
                       '</font>'
                       '<p></p>'
                       '<input type="text" name="email">'
                      
                       '<p></p>'
                       '<input type="submit" value="Submit">'
                       '</form>')
    # Tail                  
    tuzigoot_tail = '</body></html>'
    start_response('200 OK', [('Content-Type', 'text/html'),
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')]) 
    return [''.join([tuzigoot_head, tuzigoot_middle, tuzigoot_tail])]

def unsubscribe(environ, start_response):
    '''This unsubscribes a particular request.'''
    unsub_str = environ['PATH_INFO'].partition('/unsubscribe/')[2].rstrip('/')
    hash_list = unsub_str.split('&')
    for unsub_hash in hash_list:
        unsub_hash = escape(unsub_hash)  
        request.delete_local_request(unsub_hash)
    # Response
    tuzigoot_head = ('<html><body bgcolor="#000000">'
                     '<img src="/image/tuzigoot_logo.png"><p></p>')
    tuzigoot_tail = '</body></html>'
    tuzigoot_middle = ('<font face=helvetica color="white">'
                       'Request confirmed.'
                       '</font><p></p>')
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [''.join([tuzigoot_head, tuzigoot_middle, tuzigoot_tail])]
    
def blacklist_email(environ, start_response):
    '''This takes a GET request and prevents further emails from being sent.'''
    # www.theonaunheim.com/blacklist/email&hash
    unsub_str = environ['PATH_INFO'].partition('/blacklist/')[2].rstrip('/')
    email, ampersand, hash_ = unsub_str.partition('&')
    email = escape(email)
    hash_ = escape(hash_)
    tuzigoot_head = ('<html><body bgcolor="#000000">'
                     '<img src="/image/tuzigoot_logo.png"><p></p>')
    tuzigoot_tail = '</body></html>'
    blacklist_response = blacklist.scratch(email, hash_)
    if blacklist_response:
        tuzigoot_middle = ('<font face=helvetica color="white">'
                           'No more emails will be sent to ' + email + '. '
                           'We apologize for any inconvenience.'
                           '</font><p></p>')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [''.join([tuzigoot_head, tuzigoot_middle, tuzigoot_tail])]
    else:
        tuzigoot_middle = ('<font face=helvetica color="white">'
                           'Blacklist error. Please check hash and try again.'
                           '</font><p></p>')
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [''.join([tuzigoot_head, tuzigoot_middle, tuzigoot_tail])]
        
# Create functions for lins so we can put image references in other pages.
def error_404(environ, start_response):
    '''image_404 is mounted at '/image/error_404.png'.'''
    start_response('200 OK', [('Content-Type', 'image/png'), ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [open(os.path.join(settings_dict['application_dir'],
                         'error_404.png'), 'rb').read()]
                         
def confirmation(environ, start_response):
    '''The recipient confirms newly added requests here.'''
    conf_str = environ['PATH_INFO'].partition('/confirmation/')[2].rstrip('/')
    conf_hash_list = conf_str.split('&')
    for hash_string in conf_hash_list:
        hash_string = escape(hash_string)
        request.confirm_request(hash_string)
    tuzigoot_head = ('<html><body bgcolor="#000000">'
                     '<img src="/image/tuzigoot_logo.png"><p></p>')
    tuzigoot_tail = '</body></html>'
    tuzigoot_middle = ('<font face=helvetica color="white">'
                       'Your request has been confirmed.'
                       '</font><p></p>')
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [''.join([tuzigoot_head, tuzigoot_middle, tuzigoot_tail])]
        
def submit(environ, start_response):
    '''This takes POST data and is mounted at 'tuzigoot/submit'.'''
    try:
       request_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
       request_body_size = 0
    try:
        request_body = environ['wsgi.input'].read(request_size)
        post_data = parse_qs(request_body)
        company = post_data.get('Company')[0]
        product = post_data.get('Product')[0]
        subprod = post_data.get('Subprod')[0]
        frequency = post_data.get('Frequency')[0]
        try:
            email = post_data.get('email')[0]
        except TypeError:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [str('Invalid address or unpermitted domain.')]
        # WSIG escape
        email = escape(email)
        # case insensitive
        email = email.lower()
        company = escape(company)
        subprod = escape(subprod)
        frequency = escape(frequency)
        # Errors
        # Improper domain
        name, at, domain = email.partition('@')
        if domain == '':
            start_response('200 OK', [('Content-Type', 'text/html')])
            print 'domain'
            return [str('Invalid address or unpermitted domain.')]

        # Commit to local db
        if company and product and subprod and frequency and email:
            request.create_local_request(email,
                                         frequency,
                                         company, 
                                         product, 
                                         subprod)

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [str(open(os.path.join(settings_dict['application_dir'],
                                      'success_page.html')).read())]
    # TODO Be more specific
    except IndexError:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['You killed Tuzigoot. I hope you are proud of yourself.']
    except IndexError:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['You killed Tuzigoot. I hope you are proud of yourself.']
    
def tuzigoot_logo(environ, start_response):
    '''tuzigoot_logo is mounted at '/image/tuzigoot_logo.png'.'''
    start_response('200 OK', [('Content-Type', 'image/png'),
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [open(os.path.join(settings_dict['application_dir'],
                              'tuzigoot_logo.png'), 'rb').read()]
    
def welcome_banner(environ, start_response):
    '''welcome_banner is mounted at '/image/welcome_banner.png'.'''
    start_response('200 OK', [('Content-Type', 'image/png'), 
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [open(os.path.join(settings_dict['application_dir'],
                              'welcome_banner.png'), 'rb').read()]
    
def ftp_logo(environ, start_response):
    '''ftp_logo is mounted at '/image/ftp_logo.png'.'''
    start_response('200 OK', [('Content-Type', 'image/png'), 
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [open(os.path.join(settings_dict['application_dir'],
                              'ftp_logo.png'), 'rb').read()]
                              
def robots(environ, start_response):
    '''This is for robots.txt.'''
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [str('User-agent: *\nDisallow: /')]
    
def spry(environ, start_response):
    '''spry is mounted at '/image/spry_the_comply_guy.png'.'''
    start_response('200 OK', [('Content-Type', 'image/png'), 
                              ('Expires', 'Mon, 25 Jun 2020 21:31:12 GMT')])
    return [open(os.path.join(settings_dict['application_dir'],
                              'spry_the_comply_guy.png'), 'rb').read()]
      
# These are for matching urls to the respective functions.
# Note that leading and trailing slashes have been removed already.
map_regex_to_function = [(r'^$', index),
                         (r'^tuzigoot/unsubscribe', unsubscribe),
                         (r'^tuzigoot/blacklist', blacklist_email),
                         (r'^tuzigoot/submit', submit),
                         (r'^tuzigoot/confirmation', confirmation),
                         (r'^image/error_404.png$', error_404),
                         (r'^image/tuzigoot_logo.png$', tuzigoot_logo),
                         (r'^image/welcome_banner.png$', welcome_banner),
                         (r'^image/ftp_logo.png$', ftp_logo),
                         (r'^image/spry_the_comply_guy.png$', spry),
                         (r'^tuzigoot$', tuzigoot),
                         (r'^robots.txt$', robots)]

def application(environ, start_response):
    # Get path from URL
    path = environ['PATH_INFO'].lstrip('/').rstrip('/')
    for regex, function in map_regex_to_function:
        # Match regex to path
        match = re.search(regex, path)
        if match:
            return function(environ, start_response)
    return error_404(environ, start_response)

class Server_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.server = make_server('', 8080, application)
        print "Server_Thread initialized. Serving."
    def run(self):
        while self.running == True:
           self.server.serve_forever()
