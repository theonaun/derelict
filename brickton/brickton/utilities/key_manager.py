import collections
import io
import json
import os

from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal

from .key_handle import KeyHandle
from .export_thread import ExportThread
from .import_thread import ImportThread
from .generator_thread import GeneratorThread
from .error import BricktonError


class KeyManager(QObject):
    '''Handles key generation. TODO: refactor into smaller pieces.'''

    # Signals
    key_created = pyqtSignal(name="key_created")
    splash_update = pyqtSignal([str], name="splash_update")
    keylist_update = pyqtSignal(name="keylist_update")
    console_update = pyqtSignal([str], name="console_update")

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._parent = parent
        self.VERSION = parent.VERSION
        self._home = os.path.expanduser('~')
        self._key_directory = os.path.join(self._home,
                                           '.brickton',
                                           'keys')
        self._file_directory = os.path.join(self._home,
                                            '.brickton',
                                            'files')
        self._export_directory = os.path.join(self._home,
                                             '.brickton',
                                             'exports')
        self._used_key_directory = os.path.join(self._home,
                                                '.brickton',
                                                'used_keys')
        for directory in [self._key_directory,
                          self._file_directory,
                          self._export_directory,
                          self._used_key_directory]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        # Sorting items
        self._all_keys = set()
        self._sender_subset = set()
        self._receiver_subset = set()
        self._selected_subset = set()
        self.sender_identities = set()
        self.receiver_identities = set()
        # Key thread cancellations.
        self._cancellations = []
        # Sort keys for communication
        self._outbound_keys = []
        self._inbound_keys = []

    def add_to_outbound(self, keyname):
        handle = KeyHandle(keyname)
        self._outbound_keys.append(handle)

    def add_to_inbound(self, keyname):
        handle = KeyHandle(keyname)
        self._inbound_keys.append(handle)

    def harmonize_keys(self, server_key_data, client_key_data):
        '''Run by the server to sync up keys. Takes client input list.'''
        harmonized_keys = []
        for server_dict, client_dict in zip(server_key_data, client_key_data):
            if all([server_dict['sender']    ==    client_dict['sender'],
                    server_dict['receiver']  ==    client_dict['receiver'],
                    server_dict['created']   ==    client_dict['created'],
                    server_dict['length']    ==    client_dict['length'],
                    server_dict['position']  ==    client_dict['position'],
                    server_dict['name']      ==    client_dict['name']]):
                harmonized_keys.append(server_dict)
            else:
                pass
        return harmonized_keys

    def get_random_sources(self):
        if os.name == 'posix':
            return ['os.random', '/dev/random (slow!)']
        else:
            return ['os.random']

    def load_keys(self):
        '''With splash screen.'''
        self.splash_update.emit('Starting key check.')
        key_names = os.listdir(self._key_directory)
        self.splash_update.emit('Checking {} keys.'.format(len(key_names)))
        for index, name in enumerate(key_names, start=1):
            status = "Checking key {} of {}.".format(index, len(key_names))
            self.splash_update.emit(status)
            handle = KeyHandle(name)
            if handle.is_valid():
                self._all_keys.add(handle)
                self.sender_identities.add(handle.sender)
                self.receiver_identities.add(handle.receiver)
            else:
                handle.delete()
        self.splash_update.emit('Key check complete.')
        self.splash_update.emit('sentinel_value')
        self.keylist_update.emit()

    def sort_by_sender(self, sender):
        if sender == 'ALL':
            self._sender_subset = self._all_keys
        else:
            self._sender_subset = set([key for key
                                       in self._all_keys
                                       if key.sender == sender])

    def sort_by_receiver(self, receiver):
        if receiver == 'ALL':
            self._receiver_subset = self._all_keys
        else:
            self._receiver_subset = set([key for key
                                         in self._all_keys
                                         if key.receiver == receiver])

    def add_to_pool(self, name):
        handle = KeyHandle(name)
        if handle.is_valid():
            self._all_keys.add(handle)
            self.sender_identities.add(handle.sender)
            self.receiver_identities.add(handle.receiver)
            self.keylist_update.emit()
        else:
            handle.delete()

    def import_keys(self, import_path):
        import_thread = ImportThread(import_path,
                                     self,
                                     self.console_update,
                                     self._key_directory,
                                     self)
        import_thread.start()

    def export_keys(self, party_1, party_2):
        export_thread = ExportThread(party_1,
                                     party_2,
                                     self._all_keys,
                                     self.console_update,
                                     self._key_directory,
                                     self._export_directory,
                                     self)
        export_thread.start()

    def generate_keys(self,
                      party_1,
                      party_2,
                      number_of_key_pairs,
                      random_source,
                      cancellation_event):
        self._cancellations.append(cancellation_event)
        generator_thread = GeneratorThread(party_1,
                                           party_2,
                                           number_of_key_pairs,
                                           random_source,
                                           cancellation_event,
                                           self,
                                           self.console_update,
                                           self._key_directory,
                                           self)
        generator_thread.start()

    def get_all_keys(self):
        key_list = [key for key in self._all_keys]
        key_list.sort(key=lambda x: x.created)
        return key_list

    def get_subset_key_names(self):
        shared_keys = self._receiver_subset.intersection(self._sender_subset)
        return [key.name for key in shared_keys]

    def get_key_data(self, key_name):
        '''Convenience function that extracts key info.'''
        key = list(filter(lambda key: key.name == key_name,
                          self._all_keys))[0]
        # Why does it succeed initially, but fail in handshake2?
        return key.get_summary_data()

    def get_serialized_key_handles(self):
        all_keys = self.get_all_keys()
        handle_list = [KeyHandle(key)
                       for key
                       in all_keys]
        return handle_list

    def get_senders(self):
        senders = sorted(list(self.sender_identities))
        senders.insert(0, 'ALL')
        return senders

    def get_receivers(self):
        receivers = sorted(list(self.receiver_identities))
        receivers.insert(0, 'ALL')
        return receivers

    def trigger_cancellation(self):
        try:
            cancellation_event = self._cancellations.pop()
            cancellation_event.accept()
            self.console_update.emit("Cancelling generation job.")
        except IndexError:
            self.console_update.emit("No jobs to cancel.")

    def remove_cancellation(self):
        '''This removes a cancellation object when it is no longer needed.'''
        self._cancellations.pop()

    def has_key(self, keyname):
        if keyname in self.all_keys:
            return True

    def on_disconnect(self):
        self._inbound_keys = []
        self._outbound_keys = []
        self.console_update('Inbound and outbound keys cleared.')
    
    def compose_outbound_keys(self, key_length):
        '''Convenience function for outbound keys. Raises BricktonError.'''
        return self._compose_keys(self._outbound_keys, key_length)

    def compose_inbound_keys(self, key_length):
        '''Convenience function for inbound keys. Raises BricktonError.'''
        return self._compose_keys(self._inbound_keys, key_length)
    
    def _compose_keys(self, key_list, key_length):
        '''Raises BricktonError.'''
        # Check if sufficient bytes exist for 32 byte hash and key bytes.
        required_bytes = key_length + 32
        availible_bytes = 0
        for key_handle in key_list:
            availible_bytes += key_handle.availible_bytes()
            # Stop going through keys if we know we have neough.
            if availible_bytes > required_bytes:
                break
        # Now that we've looped through, if not enough, raise error.
        if availible_bytes < required_bytes:
            raise BricktonError('Insufficient keys for message.')
        main_key = self._build_key_bytes(key_list, key_length)
        hash_key = self._build_key_bytes(key_list, 32)
        return (main_key, hash_key)

    def _build_key_bytes(self, key_list, number_of_bytes):
        '''Presumes enough bytes exist.'''
        bytes_buffer = io.BytesIO()
        while bytes_buffer.tell() < number_of_bytes:
            key_handle = key_list[0]
            unfetched_bytes = number_of_bytes - bytes_buffer.tell()
            availible_bytes = key_handle.availible_bytes()
            # If key has enough, just get all from key.
            if unfetched_bytes < availible_bytes:
                key_bytes = key_handle.fetch_bytes(unfetched_bytes)
            # If not enough, use whole key and remove file and handle.
            else:
                key_bytes = key_handle.fetch_bytes(availible_bytes)
                key_list.pop(0)
                key_handle.delete()
            # write to buffer
            bytes_buffer.write(key_bytes)
        return bytes_buffer.getvalue()
