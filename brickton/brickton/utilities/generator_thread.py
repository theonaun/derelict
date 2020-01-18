import base64
import collections
import io
import json
import os
import time

from PyQt5.Qt import QThread


class GeneratorThread(QThread):

    def __init__(self,
                 party_1,
                 party_2,
                 number_of_pairs,
                 random_source,
                 cancellation_event,
                 key_manager,
                 console_signal,
                 key_directory,
                 parent,
                 key_length=1000000):
        QThread.__init__(self, parent)
        self._party_1 = party_1
        self._party_2 = party_2
        self._number_of_pairs = int(number_of_pairs)
        self._random_source = random_source
        # Select appropriate random function.
        if self._random_source == '/dev/random (slow!)':
            self._random_function = self._dev_random
        else:
            self._random_function = self._os_urandom
        # Attach cancel button signal to cancel function.
        self._cancellation_event = cancellation_event
        self._km = key_manager
        self._cs = console_signal
        self._key_directory = key_directory
        self._parent = parent
        self._key_length = key_length
        self._VERSION = self._km.VERSION

    def run(self):
        self._cs.emit('Creating {} key pair(s)'.format(self._number_of_pairs))
        for x in range(self._number_of_pairs):
            self.sleep(0)
            # Check if this thread is cancelled.
            if self._cancellation_event.isAccepted():
                return
            timestamp = '{0:.7f}'.format(time.time())
            key_1_name = ''.join([self._party_1,
                                  '_to_',
                                  self._party_2,
                                  '@',
                                  timestamp,
                                  '.brick'])
            key_2_name = ''.join([self._party_2,
                                  '_to_',
                                  self._party_1,
                                  '@',
                                  timestamp,
                                  '.brick'])
            # Perform same stesp for each key.
            for key_name in [key_1_name, key_2_name]:
                key_path = os.path.join(self._key_directory, key_name)
                array = bytearray()
                final_count = self._key_length
                while len(array) < final_count:
                    self.sleep(0)
                    if self._cancellation_event.isAccepted():
                        return
                    random_bytes = self._random_function()
                    # If you get back False, the thread has been cancelled.
                    if random_bytes is False:
                        return
                    array += random_bytes
                # Use key_length of kilobytes, otherwise you lose data.
                chopped_array = array[0:self._key_length]
                data_string = base64.b64encode(chopped_array).decode('utf-8')
                parties, at, tail = key_name.partition('@')
                sender, breaker, receiver = parties.partition('_to_')
                OD = collections.OrderedDict
                data_dict = OD([('sender', sender),
                                ('receiver', receiver),
                                ('created', timestamp),
                                ('length', self._key_length),
                                ('position', 0),
                                ('version', self._VERSION),
                                ('data', str(data_string))])
                json_string = json.dumps(data_dict, indent=4)
                with open(key_path, 'w+') as f:
                    f.write(json_string)
                # Add to pool.
                self._km.add_to_pool(key_name)
                self._cs.emit('Generated {}.'.format(key_name))
        self._km.remove_cancellation()

    def _os_urandom(self):
        self.sleep(0)
        if self._cancellation_event.isAccepted():
            return False
        return os.urandom(1000)

    def _dev_random(self):
        '''Loops forever.'''
        while True:
            with open('/proc/sys/kernel/random/entropy_avail', 'rb') as f1:
                entropy_string = (f1.read(20)).decode().replace('\n', '')
                availible_entropy = int(entropy_string)
            if availible_entropy > 1000:
                with open('/dev/random', 'rb') as f2:
                    data = f2.read(1000)
                    return data
            else:
                self.sleep(1)
                if self._cancellation_event.isAccepted():
                    return False
