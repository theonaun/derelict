cfpb_twitternotify
==================

This Python2 script creates a Twitter feed that notifies people of CFPB complaints according to specific criteria.

1.

This program is meant to be run from a user's home directory (it has only been tested on Linux at this time). Presuming python2 is your default installation, the command would be:

python /appropriate_directory/cfpb_twitterpush/main_app.py

The first day it will update the local db. On following days it will post changes from this database to Twitter.

Tweepy (a third party library) is included.

YOU WILL NEED TO ADD YOUR OWN OAUTH TOKENS TO twit_post.py BEFORE THIS PROGRAM WILL WORK.

-------------

2.

You need to set up your OAuth tokens with Twitter beforehand.

This is very useful to that end (link valid as of 4/21/2014):
http://talkfast.org/2010/05/31/twitter-from-the-command-line-in-python-using-oauth/

-------------

3.

CFPB enters these complaints on a rolling basis as companies complete their responses.

If no response in 15 or so days, posted.

