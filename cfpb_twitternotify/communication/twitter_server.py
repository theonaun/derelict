from multiprocessing import Process
from wsgiref.simple_server import make_server
from cgi import parse_qs
from cgi import escape

import os
import re
import time

class Authentication_Server(Process):
    def __init__(self, server_to_fielder_queue):
        Process.__init__(self)
        self.server = make_server('', 8080, self.web_app)
        self.server_to_fielder_queue = server_to_fielder_queue
        print 'Initializing authentication server.'

    def run(self):
        # Load regex list.
        self.load_regex()
        # Serve.
        self.server.serve_forever()

    def web_app(self, environ, start_response):
        # Get path from URL
        path = environ['PATH_INFO'].lstrip('/').rstrip('/')
        if path == '':
            return self.index(environ, start_response)
        for regex, function in self.regex_funclist:
            # Match regex to path
            match = re.search(regex, path)
            if match:
                return function(environ, start_response)
        # If not match return 404.
        return self.error_404(environ, start_response)

    def load_regex(self):
        self.regex_funclist = [(r'^$', self.index),
                               (r'^auth', self.get_auth),
                               (r'^companies.csv', self.get_companies),
                               (r'^products.csv', self.get_products),
                               (r'^issues.csv', self.get_issues)]
################################################################################
# Remaining functions
################################################################################
    def error_404(self, environ, start_response):
        '''404.'''
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['404 Error.']

    def index(self, environ, start_response):
        '''Index.'''
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Index']

    def get_auth(self, environ, start_response):
        '''Auth'''
        # Get query data
        query_data = environ['QUERY_STRING']
        # Prevent injection attacks
        query_data = escape(query_data)
        # Make a dict.
        data_dict = parse_qs(query_data)
        # Place in queue for export.
        self.server_to_fielder_queue.put(data_dict)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Your credentials have been receieved (Token = ' +
                str(data_dict['oauth_token']) +
                '; Verifier = ' + 
                str(data_dict['oauth_verifier']) +
                ')']

    def get_companies(self, environ, start_response):
        '''Companies'''
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [str(open(os.path.join(os.path.dirname(os.path.dirname\
                                     (os.path.abspath(__file__))),
                                      'data',
                                      'companies.csv'), 'r').read())]

    def get_products(self, environ, start_response):
        '''Products'''
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [str(open(os.path.join(os.path.dirname(os.path.dirname\
                                     (os.path.abspath(__file__))),
                                      'data',
                                      'products.csv'), 'r').read())]

    def get_issues(self, environ, start_response):
        '''Issues'''
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [str(open(os.path.join(os.path.dirname(os.path.dirname\
                                     (os.path.abspath(__file__))),
                                      'data',
                                      'issues.csv'), 'r').read())]

if __name__ == '__main__':
    # Debugging
    print 'Testing twitter_server.py'
    import multiprocessing
    queue = multiprocessing.Queue()
    Authentication_Server(queue).start()
