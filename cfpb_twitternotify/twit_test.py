import multiprocessing
import os
import sys

import tweepy

# Add local directory to path for local imports and debugging purposes
APP_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(APP_DIR)

CONSUMER_KEY = 'KaZHeEcrdRz4f7WZY1PEJLPyK'
CONSUMER_SECRET = 'yXN4QV9lBzfRBni43wI8H62igKTIOM3fttimFJ6llOXwHfp6bO'
ACCESS_KEY = '2473278847-wmtk1cfwwCdtpYkgO9oXYK03v7A9mULqpfmcEsZ'
ACCESS_SECRET = '0pXoG6rVl80t872SbBGaA3ZqrJGrgcO08kz6eWVAIvb5i'
CALLBACK_URL = 'http://www.theonaunheim.com/auth'

# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(CONSUMER_KEY,
                           CONSUMER_SECRET,
                           CALLBACK_URL)

auth.set_access_token(ACCESS_KEY,
                      ACCESS_SECRET)

api = tweepy.API(auth)

mentions = api.mentions_timeline(count=1)

for mention in mentions:
    print mention.text
    print mention.user.screen_name

#http://172.5.64.68:8080/?oauth_token=24Os1vH8zAiwY4baKNXmUElUj9FFBguV6QS9RLtxQTo&oauth_verifier=K6nuWIQ9rj3Yd3vk3DzrSlB2UVWkHBfqekhRRDjD8g

'''
api = tweepy.API(auth)
print api.followers_ids()
#statuses = api.home_timeline(471010602681647104)
#print len(statuses)
#print statuses[0].id



thinglist=[follower.screen_name for follower in api.followers()]

print thinglist
'''
'''
print dir(statuses[0])
print ''
print statuses[0].text
print statuses[0].user.screen_name
'''
# since_id 

# READ EVERY MINUTE. UP TO 2.
# IF REQUEST, CHECK IF FOLLOW. IF NOT FOLLOW SEND TWEET.
# ELSE SEND DM WITH AUTHORIZATION LINK
# THEY GET REDIRECTED TO WEB PAGE
# ?oauth_token=EdeTJqwgsHp5q5z6kWTcPJNnid4RRu4wrbm3yQTJIo&oauth_verifier=nXUP84leRdOdY0n34ajw6EhRcX74Oxq8oeNpn3yib74

'''
redirect_url = auth.get_authorization_url()
print auth.request_token.key
#t6WvdSJMRvW5ABbNczVF1qbiZFedEFEDALLGiwcOiM0
print auth.request_token.secret
#LjCPfBttWfbo0n4bgtTtxtx3IggjTtx1vuMScMslc
print redirect_url
'''
#auth.set_request_token(auth.request_token.key,
#                       auth.request_token.secret)

#try:
#    auth.get_access_token(verifier)

#auth.access_token.key
#auth.access_token.secret
#auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(key, secret)
#api = tweepy.API(auth)




# Creation of the actual interface, using authentication
#api = tweepy.API(auth)
 
# Sample method, used to update a status
# api.update_status('Hello Python Central!')

class Callback_Process(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.running = True
        self.server = make_server('', 8080, application)
        print "Server_Thread initialized. Serving."
    def run(self):
        while self.running == True:
           self.server.serve_forever()

#callback_instance = Callback_Process()
#callback_instance.start()

'''
import sys
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
HandlerClass = SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"
if sys.argv[1:]:
port = int(sys.argv[1])
else:
port = 8000
server_address = ('127.0.0.1', port)
HandlerClass.protocol_version = Protocol
httpd = ServerClass(server_address, HandlerClass) 
sa = httpd.socket.getsockname()
print "Serving HTTP on", sa[0], "port", sa[1], "..."
httpd.serve_forever()
'''
