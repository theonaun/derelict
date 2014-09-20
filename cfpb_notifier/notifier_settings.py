import os

home_dir = os.getenv("HOME")

with open(os.path.join(home_dir, 
                       '.cfpb_notifier', 
                       'settings.txt'),"r") as settings_file:
    global settings_dict
    settings_dict = {}
    lines = [ line.replace('\n','') for line in settings_file.readlines() ]
    for entry in lines:
        meta, junk, data = entry.partition(':')
        settings_dict.update({meta:data})
