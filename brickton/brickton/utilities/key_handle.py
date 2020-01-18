import base64
import collections
import json
import os

from . import error


class KeyHandle(object):
    '''This is an abstraction that does not actually contain key data.'''

    def __init__(self,
                 key_file_name):
        self._home = os.path.expanduser('~')
        self._key_directory = os.path.join(self._home,
                                           '.brickton',
                                           'keys')
        self.name = key_file_name
        self._file_path = os.path.join(self._key_directory,
                                       self.name)
        with open(self._file_path, 'r') as key_file:
            data = key_file.read()
        json_data     = json.loads(data)
        self.sender   = str(json_data['sender'])
        self.receiver = str(json_data['receiver'])
        self.created  = float(json_data['created'])
        self.length   = int(json_data['length'])
        self.position = int(json_data['position'])

    def get_summary_data(self):
        return {'sender':       self.sender,
                'receiver':     self.receiver,
                'created':      self.created,
                'length':       self.length,
                'position':     self.position,
                'name':         self.name}

    def availible_bytes(self):
        return self.length - self.position

    def is_empty(self):
        if self.availible() > 0:
            return False
        else:
            return True

    def delete(self):
        os.remove(self._file_path)

    def is_valid(self):
        file_string = os.path.splitext(self.name)[0]
        id_string, _, created = file_string.partition('@')
        sender, _, receiver = id_string.partition('_to_')
        with open(self._file_path, 'r') as key_file:
            data = key_file.read()
        json_data = json.loads(data)
        # First check file name.
        if any([sender != json_data['sender'],
                receiver != json_data['receiver'],
                created != json_data['created']]):
            return False
        data_bytes = base64.b64decode(json_data['data'])
        array = bytearray(data_bytes)
        length = int(json_data['length'])
        # Check array length
        if len(array) != length:
            return False
        position = int(json_data['position'])
        # Check if any True (i.e. non-zero) items before position.
        if (True in array[0: position]):
            return False
        return True

    def fetch_bytes(self, number_of_bytes):
        if number_of_bytes > self.availible_bytes():
            raise error.BricktonError("Not enough bytes in key.")
        start_position = self.position
        stop_position = self.position + number_of_bytes
        with open(self._file_path, 'r+') as key_file:
            data = key_file.read()
            data_dict = json.loads(data)
            data_bytes = base64.b64decode(data_dict['data'])
            array = bytearray(data_bytes)
            target_bytes = array[start_position: stop_position]
            # Write over bytes with null bytes.
            return target_bytes
        self.position = stop_position
        with open(self._file_path, 'r+') as key_file:
            data = f.read()
            data_dict = json.loads(data)
            data_dict['position'] = str(stop_position).zfill(10)
            data_bytes = base64.b64decode(data_dict['data'])
            old_array = bytearray(data_bytes)
            start = start_position
            stop = stop_position
            new_array[start, stop] = bytearray([0 for _ in range(start, stop)])
            data_string = base64.b64encode(data_array).decode('utf-8')
            OD = collections.OrderedDict
            data_dict = OD([('sender', data_dict['sender']),
                            ('receiver', data_dict['receiver']),
                            ('created', data_dict['created']),
                            ('length', data_dict['length']),
                            ('position', data_dict['position']),
                            ('version'), data_dict['version'],
                            ('data', str(data_string))])
            json_string = json.dumps(data_dict, indent=4)
            f.seek(0)
            f.write(json_string)
            f.truncate()
        if self.position >= self.length:
            os.remove(self._file_path)
            self._manager.remove(self.name)
