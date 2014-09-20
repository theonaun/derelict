#!usr/bin/env python
"""brickton is a one-time pad communication program written in Python 2."""
################################################################################
# Synopsis
################################################################################
#  _          _      _    _               
# | |__  _ __(_) ___| | _| |_ ___  _ __   
# | '_ \| '__| |/ __| |/ / __/ _ \| '_ \ 
# | |_) | |  | | (__|   <| || (_) | | | |
# |_.__/|_|  |_|\___|_|\_\\__\___/|_| |_|
#                                                                     
# brickton
# v.0.5.0
#
# Written by Theo Naunheim (brickton.project@gmail.com)
#
# brickton is a means for sending information using long crytographic
# keys, such as those required for one-time pads. Please see 'How brickton
# Works' for details. Please note that as of version 0.5.0, only Unix-like
# operating systems can run brickton.
#
###############################################################################
# Apache License, Version 2.0
###############################################################################
#
# Copyright 2013 Theo Naunheim
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# A copy of the license is reproduced at the end of this file.
#
###############################################################################
# Module Import / def main()
###############################################################################

import binascii
import glob
import mmap
# import multiprocessing
import os
# import ossaudiodev
import platform
import Queue
import select
import socket
import string
import sys
import threading
import time
import tkFileDialog

from Tkinter import *

# Multiprocessing does not have Queue.Empty. Import from Queue.
# from Queue import Empty

def main():

###############################################################################
# Table/Log Classes
###############################################################################

    class Settings_Table:
        '''KeySettings sets/alters basic settings for program.'''
        def __init__(self):
            self.key_length = 10000
            self.max_key_value = 127 # Ascii. Unicode soon-ish.
            self.default_com_port = 1776
            self.identity = "undefined" # alpha or bravo
            self.logging = "off"
            self.operating_system = platform.platform()
            self.python_version = sys.version_info[0]
            self.home_dir = os.getenv("HOME")
            self.brickton_dir = os.getenv("HOME") + "/.brickton"
            self.entropy_rem_file = '/proc/sys/kernel/random/entropy_avail'
            self.random_or_urandom = 'urandom'
            self.current_key_name = ""
            self.current_key_usage = ""
            self.reservation_name = ""
            self.foreign_ip_address = "0.0.0.0"
            self.brickton_version_number = '0.5.0'
            self.bravo_buffer = 1078
            self.alpha_buffer = 1078
            self.status = 'Not Connected'

    class Brickton_Log:
        '''This object provides logs'''
        def __init__(self):
            self.startup_log = []
            self.process_log = []
            self.error_log = []

###############################################################################
# Setup Sequence Classes
###############################################################################
        
    class Start_Sequence:
        '''Class with a number of functions run in sequence for startup'''
        def check_create_brickton_folder(self):
        # This checks to see if .brickton dir exists.
        # If not existing, it creates.
            if not (os.path.exists(settings_table.brickton_dir)):
                os.makedirs(settings_table.brickton_dir)
                brickton_log.startup_log.append("Creating directory.")
                os.chmod(settings_table.brickton_dir, 0700)
                brickton_log.startup_log.append("Setting permissions to 700.")
                
        def key_fidelity_check(self):
        # This function checks to see if the key is malformed (if it contains
        # anything other than numbers within the key range, used keys ('...'),
        # or metadata (lines beginning with '!!!'). Malformed keys are deleted.
            # Clean out temp files (Linux)
            for filename in os.listdir(settings_table.brickton_dir):
                filename = settings_table.brickton_dir + "/" + filename
                if filename[-1:] == "~":
                    os.remove(filename)
                    brickton_log.startup_log.append("Removing temporary file" +
                                                    filename)
            brickton_log.startup_log.append("Checking key fidelity.")
            # Check Length
            for filename in os.listdir(settings_table.brickton_dir):
                filename = settings_table.brickton_dir + "/" + filename
                # Is the file proper length? (Keylength + 5 lines for metadata)
                filename_line_count = 0
                for line in open(filename):
                    filename_line_count += 1
                if not filename_line_count == (settings_table.key_length + 5):
                    os.remove(filename)
                    brickton_log.startup_log.append("Removing file of " +
                                                    "improper length:" +
                                                    filename)
            for filename in os.listdir(settings_table.brickton_dir):
                full_filename = settings_table.brickton_dir + "/" + filename
                brickton_log.startup_log.append("Checking " + filename)
                key_is_valid = True
                # This loop through lines. If it's not a number between
                # 0 and the max key value from settings table, it checks
                # if it is a '...; or a '!!!'. If neither, loop finishes
                # and deletes.
                max_val = settings_table.max_key_value
                for line in open(full_filename):
                    try:
                        # Proper value for unused key?
                        # If yes, redo loop (true declaration for clarity).
                        if int(line[:3]) >= 0 and int(line[:3]) <= max_val:
                            key_is_valid = True
                    except ValueError:
                        # Proper value for used key or metadata?
                        # If yes, redo loop (true declaration for clarity).
                        if str(line[:3]) == '...':
                             key_is_valid = True
                        elif str(line[:3]) == '!!!':
                            key_is_valid = True
                        # Improper value. Close, delete, and end loop.
                        else:
                            key_is_valid = False
                if key_is_valid == False:
                    os.remove(filename)
                if key_is_valid == True:
                    brickton_log.startup_log.append(filename + " is valid.")
                    
        def key_usage_check(self):
        # This function checks to see the number of keys within a file that
        # have been used. The key name is updated with the new usage number.
        # Keys have the format "NUK." + Unix Timestamp + "_" + Number of keys
        # remaining + ".txt"
        # Example: /home/user/.brickton/NUK.1333333331_09700.txt 
            brickton_log.startup_log.append("Checking key usage.")                                   
            for filename in os.listdir(settings_table.brickton_dir):
                full_filename = settings_table.brickton_dir + "/" + filename
                brickton_log.startup_log.append("Checking usage " + filename)
                # Keys are 3 digit ints. Metadata lines '!!!'. Used keys '...'
                keys_remaining = settings_table.key_length
                lowest_number_of_keys_remaining = settings_table.key_length
                for line in reversed(open(full_filename).readlines()):
                    # Keys remaining count goes down, but is only recorded in
                    # the event of a '...' line (denotes used).
                    keys_remaining -= 1
                    if line[:3] == '...':
                        # Add 5 to eliminate the effect of 5 !!! lines at end.
                        lowest_number_of_keys_remaining = keys_remaining + 5
                update_file_name = (full_filename[:-9] +
                            str(lowest_number_of_keys_remaining).zfill(5) +
                            ".txt")
                # Rename file to reflect key usage)
                os.rename(full_filename, update_file_name)

        # Removes empty keys. In future, use a 'shred'-type program.
            key_list_for_cull = os.listdir(settings_table.brickton_dir)
            for item in key_list_for_cull:
                if item[-9:][:5] == '00000':
                    os.remove(settings_table.brickton_dir + "/" + item)
                if item[-1:] == "~":
                    os.remove(settings_table.brickton_dir + "/" + item)
###############################################################################
# Key Classes
###############################################################################

    class Key_Creator:
        '''KeyCreator creates text-based numeric, ultra-long keys (NUKs)'''
        
        def continuous_gen(self):
            '''continuous_gen generates keys in the background until stopped'''
            # Start loop
            settings_table.continuous_gen = "on"
            while settings_table.continuous_gen == "on":
            # Generate key with format:
            # NUK_<UNIX TIME>_<KEY LENGTH>.txt
                os.chdir(settings_table.brickton_dir)
                key_generated_at = str(time.time())
                if len(key_generated_at) == 12:
                    key_generated_at = key_generated_at + "0"
                NUK_file = open('NUK_' + key_generated_at + '_' +
                                str(settings_table.key_length) + '.txt'
                                , 'w+')
                NUK_file_progress = 0
                while NUK_file_progress < 10000:
                    #entropy_file = open(settings_table.entropy_rem_file, "r")
                    #entropy_avail = entropy_file.read()
                    #entropy_file.close()
                    # If entropy is too low, add entropy through pointless
                    # process. If high enough, add key.
                    entropy_avail = 200
                    # Nasty workaround for OSX.
                    if entropy_avail < 100:
                        # Run pointless process to generate entropy. Removed.
                        continue
                    if entropy_avail >= 100:
                        # Open file, read 1 random byte, modulo 127
                        # Then write the result to the NUK, 3 digit.
                        if settings_table.random_or_urandom == "random":
                            random_file = open('/dev/random', 'r')
                            random_number = ord(random_file.read(1)) % 127
                            # DOES THIS INTRODUCE BIAS? SEE ALSO URANDOM.
                            random_file.close()
                            three_digit_random = str(random_number).zfill(3)
                        if settings_table.random_or_urandom == "urandom":
                            random_file = open('/dev/urandom', 'r')
                            random_number = ord(random_file.read(1)) % 127
                            random_file.close()
                            three_digit_random = str(random_number).zfill(3)
                        # Write digit to file
                        NUK_file.write(three_digit_random + "\n")
                        NUK_file_progress = NUK_file_progress + 1       
                # Add 5 extra lines for later data at end
                NUK_file.write('!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n")
                os.chmod('NUK_' + key_generated_at + '_' +
                                str(settings_table.key_length) + '.txt',
                                0700)
                NUK_file.close()
                
        def discrete_gen(self, number_of_keys_to_gen):
            '''discrete_gen makes a specific number of keys.'''
            # Start loop
            for x in range(0, number_of_keys_to_gen):
            # Generate key with format:
            # NUK_<UNIX TIME>_<KEY LENGTH>.txt
                os.chdir(settings_table.brickton_dir)
                key_generated_at = str(time.time())
                if len(key_generated_at) == 12:
                    key_generated_at = key_generated_at + "0"
                NUK_file = open('NUK_' + key_generated_at + '_' +
                                str(settings_table.key_length) + '.txt'
                                , 'w+')
                NUK_file_progress = 0
                while NUK_file_progress < 10000:
                    #entropy_file = open(settings_table.entropy_rem_file, "r")
                    #entropy_avail = entropy_file.read()
                    #entropy_file.close()
                    # If entropy is too low, trap. If high enough, add key.
                    entropy_avail = 200
                    # Nasty workaround for OSX.
                    if entropy_avail < 100:
                        # Run pointless process to generate entropy.
                        continue
                    if entropy_avail >= 100:
                        # Open file, read 1 random byte, modulo 127
                        # Then write the result to the NUK, 3 digit.
                        if settings_table.random_or_urandom == "random":
                            random_file = open('/dev/random', 'r')
                            random_number = ord(random_file.read(1)) % 127
                            # DOES THIS INTRODUCE BIAS? SEE ALSO URANDOM.
                            random_file.close()
                            three_digit_random = str(random_number).zfill(3)
                        if settings_table.random_or_urandom == "urandom":
                            random_file = open('/dev/urandom', 'r')
                            random_number = ord(random_file.read(1)) % 127
                            random_file.close()
                            three_digit_random = str(random_number).zfill(3)
                        # Write digit to file
                        NUK_file.write(three_digit_random + "\n")
                        NUK_file_progress = NUK_file_progress + 1
                # Add 5 extra lines for later data at end
                NUK_file.write('!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n" +
                               '!!!' + "\n")
                os.chmod('NUK_' + key_generated_at + '_' +
                                str(settings_table.key_length) + '.txt',
                                0700)
                NUK_file.close()

###############################################################################
# Translation Classes
###############################################################################

    class Translator:
        '''Translator class handles conversion and key cleaving'''
        def __init__(self):
            pass

        # File conversion functions
        def file_to_hex_list(self, file_to_hex):
        # Actual list of hex data formed from file conversion
        # len(list_of_hex_file()) for length of this list
            with open(file_to_hex, 'rb') as f:
                raw_data = f.read()
                list_of_hex_data = list(binascii.hexlify(raw_data))
                return list_of_hex_data
            
        def hex_list_to_file(self, data_to_reconstitute_in_list_format,
                             reconstituted_file_filename):
        # List of hex data turned to file
                recon_data = data_to_reconstitute_in_list_format
                file_data = binascii.unhexlify(''.join(recon_data))
                # Write data to new file
                file_object = open(settings_table.brickton_dir + '/' + 
                                   reconstituted_file_filename, 'w')
                file_object.write(file_data)
                file_object.close()
                
        # Text conversion functions
        def text_to_list(self, text_to_convert):
            list_of_text = list(text_to_convert)
            return list_of_text
            
        def list_to_text(self, list_to_convert):
            text_from_list = ''.join(list_to_convert)
            return text_of_list

        # Character conversion functions
        def int_to_ascii(self, integer):
            ascii_character = chr(integer)
            return ascii_character
            
        def ascii_to_int(self, ascii_character):
            integer = ord(ascii_character)
            return integer
      

###############################################################################
# Key Assembly Classes
###############################################################################

    class Assembler:
        '''Translator class handles conversion and key cleaving'''
        def __init__(self):
            self.linked_list_of_keybits = []
            # Front to back
            self.linked_list_of_keys_used = []
            # Below should come from Comm Pipe. Comm pipe calls
            # key_agreement, which plugs into assembler.alpha_keys &
            # assembler.bravo_keys
            self.alpha_keys = []
            self.bravo_keys = []
            self.offline_keys = []
            self.current_key = ""
            self.next_key = ""
            self.key_location = ""
            
        def link_keys_together(self, number_of_keybits_needed):
            # This links keys together based on the numbers at the end of
            # the key. Returns tuple with keybits and where the key locations
            # they came from.
            # Reset lists
            self.linked_list_of_keybits = []
            self.linked_list_of_keys_used = []
            bits_in_dir = 0
            if settings_table.identity == 'alpha':
                keylist_to_use = self.alpha_keys
            if settings_table.identity == 'bravo':
                keylist_to_use = self.bravo_keys
            if settings_table.identity == 'undefined':
                raise Exception("Error: Identity not defined. Assembler" +
                                "object unable to proceed.")
            if settings_table.identity == 'offline':
                keylist_to_use = self.offline_keys
                directory_keys = os.listdir(settings_table.brickton_dir)
                for name in directory_keys:
                    if name.startswith('NUK'):
                        # Chop of .txt so consistent with others.
                        name = name[:-4]
                        self.offline_keys.append(str(name))
                        
            for item in keylist_to_use:
            # Check to see if there are enough keys in the entire pool
            # to satisfy the request
                NUK_keys_left_number = int(item[-9:][4:])
                # TODO: This only works for keys that are 5 digits in
                # length, (e.g. 10000). Fix for longer/shorter keys
                # (e.g. 1000)
                bits_in_dir = bits_in_dir + NUK_keys_left_number
            if bits_in_dir < number_of_keybits_needed:
                brickton_log.error_log.append("Not enough keybits " +
                                              "to satisfy request.")
                    # End method (change text to None upon finalization)
                app.chat_messages.queue.put("Too few keys to satisfy" +
                                            " request.")
                brickton_log.error_log.append(str(bits_in_dir))
                brickton_log.error_log.append("Not enough keybits.")
                raise Exception("Too few keybits to satisfy request.")
                return 0
            # Set keybit increment to 0
            keybit_count = 0
            for item in keylist_to_use:
                # Stop when reach the number of keybits needed
                if number_of_keybits_needed == keybit_count:
                    break
                NUK_keys_left_number = int(item[-9:][4:])
    ############# Present NUK has enough
                if NUK_keys_left_number >= number_of_keybits_needed:
                    # Key has more keybits than needed, number of keys to
                    # take is difference (DIFF).
                    # As the number of keys to start is part of the information
                    # sent, the key number is frozen for later
                    frozen_keys_left_number = str(NUK_keys_left_number).zfill(5)
                    frozen_key_name = item[:-6]
                    # EG if 10,000 left and we need two keybits, remaining
                    # for next is 9,998.
                    new_keys_left_number = int(NUK_keys_left_number)\
                    -int(number_of_keybits_needed)
                    # Superfluous?
                    difference = int(NUK_keys_left_number) - \
                    int(new_keys_left_number)
                    # Correction for filename, because the list gives
                    # the lowest value for the file, not necessarily
                    # its actual name.
                    os.chdir(settings_table.brickton_dir)
                    item_filename = glob.glob("*" + frozen_key_name +
                                              "*")
                    with open(settings_table.brickton_dir + '/' +
                              item_filename[0], "r+") as f:
                        mm = mmap.mmap(f.fileno(), 0)
                        for x in range (0, number_of_keybits_needed):
                            if number_of_keybits_needed < keybit_count:
                                break
                            # MMAP NOTES, EACH LINE IS 4 bytes.
                            # First line is 0, 2nd line is 4
                            # 100th line is 96
                            file_loc = (int(NUK_keys_left_number)-1)*4
                            mm.seek(file_loc)
                            key_bit = mm.read(3)
                            key_bit = int(key_bit)
                            self.linked_list_of_keybits.append(key_bit)
                            # Write '...' in place of used key.
                            mm.seek(file_loc)
                            mm.write('...')
                            NUK_keys_left_number = int(NUK_keys_left_number)-1
                            keybit_count = keybit_count + 1
                            
                    # Add key to list
                    new_remaining_keys = int(frozen_keys_left_number) + 1 -\
                                         int(keybit_count)
                    name_for_list = (frozen_key_name + "_" +
                                     str(frozen_keys_left_number) +
                                     '-' +
                                     str(new_remaining_keys).zfill(5))
                    self.linked_list_of_keys_used.append(name_for_list)
                    # Change filename
                    name_stem = name_for_list[:18]
                    # Subtract one for good key ref?
                    name_end = str(NUK_keys_left_number).zfill(5)
                    new_name = name_stem + name_end + '.txt'
                    old_name = item_filename[0]
                    os.rename(settings_table.brickton_dir + "/" + old_name
                              , settings_table.brickton_dir + "/" + new_name)
                    # Change key_agreement.keys_agreed_upon so it does not
                    # give a 'list out of range' error on the next loop
                    if new_name[18:23] == '00000':
                        os.remove(settings_table.brickton_dir + new_name)

                    # change item in key_list_to_use
                    # index and sbustitute (after removing '.txt')
                    index_location = keylist_to_use.index(old_name[:-4])
                    keylist_to_use[index_location] = new_name[:-4]
                    return [self.linked_list_of_keybits, 
                            self.linked_list_of_keys_used]

    ############# Present NUK does not have enough. Take whole NUK & Repeat
                # Runs until the current key can satisfy the requirements
                # then runs the 'Present NUK has enough loop above'
                if NUK_keys_left_number < number_of_keybits_needed:
                    frozen_keys_left_number = str(NUK_keys_left_number).zfill(5)
                    frozen_key_name = item[:-6]
                    os.chdir(settings_table.brickton_dir)
                    item_filename = glob.glob("*" + frozen_key_name + "*")
                    with open(settings_table.brickton_dir + '/' +
                              item_filename[0], "r+") as f:
                        mm = mmap.mmap(f.fileno(), 0)
                        for x in range (0, NUK_keys_left_number):
                            # MMAP NOTES, EACH LINE IS 4 bytes.
                            # First line is 0, 2nd line is 4
                            # 100th line is 96
                            file_loc = (int(NUK_keys_left_number)-1)*4
                            mm.seek(file_loc)
                            key_bit = mm.read(3)
                            key_bit = int(key_bit)
                            assembler.linked_list_of_keybits.append(key_bit)
                            # Write '...' in place of used key.
                            mm.seek(file_loc)
                            mm.write('...')
                            NUK_keys_left_number = int(NUK_keys_left_number)-1
                            keybit_count = keybit_count + 1
                    # Change filename

                    # Add key to list
                    name_for_list = (frozen_key_name + "_" +
                                     str(frozen_keys_left_number) +
                                     '-' +
                                     str('1').zfill(5))
                    self.linked_list_of_keys_used.append(name_for_list)
                    # Change filename
                    name_stem = name_for_list[:18]
                    name_end = str(NUK_keys_left_number - 1).zfill(5)
                    new_name = name_stem + name_end + '.txt'
                    old_name = item_filename[0]
                    os.rename(settings_table.brickton_dir + "/" + old_name
                              , settings_table.brickton_dir + "/" + new_name)
                    # Change key_agreement.keys_agreed_upon so it does not
                    # give a 'list out of range' error on the next loop

                    if new_name[18:23] == '00000':
                        os.remove(settings_table.brickton_dir + new_name)

                    # Now that you have used item, remove from list
                    keylist_to_use.remove(item)
                    # change item in key_list_to_use

        def create_keys_from_meta(self, key_list):
            list_of_keys = key_list.split(';')
            # At this point you will have a list of keys formatted:
            # NUK_1234567890.12_10000-00000 ... this gives all the
            # info needed.
            self.linked_list_of_keybits = []
            for key_data in list_of_keys:
                NUK_long_name = key_data
                NUK_name = key_data[4:17]
                NUK_start = int(key_data[18:23])
                NUK_end = int(key_data[24:29])
                NUK_keys_needed = NUK_start - NUK_end + 1

                os.chdir(settings_table.brickton_dir)
                item_filename = glob.glob("*" + NUK_name + "*")
                with open(settings_table.brickton_dir + '/' +
                          item_filename[0], "r+") as f:
                    mm = mmap.mmap(f.fileno(), 0)
                    NUK_start_frozen = NUK_start
                    for x in range (0, NUK_keys_needed):
                        # MMAP NOTES, EACH LINE IS 4 bytes.
                        # First line is 0, 2nd line is 4
                        # 100th line is 96
                        file_loc = (int(NUK_start)-1)*4
                        mm.seek(file_loc)
                        key_bit = mm.read(3)

                        key_bit = int(key_bit)
                        assembler.linked_list_of_keybits.append(key_bit)
                        # Write '...' in place of used key.
                        mm.seek(file_loc)
                        mm.write('...')
                        NUK_start = int(NUK_start)-1

                    # Determine name
                    name_stem = NUK_long_name[:18]

                    # Subtract 1?
                    name_end = str(NUK_end - 1).zfill(5)
                    new_name = name_stem + name_end + '.txt'
                    old_name = item_filename[0]

                    # List alteration
                    
                    if settings_table.identity == 'alpha':
                        keylist_other_party = self.bravo_keys
                    if settings_table.identity == 'bravo':
                        keylist_other_party = self.alpha_keys
                    if settings_table.identity == 'offline':
                        keylist_other_party = self.offline_keys
                    # Where in the list is this key found? Index location?
                    index_loc = keylist_other_party.index(name_stem +\
                                str(NUK_start_frozen).zfill(5))
                    # Fill in new key name (minus '.txt') in keylist
                    keylist_other_party[index_loc] = name_stem + name_end

                    # Filename alteration

                    os.rename(old_name, new_name)
                    # Destroy empty key
                    if new_name[18:23] == '00000':
                        os.remove(settings_table.brickton_dir +
                                  '/' +
                                  new_name)
            return assembler.linked_list_of_keybits
        
        def remove_empty_keys(self):
        # Removes empty keys. In future, use a 'shred'-type program.
            key_list_for_cull = os.listdir(settings_table.brickton_dir)
            for item in key_list_for_cull:
                if item[-9:][:5] == '00000':
                    os.remove(settings_table.brickton_dir + "/" + item)
                if item[-1:] == "~":
                    os.remove(settings_table.brickton_dir + "/" + item)
        
###############################################################################
# Offline Class
############################################################################### 

    class Offline:
        '''This class allows for offline conversion of NUK files.'''
        def auto_pack(self, file_to_pack):
            '''
            We create a text file format PAK_1378682474.28.txt
            It contains a 100 letter string containing the file name 
            The data is in hex format follows
            '''
            settings_table.identity = 'offline'
            #
            #
            # Path and file name.
            short_slash_loc = int(str(file_to_pack).rfind('/'))
            short_name = file_to_pack.replace(" ","_")
            # Tack a space to the end of the filename
            short_name = file_to_pack[short_slash_loc + 1:] + " "
            package_name = 'PAK_' + '{:.2f}'.format(time.time()) +'.txt'
            short_name_length = len(short_name)
            quotient = 100//short_name_length
            remainder = 100%short_name_length
            truncated_tail = short_name[:remainder]
            string_to_encode = quotient*short_name + truncated_tail
            name_hex_list = list(binascii.hexlify(string_to_encode))
            file_hex_list = translator.file_to_hex_list(file_to_pack)
            full_file_list = name_hex_list + file_hex_list
            
            # File
            hexed_file_as_string = ''.join(full_file_list)
            len_hexed_file_as_string = len(hexed_file_as_string)
            
            keybit_list, keys_used_list =\
                assembler.link_keys_together(len_hexed_file_as_string)
            
            # Convert ASCII to INT in outgoing item
            list_of_converted_characters = []
            for alphanumeric in full_file_list:
                number = translator.ascii_to_int(alphanumeric)
                list_of_converted_characters.append(number)
            converted_list = zip(keybit_list,
                                 list_of_converted_characters)
            # Add zipped list together
            pre_modulo_list = [key + text for key,
                               text in converted_list]
            # Modulo 127
            post_modulo_number_list = []
            
            for summed_number in pre_modulo_list:
                modulo_result = int(summed_number) % 127
                post_modulo_number_list.append(str(modulo_result)\
                                               .zfill(3))
            outgoing_text = ';'.join(post_modulo_number_list)
            outgoing_keys_used = ';'.join(keys_used_list)

            # Create file
            PAK_file = open(settings_table.brickton_dir + '/' +
                            package_name, 'w+')
            PAK_file.write(outgoing_text + ':' + outgoing_keys_used)
            PAK_file.close()   
            settings_table.identity = 'undefined'
            
        def auto_unpack(self, file_to_unpack):
            '''
            Takes a PAK_1378682474.28.txt style file and reconstitutes
            as a regular file.
            '''
            #
            # Populate assembler.offline_keys
            prelist = os.listdir(settings_table.brickton_dir)
            postlist = []
            # Strip '.txt' from filename
            for item in prelist:
                postlist.append(item[:-4])
                                
            assembler.offline_keys = postlist
            # TODO Make sure PAK file.
            settings_table.identity = 'offline'
            #
            f = open(file_to_unpack)
            data = f.read()
            location = data.find(':')
            meta = data[location+1:]
            text = data[:location]
            keybit_list = assembler.create_keys_from_meta(meta)

           # 3 digits zfill text version of number to int.
           # Repeated code.
           
            split_text = text.split(';')
            
            temp_list_of_ints = []
            for number in split_text:
                number_as_int = int(number) + 127
                temp_list_of_ints.append(number_as_int)
            
            temp_list_of_keybits = []
            
            for number in keybit_list:
                number_as_int = int(number)
                temp_list_of_keybits.append(number_as_int)
                
            converted_list = zip(temp_list_of_ints,
                                 temp_list_of_keybits)
            post_conv_list = [text - key for text,
                              key in converted_list]

            final_list = []
            
            for summed_number in post_conv_list:
                mod_number = summed_number % 127
                decoded_text = translator.int_to_ascii(mod_number)
                final_list.append(decoded_text)
            #
            decoded_string = "".join(final_list)
            # Hex is twice as long as reg digits
            filename_data = decoded_string[:200]
            file_data = decoded_string[200:]

            data_list = list(file_data)
            filename_string = binascii.unhexlify(filename_data)
            filename = filename_string[:int(filename_string.find(' '))]
            translator.hex_list_to_file(data_list, filename)

            f.close()
            os.remove(file_to_unpack)
            settings_table.identity = 'undefined'
            
        def manual_pack(self, item_to_pack, keylist):
            pass
            # TODO
        def create_earmarked_keys(self, list_of_keys_to_reserve):
            pass
            # TODO

###############################################################################
# Arduino RNG Read Class
###############################################################################

    # TODO
    
###############################################################################
# Parser Class
###############################################################################          

    class B_Parser:
        '''This class adds metadata for coordination between the nodes.'''
        # Incoming translates brickton_format to non_brickton_format
        # Outgoing translates non_brickton_format to brickton_format
        # A2B:|TEXT|text_goes_here|ENDTEXT|:|META|metadata_goes_here|ENDMETA|
        
        def parse_outgoing(self,non_brickton_formatted_item, metadata):
        # For alpha (host) outgoing
            if settings_table.identity == 'alpha':
                brickton_formatted_item = ('A2B:' +
                                           '|TEXT|' +
                                           non_brickton_formatted_item +
                                           '|ENDTEXT|:' +
                                           '|META|' +
                                           metadata +
                                           '|ENDMETA|')
            # ' Text editor has wonky syntax
            # For bravo outgoing
            if settings_table.identity == 'bravo':
                brickton_formatted_item = ('B2A:' +
                                           '|TEXT|' +
                                           non_brickton_formatted_item +
                                           '|ENDTEXT|:' +
                                           '|META|' +
                                           metadata +
                                           '|ENDMETA|')
            # For undefined outgoing
            if settings_table.identity == 'undefined':
                app.chat_messages.queue.put('Cannot parse. Identity not ' +
                                              'assigned')
            try:
                return brickton_formatted_item
            except Exception:
                pass # brickton_log above handles.
         
        def parse_incoming(self,brickton_formatted_item):
        # For bravo (client) outgoing
            if settings_table.identity == 'alpha':
                id_tag, text_content, meta_content = \
                self.pull_meta_and_text(brickton_formatted_item)
                return (id_tag, text_content, meta_content)
            # For bravo outgoing
            if settings_table.identity == 'bravo':
                id_tag, text_content, meta_content = \
                self.pull_meta_and_text(brickton_formatted_item)
                return (id_tag, text_content, meta_content)
            # For undefined outgoing
            if settings_table.identity == 'undefined':
                app.chat_messages.queue.put('Cannot parse. Identity not ' +
                                              'assigned')
            try:
                return non_brickton_formatted_item
            except Exception:
                pass
        
        def pull_meta_and_text(self, brickton_formatted_item):
            # This gets the location that text starts and ends, then pulls
            text_start = brickton_formatted_item.find('|TEXT|') + 6
            text_end = brickton_formatted_item.find('|ENDTEXT|')
            text_content = brickton_formatted_item[text_start:text_end]
            # This does the same for metadata
            meta_start = brickton_formatted_item.find('|META|') + 6
            meta_end = brickton_formatted_item.find('|ENDMETA|')
            meta_content = brickton_formatted_item[meta_start:meta_end]
            id_tag = brickton_formatted_item[:3]
            return (id_tag, text_content, meta_content)
                
###############################################################################
# Communication Pipeline
###############################################################################

    class Communication_Pipeline:
        def __init__(self):
            pass
        # This handles the logic for the communication.
        def startup(self):
            # This is invoked by bravo to kick everything off.
            # bravo (stage 1) states it is a brickton node
            bravo_startup_1 = b_parser.parse_outgoing("brickton v." +\
            settings_table.brickton_version_number, "bravo_startup_1")
            sender.queue.put(bravo_startup_1)
            app.chat_messages.queue.put('Control: Communication Pipeline ' +
                                        'starting up ...')

        def incoming(self, incoming_item):
            # Split up string into component pieces
            A2B_or_B2A_tag, text, meta = \
            self.incoming_tuple_split(incoming_item)
            
            ### Responses to communication_pipeline.startup() ###
            if meta == ("bravo_startup_1"):
                # alpha (stage 1) confirms that it is a brickton node.
                alpha_startup_1 = b_parser.parse_outgoing("brickton v." +\
                settings_table.brickton_version_number, "alpha_startup_1")
                sender.queue.put(alpha_startup_1)
                app.chat_messages.queue.put('Control: Receieved query. ' +
                                            'Returning ...')
            elif meta == ("alpha_startup_1"):
                # bravo (stage 2) sends over all of its keys
                bravo_keylist = os.listdir(settings_table.brickton_dir)
                bravo_keylist_as_string = ' '.join(bravo_keylist)
                bravo_startup_2 = \
                b_parser.parse_outgoing(bravo_keylist_as_string, 
                                        "bravo_startup_2")
                sender.queue.put(bravo_startup_2)                                                          
            elif meta == 'bravo_startup_2':
                # alpha (stage 2) processes keys and sends back
                # the list of shared keys
                bravo_keylist = text.split()
                key_agreement.combine_lists_on_host(bravo_keylist)
                
                keys_shared_string = \
                ' '.join(key_agreement.keys_agreed_upon)
                alpha_startup_2 = \
                b_parser.parse_outgoing(keys_shared_string,
                                       "alpha_startup_2")
                sender.queue.put(alpha_startup_2)
                # Keys 1, 3, 5 etc become alpha keys. 2, 4 become bravo
                assembler.alpha_keys = key_agreement.keys_agreed_upon[::2]
                assembler.bravo_keys = key_agreement.keys_agreed_upon[1::2]
                # Put keys in queue for tkinter update
                for key in assembler.alpha_keys:
                    key = 'Alpha: ' + key
                    app.shared_list.queue.put(key)
                for key in assembler.bravo_keys:
                    key = 'Bravo: ' + key
                    app.shared_list.queue.put(key)

                # Untested alpha end connections if insufficient keys
                if len(key_agreement.keys_agreed_upon) < 2:
                    app.chat_messages.queue.put('Control: Insufficient keys. ' +
                                                '5 second timeout ...')
                    time.sleep(5)
                    app.clear_sockets()

            ####
            # Add option for insecured chat.
            # Add option for splitting keys (e.g. alpha top half, bravo bottom)
            ####

            elif meta == 'alpha_startup_2':
                # bravo receives the processed list and sets the
                # settings_table.keys_agreed_upon to received list
                # alpha was already set in key_agreement.combine_lists
                key_agreement.keys_agreed_upon = text.split()
                assembler.alpha_keys = key_agreement.keys_agreed_upon[::2]
                assembler.bravo_keys = key_agreement.keys_agreed_upon[1::2]
                # Put keys in queue for tkinter update
                for key in assembler.alpha_keys:
                    key = 'Alpha: ' + key
                    app.shared_list.queue.put(key)
                for key in assembler.bravo_keys:
                    key = 'Bravo: ' + key
                    app.shared_list.queue.put(key)
                # Untested
                if len(key_agreement.keys_agreed_upon) < 2:
                    app.chat_messages.queue.put('Control: Insufficient keys. ' +
                                                'Exiting ...')
                    app.clear_sockets()
                 
            ### General Messaging ###
            elif meta[:12] == "ciphertext: ":
                key_list = meta[12:]
                keybit_list = assembler.create_keys_from_meta(key_list)
              
                # 3 digits zfill text version of number to int.
                split_text = text.split(';')
                
                temp_list_of_ints = []
                for number in split_text:
                    number_as_int = int(number) + 127
                    temp_list_of_ints.append(number_as_int)
                
                temp_list_of_keybits = []
                
                for number in keybit_list:
                    number_as_int = int(number)
                    temp_list_of_keybits.append(number_as_int)
                    
                
                converted_list = zip(temp_list_of_ints,
                                     temp_list_of_keybits)
                post_conv_list = [text - key for text,
                                  key in converted_list]

                final_list = []
                
                for summed_number in post_conv_list:
                    mod_number = summed_number % 127
                    decoded_text = translator.int_to_ascii(mod_number)
                    final_list.append(decoded_text)
                decoded_string = "".join(final_list)
                app.chat_messages.queue.put(decoded_string)
            ### Plaintext ###
            elif meta == 'plaintext':
                # Send to incoming messages queue without translation.            
                app.chat_messages.queue.put("<<<Insecure>>> plaintext: " +
                                             text)
            ### File ###
            elif meta[:6] == 'file: ':
                key_list = meta[6:]
                keybit_list = assembler.create_keys_from_meta(key_list)
                # 3 digits zfill text version of number to int.
                split_text = text.split(';')
                
                temp_list_of_ints = []
                for number in split_text:
                    number_as_int = int(number) + 127
                    temp_list_of_ints.append(number_as_int)
                
                temp_list_of_keybits = []
                
                for number in keybit_list:
                    number_as_int = int(number)
                    temp_list_of_keybits.append(number_as_int)
                    
                converted_list = zip(temp_list_of_ints,
                                     temp_list_of_keybits)
                post_conv_list = [text - key for text,
                                  key in converted_list]

                final_list = []
                
                for summed_number in post_conv_list:
                    mod_number = summed_number % 127
                    decoded_text = translator.int_to_ascii(mod_number)
                    final_list.append(decoded_text)
                decoded_string = "".join(final_list)
                file_transfer.recv(decoded_string)

            ### Malformed Packet ###
            else:
                if settings_table.identity == 'alpha':
                    try:
                        client_socket.shutdown()
                        client_socket.close()
                    except Exception:
                        pass
                    try:
                        server_socket.shutdown()
                        server_socket.close()
                    except Exception:
                        pass
                    app.chat_messages.queue.put("Error: Packet format " +
                                                "not recognized. " +
                                                incoming_item)
                    brickton_log.error_log.append("Malformed packet: " +
                                                  incoming_item)
                    raise Exception('Malformed packet.')

        def outgoing(self, outgoing_item):
            # If outgoing item is empty, no need to run.
            if outgoing_item == 'False':
                raise Exception('Pipeline: Empty outgoing string.')
                return 0
            
            ### Plaintext ###
            if outgoing_item[:10] == 'plaintext:':
                outgoing_item = outgoing_item[10:]

                # Send to sender queue without translation
                parsed_plaintext = b_parser.parse_outgoing(outgoing_item,
                                                            'plaintext')
                sender.queue.put(parsed_plaintext)
            ### File Transfer ###
            # largely duplicates ciphertext functionality
            elif outgoing_item[:6] == 'file: ':
                # Remove file designation
                outgoing_item_with_filename = outgoing_item[6:]
                # This has a 20 alphanumeric in front
                outgoing_item_list = list(outgoing_item_with_filename)
                length_outgoing_item = len(outgoing_item_list)
                # Returns tuple: keybit list and keys used list
                keybit_list, keys_used_list =\
                assembler.link_keys_together(length_outgoing_item)
                # Convert ASCII to INT in outgoing item
                list_of_converted_characters = []
                for alphanumeric in outgoing_item_list:
                    number = translator.ascii_to_int(alphanumeric)
                    list_of_converted_characters.append(number)
                converted_list = zip(keybit_list,
                                     list_of_converted_characters)
                # Add zipped list together
                pre_modulo_list = [key + text for key,
                                   text in converted_list]
                # Modulo 127
                post_modulo_number_list = []
                
                for summed_number in pre_modulo_list:
                    modulo_result = int(summed_number) % 127
                    post_modulo_number_list.append(str(modulo_result)\
                                                   .zfill(3))
                outgoing_text = ';'.join(post_modulo_number_list)
                outgoing_keys_used = ';'.join(keys_used_list)
                string_for_sender = b_parser.parse_outgoing(outgoing_text,
                                                            "file: " +
                                                            outgoing_keys_used)
                sender.queue.put(string_for_sender)
            
            ### Ciphertext ###
            else:
                outgoing_item_list = list(outgoing_item)
                length_outgoing_item = len(outgoing_item_list)
                # Returns tuple: keybit list and keys used list
                keybit_list, keys_used_list =\
                assembler.link_keys_together(length_outgoing_item)
                # Convert ASCII to INT in outgoing item
                list_of_converted_characters = []
                for alphanumeric in outgoing_item_list:
                    number = translator.ascii_to_int(alphanumeric)
                    list_of_converted_characters.append(number)
                converted_list = zip(keybit_list,
                                     list_of_converted_characters)
                # Add zipped list together
                pre_modulo_list = [key + text for key,
                                   text in converted_list]
                # Modulo 127
                post_modulo_number_list = []
                
                for summed_number in pre_modulo_list:
                    modulo_result = int(summed_number) % 127
                    post_modulo_number_list.append(str(modulo_result)\
                                                   .zfill(3))
                outgoing_text = ';'.join(post_modulo_number_list)
                outgoing_keys_used = ';'.join(keys_used_list)
                string_for_sender = b_parser.parse_outgoing(outgoing_text,
                                                            "ciphertext: " +
                                                            outgoing_keys_used)
                sender.queue.put(string_for_sender)
                
        def incoming_tuple_split(self, incoming_item):
        # Splits the 3 element tuple into its component parts
            parsed_incoming_tuple = b_parser.parse_incoming(incoming_item)
            A2B_or_B2A_tag = parsed_incoming_tuple[0]
            text = parsed_incoming_tuple[1]
            meta = parsed_incoming_tuple[2]
            return (A2B_or_B2A_tag, text, meta)

        def outgoing_tuple_split(self, outgoing_item):
        # Splits the 3 element tuple into its component parts
            parsed_outgoing_tuple = b_parser.parse_outgoing(outgoing_item)
            A2B_or_B2A_tag = parsed_outgoing_tuple[0]
            text = parsed_outgoing_tuple[1]
            meta = parsed_outgoing_tuple[2]
            return (A2B_or_B2A_tag, text, meta)

###############################################################################
# File Sharing Classes
###############################################################################

    class File_Transfer:
        def __init__(self):
            pass
        def send(self, file_to_send):
            hexed_file_as_list = translator.file_to_hex_list(file_to_send)
            hexed_file_as_string = ''.join(hexed_file_as_list)
            # Add F1378155491.08_a.txt format filename to front of string
            hexed_file_with_name = ('F' + '{:.2f}'.format(time.time()) +
                                    '_' + file_to_send[-5:] +
                                    hexed_file_as_string)
            communication_pipeline.outgoing('file: ' + hexed_file_with_name)
        def recv(self, encoded_file_string):
            filename = encoded_file_string[:20]
            file_as_hex_list = list(encoded_file_string[20:])
            translator.hex_list_to_file(file_as_hex_list, filename)
        
        # TODO: do file name like "Offline" does. Truncating name is stupid.

###############################################################################
# VOIP Classes
###############################################################################
##
##    class Voice_In(Process):
##        '''This class records a sound. Requires padsp wrapper.'''
##        def __init__(self):
##            self.running = True
##        def run(self):
##            read_device = ossaudiodev.open('r')
##            read_device.setparameters(ossaudiodev.AFMT_S16_LE,1,8000)
##            frame = 8000
##            while self.running == True:
##                data = read_device.read(500*frame)
##                hexed_data = binascii.hexlify(data)
##                # BOOKMARK... PARSE AND OUT. ADD VOICE TO COMM PIPELINE
##                time.sleep(0)
##            return 0
##                
##    class Voice_Out(Process):
##        '''This class plays a sound. Requires padsp wrapper.'''
##        def __init__(self,write_queue):
##            self.running = True
##            self.queue = write_queue
##        def run(self):
##            write_device = ossaudiodev.open('w')
##            write_device.setparameters(ossaudiodev.AFMT_S16_LE,1,8000)
##            while self.running == True:
##                try:
##                    queue_item = write_queue.get_nowait()
##                    write_device.write(queue_item)
##                    time.sleep(0)
##                except Empty:
##                    time.sleep(0)
##            return 0
##                    
###############################################################################
# Communications Thread Classes
###############################################################################

    # Alpha is host/server     
    class Server_Side(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.running = True
            self.conn = None
            self.addr = None
            self.temp_holding = []
            
        def run(self):
            HOST = ''
            PORT = settings_table.default_com_port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST,PORT))
            s.listen(1)
            # Accept is blocking, so every second, check to see if this
            # tneeds to be done.
            s.settimeout(1)
            while self.running == True:
                try:
                    self.conn, self.addr = s.accept()
                    app.chat_messages.queue.put('Control: Client' +
                                                ' has connected ...')
                    settings_table.status = 'Connected'
                    break
                except socket.error:
                    settings_table.status = 'Not Connected'
            if self.running == False:
                return 0
            # Socket options for new socket 'conn'
            self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Select loop for listen
            while self.running == True:
                try:
                    inputready,outputready,exceptready \
                    = select.select ([self.conn],[],[])
                except:
                    pass
                for input_item in inputready:
                    # Handle sockets
                    try:
                        data = self.conn.recv(settings_table.alpha_buffer)
                    except socket.error:
                        settings_table.status = 'Not Connected'
                        app.chat_messages.insert(END,
                                                 'CONNECTION TERMINATED')
                    time.sleep(0)
                    if data:
                        # Header is in format:
                        # <start_brickton_v.0.5.0_00001_of_00001>
                        package_num = int(data[24:29])
                        total_num_of_packages = int(data[33:38])
                        data_minus_tags = data[39:][:-39]
                        # Is this the last package in a set? If not,
                        # place it into the temp_holding list.
                        if not package_num == total_num_of_packages:
                            self.temp_holding.insert(package_num - 1,
                                                     data_minus_tags)
                        # If it is the last package, reconstitute and
                        # send to the pipeline for translation.
                        if package_num == total_num_of_packages:
                            self.temp_holding.insert(package_num - 1,
                                                     data_minus_tags)
                            combined_data_list = self.temp_holding
                            self.temp_holding = []
                            combined_data = "".join(combined_data_list)
                            # Send to pipeline for translation
                            communication_pipeline.incoming(combined_data)
                    else:
                        time.sleep(0)
                time.sleep(0)
            # If not running, terminate.
            return 0
        
    # Bravo is client     
    class Client_Side(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.host = settings_table.foreign_ip_address
            self.port = settings_table.default_com_port
            self.sock = None
            self.parsed_incoming_bravo = None
            self.running = True
            self.temp_holding = []
            
        def run(self):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(5)
            # Holding
            self.temp_holding = []
            try:
                self.sock.connect((settings_table.foreign_ip_address,
                                   self.port))
                settings_table.status = 'Connected'
                communication_pipeline.startup()
            except socket.error:
                app.chat_messages.queue.put('Control: Socket Error. ' +
                                            'Connection refused.')
            # Select loop for listen
            while self.running == True:
                try:
                    inputready,outputready,exceptready \
                    = select.select ([self.sock],[],[])
                    for input_item in inputready:
                        # Handle sockets
                        try:
                            data = self.sock.recv(settings_table.bravo_buffer)
                        except socket.error:
                            settings_table.status = 'Not Connected'
                        # Does data contain anything?
                        if data:
                            # Header is in format:
                            # <start_brickton_v.0.5.0_00001_of_00001>
                            package_num = int(data[24:29])
                            total_num_of_packages = int(data[33:38])
                            data_minus_tags = data[39:][:-39]
                            # Is this the last package in a set? If not,
                            # place it into the temp_holding list.
                            if not package_num == total_num_of_packages:
                                self.temp_holding.insert(package_num - 1,
                                                         data_minus_tags)
                            # If it is the last package, reconstitute and
                            # send to the pipeline for translation.
                            if package_num == total_num_of_packages:
                                self.temp_holding.insert(package_num - 1,
                                                         data_minus_tags)
                                combined_data_list = self.temp_holding
                                self.temp_holding = []
                                combined_data = "".join(combined_data_list)
                                # Send to pipeline for translation
                                communication_pipeline.incoming(combined_data)
                        else:
                            time.sleep(0)
                            break
                        time.sleep(0)
                except socket.error:
                    app.chat_messages.insert(END, 'CONNECTION TERMINATED')
                    settings_table.status = 'Not connected'
                    time.sleep(0)
            # If not running, terminate.
            return 0

    class Sender(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.queue = Queue.Queue()
            self.running = True
        def run(self):
            while self.running == True:
                try:
                    # Try queue item.
                    queue_item = self.queue.get(True)
                except Queue.Empty:
                    continue
                pre_wrapped_length = len(queue_item)
                # Wrapper for length
                pre_wrapped_length = len(queue_item)
                # TODO: Optimize. Lists, not strings?
                # Packes of 10,000
                req_num_of_packages = (pre_wrapped_length//1000)+1
                # Split into packages
                finalized_packages = []
                list_of_queue_item = list(queue_item)
                for package in range(0,req_num_of_packages):
                    temp_package_build = []
                    try:
                        for bit in range(0,1000):
                            temp_package_build.append\
                            (list_of_queue_item.pop(0))
                    except IndexError:
                        pass
                    finally:
                        finalized_packages.append(temp_package_build)
                # Tag and send packages out
                package_num = 1
                # <start_brickton_v.0.5.0_00001_of_00001>
                # <cease_brickton_v.0.5.0_00001_of_00001>
                for package in finalized_packages:
                    package = str('<start_brickton_v.0.5.0_' +
                              str(package_num).zfill(5) +
                              '_of_' +
                              str(req_num_of_packages).zfill(5) +
                              '>' +
                              "".join(package) +
                              '<cease_brickton_v.0.5.0_' +
                              str(package_num).zfill(5) +
                              '_of_' +
                              str(req_num_of_packages).zfill(5) +
                              '>')
                    package_num += 1
                    if settings_table.identity == 'alpha':
                        try:
                            server_side.conn.sendall(package)
                        except socket.error:
                            app.chat_messages.insert(END,\
                            'NO CONNECTION')
                            settings_table.status = 'Not connected'
                    if settings_table.identity == 'bravo':
                        try:
                            client_side.sock.sendall(package)
                        except socket.error:
                            app.chat_messages.insert(END,\
                            'NO CONNECTION')
                            settings_table.status = 'Not connected'
                    if settings_table.identity == 'undefined':
                        raise Exception('No identity, Sender thread')
            time.sleep(0)
            return 0
            
###############################################################################
# Communications Classes
###############################################################################

    class Key_Agreement:
        '''This is run by alpha to determine the keys to use.'''
        def __init__(self):
            self.keys_agreed_upon = []
            self.alpha_keys = []
            self.bravo_keys = []
            
        def combine_lists_on_host(self, bravo_keylist):
        # This portion is invoked by Alpha
        #
        # Both Bravo and Alpha (host) look up their list of keys.
        # Bravo sends Alpha Bravo's keylist. Alpha sees what keys the
        # two of them share, and how much of the key is remaining.
        # Alpha sends back a list of keys they may both use.
        # e.g. NUK_1370245416.25:10000
            alpha_keylist = os.listdir(settings_table.brickton_dir)
            bravo_keylist_names_only = []
            bravo_keylist = bravo_keylist
            for key in bravo_keylist:  
                bravo_keylist_names_only.append(key[:17])
            alpha_keylist_names_only = []
            for key in alpha_keylist:
                alpha_keylist_names_only.append(key[:17])
            shared_keys_list_short = list(set(alpha_keylist_names_only) &
                                     set(bravo_keylist_names_only))
            shared_keys_with_num = []

            # Match key with name
            for key in shared_keys_list_short:
                name_for_comparison = key[:17]
                
                for alpha_key in alpha_keylist:
                    if alpha_key[:17] == name_for_comparison:
                        alpha_num = alpha_key[-9:-4]
                for bravo_key in bravo_keylist:
                    if bravo_key[:17] == name_for_comparison:
                        bravo_num = bravo_key[-9:-4]
                        
                if int(alpha_num) > int(bravo_num):
                    shared_long = name_for_comparison + '_' + str(bravo_num)
                else:
                    shared_long = name_for_comparison + '_' + str(alpha_num)
                key_agreement.keys_agreed_upon.append(shared_long)
            
            # Sort as to pull from oldest keys
            key_agreement.keys_agreed_upon.sort()

        def get_list_server_send(self):
        # This is Bravo's portion of the process?
            bravo_keylist = os.listdir(settings_table.brickton_dir)

###############################################################################
# Tkinter Classes
###############################################################################

    class Splash_App:
        '''This is a splash screen while key fidelity checks complete'''
        def __init__(self, master):
    ######### Initial Frame
            base = Frame(master)
            base.grid()
            self.main_splash_frame = Frame(base)
            self.main_splash_frame.grid()
            self.queue = Queue.Queue()
            self.text_var = StringVar()
            self.text_var.set('Setting up brickton ...')
            self.status_label = Label(self.main_splash_frame, text=
                                      self.text_var.get())
            self.status_label.pack(padx=110,pady=45)
           
        def update(self):
            # Check all keys before opening window
            splash_screen.update()
            try:
                # Non-blocking queue
                queue_item = self.queue.get(False)
                if queue_item == 'Destroy':
                    splash_screen.destroy()
                    return 0
                self.text_var.set(queue_item)
                self.status_label.destroy()
                self.status_label = Label(self.main_splash_frame,
                                          text=self.text_var.get())
                self.status_label.pack(padx=110,pady=45)
                try:
                    loop_num_var
                except NameError:
                    loop_num_var = 1
                finally:
                    loop_num_var = loop_num_var + 1
                    splash_screen.after(100*loop_num_var,
                                        func=self.update)
            except Queue.Empty:
                try:
                    loop_num_var
                except NameError:
                    loop_num_var = 1
                finally:
                    loop_num_var = loop_num_var + 1
                    splash_screen.after(100*loop_num_var,
                                        func=self.update)
            
    class App:
        '''This is the main Tkinter window'''
        def __init__(self, master):
 ######### Initial Frame
            base = Frame(master)
            base.grid()
            
    ######### Conponent Frame / Hot Mess
            self.start_frame = Frame(base)
            self.start_frame.grid()
            
            # Quit Button
            self.quit_button = Button(self.start_frame, text="Quit",
                                      command=self.quit_button)
            self.quit_button.grid(row=21, column=12, sticky=W+E)
            # Reset Defaults Button
            self.defaults_button = Button(self.start_frame, text="Defaults",
                                          command=self.default_revert)
            self.defaults_button.grid(row=20, column=12, sticky=W+E)
            # Offline Pack
            self.offline_pack_button = Button(self.start_frame,
                                              text="Offline Pack",
                                              command=self.offline_pack)
            self.offline_pack_button.grid(row=21, column=10, sticky=W+E)
            # Offline Unpack
            self.offline_pack_button = Button(self.start_frame,
                                              text="Offline Unpack",
                                              command=self.offline_unpack)
            self.offline_pack_button.grid(row=21, column=11, sticky=W+E)
            # TODO Blind router
            #server_label = Label(start_frame, text="Server")
            #server_label.grid(row=25, column=14, sticky=E)
            # Center buttons
            # Text Entry
            self.entry_var = StringVar()
            self.entry_main = Entry(self.start_frame, width=55,
                                    textvariable=self.entry_var,
                                    background="WHITE",
                                    insertborderwidth=1)
            self.entry_main.grid(row=20, column=0, sticky=W)
            self.entry_main.bind('<Return>', self.event_collect_text)
            # Chat Window
            self.chat_messages = Text(self.start_frame, height=20, width=72,
                                      background="WHITE",
                                      borderwidth=1,
                                      relief="sunken")
            self.chat_messages.grid(row=0, column=0, columnspan=10, rowspan=20,
                                    sticky=W)
            self.chat_messages.queue = Queue.Queue()
            self.chat_messages_running = True
            
            # Scrollbar
            self.chat_scroll = Scrollbar(self.start_frame)
            self.chat_scroll.grid(row=19, column=10, sticky=W)
            self.chat_messages.config(yscrollcommand=self.chat_scroll.set,
                                      insertborderwidth=1)
            self.chat_scroll.config(command=self.chat_messages.yview,
                                    borderwidth=1,
                                    relief="sunken")
            # Empty space
            self.empty_col_1 = Label(self.start_frame, text=" ")
            self.empty_col_1.grid(row=23, column=0, sticky=W)
            # Shared List of Keys
            self.shared_list_label = Label(self.start_frame,
                                           text="Keys Agreed Upon")
            self.shared_list_label.grid(row=24, column=0, sticky=E)
            self.shared_list = Text(self.start_frame, height=20, width=35,
                                    background="WHITE",
                                    borderwidth=1,
                                    relief="sunken")
            self.shared_list.grid(row=25, column=0, columnspan=10, rowspan=20,
                                  sticky=E)
            self.shared_list.queue = Queue.Queue()
            # Shared List Scrollbar
            self.shared_scroll = Scrollbar(self.start_frame)
            self.shared_scroll.grid(row=44, column=10, sticky=W)
            self.shared_list.config(yscrollcommand=self.shared_scroll.set)
            self.shared_scroll.config(command=self.shared_list.yview)
            # Return Button
            self.return_button = Button(self.start_frame, text="Send",
                                        command=self.collect_text)
            self.return_button.grid(row=20, column=9, sticky=W+E)
            # Share button
            self.share_button = Button(self.start_frame, text="Send File",
                                       command=self.file_dialog)
            self.share_button.grid(row=20, column=10, sticky=W+E)

            # IP/Connect
            self.IP_var = StringVar()
            self.IP_label = Label(self.start_frame, text="IP Address")
            self.IP_label.grid(row=0, column=10, sticky=W)
            self.IP_entry = Entry(self.start_frame, width=15,
                                  textvariable=self.IP_var)
            self.IP_entry.bind('<Return>', self.event_collect_IP_and_con)
            self.IP_entry.grid(row=0, column=11)
            self.connect_button = Button(self.start_frame,
                                         text="Chat Connect",
                                         command=self.collect_IP_and_con)
            self.connect_button.grid(row=0, column=12, sticky=W+E)
            self.IP_entry.insert(0, settings_table.foreign_ip_address)
            # Listen Button
            self.listen_button = Button(self.start_frame,
                                        text="Chat Listen",
                                        command=self.listen_for_con)
            self.listen_button.grid(row=1, column=12, sticky=W+E)
            #Clear sockets button
            self.clear_sockets_button = Button(self.start_frame,
                                              text="Clear Sockets",
                                              command=self.clear_sockets)
            self.clear_sockets_button.grid(row=2, column=12, sticky=W+E)
            # Space
            self.empty_space = Label(self.start_frame, text="    ")
            self.empty_space.grid(row=0, column=13, sticky=W)
            # Random or Urandom
            self.random_urandom_label = Label(self.start_frame,
                                              text="Random/Urandom")
            self.random_urandom_label.grid(row=25, column=10, sticky=W)
            # Variable
            self.ran_uran = IntVar() 
            self.Radiobutton1 = Radiobutton(self.start_frame, text="Random",
                                            variable=self.ran_uran, value=1,
                                            command=self.change_to_random)
            self.Radiobutton1.grid(row=25, column=11, sticky=W)
            self.Radiobutton2 = Radiobutton(self.start_frame, text="Urandom",
                                            variable=self.ran_uran, value=0,
                                            command=self.change_to_urandom)
            self.Radiobutton2.grid(row=25, column=12, sticky=W)
            # Log
            self.log1_label = Label(self.start_frame,
                                    text="                            Log")
            self.log1_label.grid(row=24, column=0, sticky=W)
            self.log1 = Text(self.start_frame, height=20, width=35,
                             background="WHITE",
                             borderwidth=1,
                             relief="sunken")
            self.log1.grid(row=25, column=0, sticky=W, rowspan=20,
                           columnspan=5)
            # Identity
            self.identity_label = Label(self.start_frame, text="Identity")
            self.identity_label.grid(row=1, column=10, sticky=W)
            self.identity_box = Entry(self.start_frame, width=15)
            self.identity_box.grid(row=1, column=11)
            self.identity_box.insert(0, settings_table.identity)
            
            # Keygen Var
            self.key_gen_type = IntVar() 
            # Discrete Keygen
            self.key_number_var = IntVar()
            self.discrete_gen_box = Entry(self.start_frame, width=10,
                                          textvariable=self.key_number_var)
            self.discrete_gen_box.grid(row=28, column=11)
            self.discrete_gen_button = Button(self.start_frame, text="Start",
                                              command=self.gen_keynum)
            self.discrete_gen_box.bind('<Return>', self.event_gen_keynum)
            self.discrete_gen_button.grid(row=28, column=12, sticky=W+E)
            self.discrete_gen_label = Label(self.start_frame,
                                            text="Discrete Gen(#)")
            self.discrete_gen_label.grid(row=28, column=10, sticky=W)
            # Continuous Keygen
            self.continuous_gen_label = Label(self.start_frame,
                                              text="Continuous Gen")
            self.continuous_gen_label.grid(row=29, column=10, sticky=W)
            self.continuous_gen_button = Button(self.start_frame, text="Start",
                                                command=self.con_gen_start)
            self.continuous_gen_button.grid(row=29, column=12, sticky=W+E)
            # Status
            self.status_label = Label(self.start_frame, text="Status")
            self.status_label.grid(row=4, column=10, sticky=W)
            self.status_box = Entry(self.start_frame, width=15)
            self.status_box.grid(row=4, column=11)
##            self.status_box.insert(0, settings_table.status)
##            self.status_box.queue = Queue.Queue()
            # Port
            self.port_var = StringVar()
            self.port_label = Label(self.start_frame, text="Port")
            self.port_label.grid(row=5, column=10, sticky=W)
            self.port_box = Entry(self.start_frame, width=15,
                                  textvariable=self.port_var)
            self.port_box.grid(row=5, column=11)
            self.port_box.bind('<Return>', self.event_collect_port)
            self.port_button = Button(self.start_frame, text="Change",
                                         command=self.collect_port)
            self.port_button.grid(row=5, column=12, sticky=W+E)
            self.port_box.insert(0, settings_table.default_com_port)
##            # VOIP
##            self.voip_var = StringVar()
##            self.voip_label = Label(self.start_frame, text="VOIP")
##            self.voip_label.grid(row=6, column=10, sticky=W)
##            self.voip_box = Entry(self.start_frame, width=15,
##                                  textvariable=self.voip_var)
##            self.voip_box.grid(row=6, column=11)
##            self.voip_box.bind('<Return>', self.event_collect_voip)
##            self.voip_button = Button(self.start_frame, text="Voice Connect",
##                                         command=self.collect_voip)
##            self.voip_button.grid(row=6, column=12, sticky=W+E)
##            self.voip_box.insert(0, settings_table.foreign_ip_address)
##            # VOIP Receive
##            self.voiprec_button = Button(self.start_frame,
##                                         text="Voice Receive",
##                                         command=self.listen_for_voice)
##            self.voiprec_button.grid(row=7, column=12, sticky=W+E)
##            
            # License tag
            self.license_label = Label(self.start_frame,
                                       text="Apache License v2")
            self.license_label.grid(row=51, column=12, sticky=E)
            
    ######### Functions
        # Debug Method
        def test(self):
            print "test"
        # Collect Methods
        def collect_text(self):
            timestamp = time.strftime("%H:%M:%S")
            text_data = self.entry_var.get()
            self.chat_messages.insert(END, settings_table.identity + "@" +
                                      timestamp + ": " + text_data + "\n")
            self.entry_main.delete(0, END)
            self.chat_messages.see(END)
            if settings_table.identity == 'undefined':
                return 0
            # Sent to comm pipeline, which gets piped to output after trans
            try:
                communication_pipeline.outgoing(text_data)
            except Exception:
                pass
        def event_collect_text(self, event):
            timestamp = time.strftime("%H:%M:%S")
            text_data = self.entry_var.get()
            self.chat_messages.insert(END, settings_table.identity + "@" +
                                      timestamp + ": " + text_data + "\n")
            self.entry_main.delete(0, END)
            self.chat_messages.see(END)
            if settings_table.identity == 'undefined':
                return 0
            # Sent to comm pipeline, which gets piped to output after trans
            try:
                communication_pipeline.outgoing(text_data)
            except Exception:
                pass
        def event_collect_IP_and_con(self,event):
            try:
                self.clear_sockets()
            except:
                pass
            settings_table.identity = 'bravo'
            # You are sender/client/bravo.
            text_data = self.IP_var.get()
            log_timestamp = time.strftime("%H:%M:%S")
            settings_table.foreign_ip_address = text_data
            self.log1.insert(END, log_timestamp + ": " +
                             "Connecting to: " + text_data +
                             "\n")
            self.log1.see(END)
            # Update Status
            self.identity_box.delete(0, END)
            self.identity_box.insert(END, 'bravo')
            # Instantiate
            global client_side
            client_side = Client_Side()
            client_side.start()
            global sender
            sender = Sender()
            sender.start()
        def collect_IP_and_con(self):
            try:
                self.clear_sockets()
            except:
                pass
            # You are sender/client/bravo
            settings_table.identity = 'bravo'
            text_data = self.IP_var.get()
            settings_table.foreign_ip_address = text_data
            log_timestamp = time.strftime("%H:%M:%S")
            settings_table.foreign_ip_address = text_data
            self.log1.insert(END, log_timestamp + ": " +
                             "Connecting to: " + text_data +
                             "\n")
            self.log1.see(END)
            # Update Status
            self.identity_box.delete(0, END)
            self.identity_box.insert(END, 'bravo')
            # Instantiate
            global client_side
            client_side = Client_Side()
            client_side.start()
            global sender
            sender = Sender()
            sender.start()
        def listen_for_con(self):
            try:
                self.clear_sockets()
            except:
                pass
        # You are listener/server/alpha
            settings_table.identity = 'alpha'
            log_timestamp = time.strftime("%H:%M:%S")
            self.log1.insert(END, log_timestamp + ": " +
                             "Listening on port " +
                             str(settings_table.default_com_port) +
                             "\n")
            self.log1.see(END)
            # Status Box
            self.identity_box.delete(0, END)
            self.identity_box.insert(END, 'alpha')
            # Instantiate
            global server_side
            server_side = Server_Side()
            server_side.start()
            global sender
            sender = Sender()
            sender.start()
            
        def clear_sockets(self):
            # Shutdown sockets and threads
            try:
                client_side.running = False
                client_side.join(5)
            except:
                pass
            try:
                client_side.sock.shutdown(socket.SHUT_RDWR)
                client_side.sock.close()
            except:
                pass
            try:
                server_side.running = False
                server_side.join(5)
            except:
                pass
            try:
                server_side.conn.shutdown(socket.SHUT_RDWR)
                server_side.conn.close()
            except:
                pass
            try:
                sender.running = False
                sender.join(5)
            except:
                pass
            # Purge key list
            assembler.linked_list_of_keybits = []
            assembler.linked_list_of_keys_used = []
            assembler.alpha_keys = []
            assembler.bravo_keys = []
            key_agreement.keys_agreed_upon = []
 
            # Notes
            log_timestamp = time.strftime("%H:%M:%S")
            self.log1.insert(END, log_timestamp + ": " +
                             "Clearing sockets." +
                             "\n")
            self.log1.see(END)
            self.identity_box.delete(0, END)
            self.identity_box.insert(END, 'undefined')
            settings_table.identity = 'undefined'
            settings_table.status = 'Not Connected'
        def event_collect_port(self,event):
            text_data = self.port_var.get()
            settings_table.default_com_port = text_data
        def collect_port(self):
            text_data = self.port_var.get()
            settings_table.default_com_port = text_data
        def event_collect_keymax(self,event):
            text_data = self.keymax_var.get()
            settings_table.max_key_value = text_data
        def collect_keymax(self):
            text_data = self.keymax_var.get()
            settings_table.max_key_value = text_data
        def event_collect_length(self,event):
            text_data = self.key_length_var.get()
            settings_table.key_length = text_data
        def collect_length(self):
            text_data = self.key_length_var.get()
            settings_table.key_length = text_data
        # Key Methods
        def event_gen_keynum(self,event):
            number_to_generate = self.key_number_var.get()
            log_timestamp = time.strftime("%H:%M:%S")
            self.log1.insert(END, log_timestamp + ": " +
                             "Generating " + str(number_to_generate) +
                             " keys." + "\n")
            self.log1.see(END)
            discrete_key_handler.queue.put(number_to_generate)
        def gen_keynum(self):
            number_to_generate = self.key_number_var.get()
            log_timestamp = time.strftime("%H:%M:%S")
            self.log1.insert(END, log_timestamp + ": " +
                             "Generating " + str(number_to_generate) +
                             " keys." + "\n")
            self.log1.see(END)
            discrete_key_handler.queue.put(number_to_generate)
            
        def con_gen_start(self):
            number_to_generate = self.key_number_var.get()
            log_timestamp = time.strftime("%H:%M:%S")
            self.log1.insert(END, log_timestamp + ": " +
                             "Generating keys." + "\n")
            self.log1.see(END)
            continuous_key_handler.queue.put(number_to_generate)
        # VOIP
##        def event_collect_voip(self,event):
##            try:
##                self.clear_sockets()
##            except:
##                pass
##            settings_table.identity = 'bravo'
##            text_data = self.voip_var.get()
##            settings_table.foreign_ip_address = text_data
##            # You are sender/client/bravo
##            log_timestamp = time.strftime("%H:%M:%S")
##            settings_table.foreign_ip_address = text_data
##            self.log1.insert(END, log_timestamp + ": " +
##                             "Connecting to: " + text_data +
##                             "\n")
##            self.log1.see(END)
##            # Update Status
##            self.identity_box.delete(0, END)
##            self.identity_box.insert(END, 'bravo')
##            # Instantiate
##            global client_side
##            client_side = Client_Side()
##            client_side.start()
##            global sender
##            sender = Sender()
##            sender.start()
##            voice_out = Voice_Out()
##            voice_in = Voice_In()
##            voice_out.start()
##            voice_in.start()
##        def collect_voip(self):
##            try:
##                self.clear_sockets()
##            except:
##                pass
##            try:
##                self.clear_sockets()
##            except:
##                pass
##            settings_table.identity = 'bravo'
##            text_data = self.voip_var.get()
##            settings_table.foreign_ip_address = text_data
##            # You are sender/client/bravo
##            log_timestamp = time.strftime("%H:%M:%S")
##            settings_table.foreign_ip_address = text_data
##            self.log1.insert(END, log_timestamp + ": " +
##                             "Connecting to: " + text_data +
##                             "\n")
##            self.log1.see(END)
##            # Update Status
##            self.identity_box.delete(0, END)
##            self.identity_box.insert(END, 'bravo')
##            # Instantiate
##            global client_side
##            client_side = Client_Side()
##            client_side.start()
##            global sender
##            sender = Sender()
##            sender.start()
##            voice_out = Voice_Out()
##            voice_in = Voice_In()
##            voice_out.start()
##            voice_in.start()
##        def listen_for_voice(self):
##            try:
##                self.clear_sockets()
##            except:
##                pass
##            settings_table.identity = 'alpha'
##            voice_out = Voice_Out()
##            voice_in = Voice_In()
##            voice_out.start()
##            voice_in.start()
##            #
##            settings_table.identity = 'alpha'
##            log_timestamp = time.strftime("%H:%M:%S")
##            self.log1.insert(END, log_timestamp + ": " +
##                             "Listening on port " +
##                             str(settings_table.default_com_port) +
##                             "\n")
##            self.log1.see(END)
##            # Status Box
##            self.identity_box.delete(0, END)
##            self.identity_box.insert(END, 'alpha')
##            # Instantiate
##            global server_side
##            server_side = Server_Side()
##            server_side.start()
##            global sender
##            sender = Sender()
##            sender.start()
        # Other Methods
        def quit_button(self):
            root.destroy()
        def file_dialog(self):
            file_to_share = tkFileDialog.askopenfilename()
            file_transfer.send(file_to_share)
            return file_to_share
        def offline_pack(self):
            file_to_pack = tkFileDialog.askopenfilename()
            offline.auto_pack(file_to_pack)
        def offline_unpack(self):
            file_to_unpack = tkFileDialog.askopenfilename()
            offline.auto_unpack(file_to_unpack)
        def default_revert(self):
            settings_table.key_length = 10000
            settings_table.max_key_value = 127 # Ascii. Unicode soon-ish.
            settings_table.default_com_port = 1776
            settings_table.identity = "undefined" # alpha or bravo
            settings_table.logging = "off"
            settings_table.home_dir = os.getenv("HOME")
            settings_table.brickton_dir = os.getenv("HOME") + "/.brickton"
            settings_table.entropy_rem_file = \
            '/proc/sys/kernel/random/entropy_avail'
            settings_table.random_or_urandom = 'urandom'
            settings_table.current_key_name = ""
            settings_table.current_key_usage = ""
            settings_table.reservation_name = ""
            settings_table.foreign_ip_address = ""
        def change_to_random(self):
            settings_table.random_or_urandom = 'random'
        def change_to_urandom(self):
            settings_table.random_or_urandom = 'urandom'
        # This method tries to emulate a thread for incoming text while
        # getting arround Tkinter threading limitations
        def move_queue_to_text(self):
            # This updates individual elements and then redraws root
            # window. Non-blocking queues 'get(False)'.
############ For Key List
            try:
                queue_item_keys = self.shared_list.queue.get(False)
                if queue_item_keys == 'Delete Keys':
                    self.shared_list.delete(0,END)
                else:
                    self.shared_list.insert(END, queue_item_keys + '\n')
            except Queue.Empty:
                pass
            
############ For Status
            try:
                status = settings_table.status
                self.status_box.delete(0, END)
                self.status_box.insert(0, status)
            except Exception:
                pass
            
############ For chat window
            try:
                # Non-blocking queue
                queue_item = self.chat_messages.queue.get(False)
                timestamp = time.strftime("%H:%M:%S")
                # Determine the title of the other party
                if queue_item[:9] == 'Control: ':
                    self.chat_messages.insert(END, queue_item[9:] + '\n')
                    self.chat_messages.see(END)
                elif queue_item[:5] == 'Error':
                    self.chat_messages.insert(END, queue_item + '\n')
                    self.chat_messages.see(END)
                elif queue_item[:12] == 'Brickton Log':
                    self.chat_messages.insert(END, queue_item + '\n')
                    self.chat_messages.see(END)
                else:
                    if settings_table.identity == 'alpha':
                        other_identity = 'bravo'
                    if settings_table.identity == 'bravo':
                        other_identity = 'alpha'
                    if settings_table.identity == 'undefined':
                        other_identity = 'undefined'
                    self.chat_messages.insert(END, other_identity + "@" +
                                              timestamp + ": " +
                                              queue_item + "\n")
                    self.chat_messages.see(END)
                # Convoluted process specific to Tkinter. Move root after
                # based on increment. This updates window.
                try:
                    loop_num_var
                except NameError:
                    loop_num_var = 1
                finally:
                    loop_num_var = loop_num_var + 1
                    root.after(100*loop_num_var,
                               func=self.move_queue_to_text)
            except Queue.Empty:
                try:
                    loop_num_var
                except NameError:
                    loop_num_var = 1
                finally:
                    loop_num_var = loop_num_var + 1
                    root.after(100*loop_num_var,
                               func=self.move_queue_to_text)
            
###############################################################################
# Permanent Key Thread Classes
###############################################################################

    # Debug
    class Debugger(threading.Thread):
            def __init__(self):
                self.queue = Queue.Queue()
                threading.Thread.__init__(self)
                self.running = True
                
            def run(self):
                while self.running == True:
                    time.sleep(5)
                    # Print debug in window
                    app.chat_messages.queue.put("Error: Debug")
                    time.sleep(0)
                return 0

    # This thread is for generating a set number of keys
    class Discrete_Key_Handler(threading.Thread):
            def __init__(self):
                self.queue = Queue.Queue()
                threading.Thread.__init__(self)
                self.running = True
                
            def run(self):
                while self.running == True:
                    try:
                        queue_item = self.queue.get(True, 1)
                        key_creator.discrete_gen(queue_item)
                        time.sleep(0)
                    except Queue.Empty:
                        continue
                        time.sleep(0)

    # This thread is for generating a continuous series of keys
    class Continuous_Key_Handler(threading.Thread):
            def __init__(self):
                self.queue = Queue.Queue()
                threading.Thread.__init__(self)
                self.running = True
            def run(self):
                while self.running == True:
                    try:
                        queue_item = self.queue.get(True, 1)
                        key_creator.continuous_gen()
                        time.sleep(0)
                    except Queue.Empty:
                        continue
                        time.sleep(0)
            
###############################################################################
# Startup Thread
############################################################################### #

    class Startup_Thread(threading.Thread):
            def __init__(self):
                threading.Thread.__init__(self)
                self.running = True
            def run(self):
                start_sequence.check_create_brickton_folder()
                # Display starting brickton for 1 sec
                time.sleep(1)
                splash_app.queue.put("Running key fidelity check ...")
                start_sequence.key_fidelity_check()
                splash_app.queue.put("Running key usage check ...")
                start_sequence.key_usage_check()
                splash_app.queue.put('Destroy')
                return 0

###############################################################################
# Preliminary Object List
###############################################################################                                           

    # Logic Objects
    settings_table = Settings_Table()
    brickton_log = Brickton_Log()
    start_sequence = Start_Sequence()
    key_creator = Key_Creator()
    translator = Translator()
    key_agreement = Key_Agreement()
    assembler = Assembler()
    communication_pipeline = Communication_Pipeline()
    b_parser = B_Parser()
    file_transfer = File_Transfer()
    offline = Offline()

    # Key Threads
    # In retrospect, having 2 threads solely for keys is a terrible idea.
    # FIXME
    # debugger = Debugger()
    discrete_key_handler = Discrete_Key_Handler()
    continuous_key_handler = Continuous_Key_Handler()

    # Start certain threads threads
    # debugger.start()
    discrete_key_handler.start()
    continuous_key_handler.start()

###############################################################################
# Startup
###############################################################################

    # Splash screen (also invokes start_sequence)
    splash_screen = Tk()
    splash_app = Splash_App(splash_screen)
    splash_screen.overrideredirect(True)
    splash_screen.geometry('400x100')
    splash_screen.after(100, func=splash_app.update())
    startup_thread = Startup_Thread()
    startup_thread.start()
    splash_screen.mainloop()
    startup_thread.join()

###############################################################################
# Main Window
###############################################################################

    # Tkinter Main Window
    root = Tk()        
    app = App(root)

    # Adjustments to Tkinter Window
    root.title('brickton v.' +
               settings_table.brickton_version_number)
    root.geometry('900x700+0+0')
    root.resizable(width=True, height=True)
    root.iconbitmap(None)
    # Loop to update Tkinter window for incoming mesages
    root.after(100, func=app.move_queue_to_text())

    #Tkinter main loop
    root.mainloop()

    #Ater mainloop quit, shutdown everything.
    discrete_key_handler.running = False
    continuous_key_handler.running = False
    discrete_key_handler.join()
    continuous_key_handler.join()

if __name__ == "__main__":
    main()

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!                   PROGRAM CONCLUSION                   !!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

###############################################################################
# How brickton Works: Generally
###############################################################################
#
# Summary:
#
# brickton is the best encryption that the year 1882 has to offer. It
# is based on the one-time pad ("OTP") encryption scheme, the details of which
# may be found here: https://en.wikipedia.org/wiki/One-time_pad
#
# In principle, it operates by starting with random numbers derived from
# a random number generator. These random numbers are added to a numerical
# representation of a character (in essence Unicode or ASCII). If each of the
# random numbers are truly random, and there is a random number for each and
# every encoded character, the ciphertext is unbreakable, at least in a
# theoretical sense.
#
# Grossly Over-Simplified Demonstration:
#
# Alpha knows that he wants to send a secure message to Bravo in the future.
# For demonstration purposes, this 1 letter in length. While Alpha and Bravo
# are together, Alpha gives Bravo a secret key, which is the number 100 (a
# number between 0 and 127). They both keep this key secret, and each keeps a
# copy for himself.
#
# Later, Alpha decides to send a message to Bravo. This message is the letter
# "A". Alpha encodes this number from plaintext to ciphertext so that
# Charlie, a potential interceptor, cannot read it.
#
# We turn the letter "A" into a number. We do this by looking up the value of
# "A" in the ASCII table. "A" is equal to 97. Alpha then adds 100 to the value
# of 97, yielding 197. Alpha then takes 197 modulo (%) 127, which yields 70.
# Simply put, to get modulo, we divide 197 by 127, and take the remainder (70)
# Alpha then sends the number 70 to Bravo. Charlie, the interceptor, sees only
# the number 70. He could try to decipher it, but because the key is random,
# from Charlie's perspective, a message of "A" and a message of "Z" are equally
# valid; it is indecipherable.
#
# Encoding synopsis:
# 1. Alpha encodes the letter A to 97 based on the ASCII table.
# 2. Alpha adds 97 (the ASCII value) to 100 (the random key value that Bravo
#    and Alpha share. This yields 197.
# 3. Alpha calculates 197 % 127 (modulo), which is 70. Alpha sends 70.
#
# On Bravo's end, he receives the number 70. After receiving the number 70, he
# subtracts the key (100). This yields -30. If the result of the subtraction
# were a positive number, it would be the ASCII code for his letter. Since it
# is less than zero, Bravo must add 127 to get the ASCII code. -30 + 127 is 97.
# The ASCII value for 97 is "A". Alteratively, -30 % 127 = 97.
#
# Decoding synopsis:
# 1. Bravo recieves 70, and subtracts the secret key of 100, yielding -30.
# 2. Bravo either calculates -30 % 127, or simply ads 127 if negative.
# 3. The resulting number, 97, converts to "A" in ASCII.
#
# Keep in mind that this whole process, while theoretically secure, is a huge
# pain when compared to asymetric-key cryptography. Also, if someone beats the
# secret key out of you, or steals your key, or if your random number generator
# isn't random, or someone hacks into your workstation, or any other number of
# other occurances happen, your encryption is broken.
#
# If you would like to try the math on your own: ord() converts ASCII strings
# to integers, chr() converts integers to ASCII strings, and % is the modulo
# operator within the Python shell.
#
###############################################################################
# Mathematical Proof: One-Time Pad
###############################################################################
#
###############################################################################
# How brickton Works: Program Level
###############################################################################
#
###############################################################################
# Arduino-based RNG
###############################################################################
#
###############################################################################
# Cruft
###############################################################################
#
# Python3
# PyQt
# Windows
# Unicode
# BUFFER
# SERVER
# init.py SPLIT / CURSES / COMMAND LINE
# Arduino rando
#
# Future Ideas/Directions:
#
# TODO: Split single key in the event of only one shared key
#    TOP HALF TO ALPHA, BOTTOM HALF TO BRAVO
# if /bin/shred ... shred -u -z -n 26 NUK_1378608135.51_10000.txt
# Unicode
# Command line interface
# XML based.
# "Dap" handshake
# HUBMODE: blind, paranoid, decode
# Hardware. anti van Eck keyboardand screen and screen anti-keylogger
# stream mode drone
# shred used key files
# Reserved Keys for specific parties in RUK names
# Hardware brick for automatic decoding on specific ports
# Convert to C. Microcontroller attached to two ethernet ports for
# passthrough
#     Everything that goes  out over a specific port gets encoded
#     Everything that comes in gets decoded.
# Test firewall for chosen port
# Same pixels for each character, circle of varying size underneath
# e ink one at a time
# Parrallel keyboard
# Shred. Check files before handcheckafter, shred all changed.  
# Snitchware License
# Firewall test
# ASIC
# XMPP Plug in Openfire
# Mobile device
# Insecure chat option. Split key option.
# Server
# FQDN
# VOIP
