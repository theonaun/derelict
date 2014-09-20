import os

APP_DIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(APP_DIR, 
                       'data', 
                       'settings.txt'),"r") as settings_file:
    settings_dict = {}
    lines = [ line.replace('\n','') for line in settings_file.readlines() ]
    for entry in lines:
        meta, junk, data = entry.partition(':')
        settings_dict.update({meta:data})
