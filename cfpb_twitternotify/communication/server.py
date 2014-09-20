from multiprocessing import Process
from wsgiref.simple_server import make_server

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
        data = environ['QUERY_STRING']
        print data
        token, verifier = data.split('&')
        token = token.partition('=')[2]
        verifier = verifier.partition('=')[2] 
        self.server_to_fielder_queue.put({'token':token, 'verifier':verifier})
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Your credentials have been receieved (Token = ' +
                str(token) +
                '; Verifier = ' + 
                str(verifier) +
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

import multiprocessing
queue = multiprocessing.Queue()
Authentication_Server(queue).start()
