import base64
import json
import os

from PyQt5.Qt import QThread


class ImportThread(QThread):

    def __init__(self,
                 import_path,
                 key_manager,
                 console_signal,
                 key_directory,
                 parent):
        QThread.__init__(self, parent)
        self._import_path = import_path
        self._km = key_manager
        self._console_signal = console_signal
        self._key_directory = key_directory
        self._parent = parent
        self._total_key_count = 0
        self._successful_key_count = 0
        self._unsuccessful_key_count = 0

    def run(self):
        emit = self._console_signal.emit
        self._key_names = os.listdir(self._import_path)
        emit('{} keys to import.'.format(len(self._key_names)))
        for key_name in self._key_names:
            import_key_path = os.path.join(self._import_path, key_name)
            local_key_path = os.path.join(self._key_directory, key_name)
            # Check validity of key.
            try:
                key_is_valid = self._check_key(import_key_path)
            except Error:
                key_is_valid = False
            # Harmonize and import.
            if key_is_valid:
                key_data = self._harmonize_keys(import_key_path,
                                                local_key_path)
                self._import_key(key_name, key_data)
                emit('Key {} imported.'.format(key_name))
            else:
                self._unsuccessful_key_count += 1
                emit('Key {} is invalid.'.format(key_name))

    def _check_key(self, key_path):
        # Parse name.
        file_string = os.path.splitext(key_path)[0]
        id_string, _, created = file_string.partition('@')
        sender, _, receiver = id_string.partition('_to_')
        # Read
        with open(key_path, 'r') as key_file:
            self.sleep(0)
            data = key_file.read()
            json_data = json.loads(data)
            # First check file name.
            if any([sender   != json_data['sender'],
                    receiver != json_data['receiver'],
                    created  != json_data['created']]):
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

    def _harmonize_keys(self,
                        import_key_path,
                        local_key_path):
        with open(import_key_path, 'r') as import_file:
            import_json = import_file.read()
            import_data = json.loads(import_json)
        with open(local_key_path, 'r') as import_file:
            local_json = import_file.read()
            local_data = json.loads(local_json)
        if all([import_data['sender']   == local_data['sender'],
                import_data['receiver'] == local_data['receiver'],
                import_data['created']  == local_data['created'],
                import_data['version']  == local_data['version'],
                import_data['length']   == local_data['length']]):
            data_bytes = base64.b64decode(local_data['data'])
            array = bytearray(data_bytes)
            position = max(import_data['position'], local_data['position'])
            array[0: position] = [0] * position
            local_data['data'] = base64.b64encode(array)
            return merged_data
        else:
            return local_data

    def _import_key(self, key_name, key_data):
        self._km.import_key(key_name, key_data)
        path = os.path.join(self._key_directory, key_name)
        with open(path, 'w+') as f:
            OD = collections.OrderedDict
            data_dict = OD([('sender', key_data['sender']),
                            ('receiver', key_data['receiver']),
                            ('created', key_data['created']),
                            ('length', key_data['length']),
                            ('position', key_data['position']),
                            ('version'), key_data['version']
                            ('data', key_data['data'])])
            json_string = json.dumps(data_dict, indent=4)
            f.seek(0)
            f.write(json_string)
            f.truncate()