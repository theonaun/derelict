import os
import time

from PyQt5.Qt import QThread


class ExportThread(QThread):

    def __init__(self,
                 party_1,
                 party_2,
                 all_keys,
                 console_signal,
                 key_directory,
                 main_export_directory,
                 parent):
        QThread.__init__(self, parent)
        self._party_1 = party_1
        self._party_2 = party_2
        self._parent = parent
        self._keys = all_keys
        self._console_signal = console_signal
        self._main_export_directory = main_export_directory
        self._key_directory = key_directory
        self._timestamp = '{0:.7f}'.format(time.time())
        self._export_package_dir = os.path.join(self._main_export_directory,
                                                self._timestamp)
        os.makedirs(self._export_package_dir)
        self._keys_to_copy = []
        self._keys_copied_count = 0
        self._keys_missed_count = 0

    def run(self):
        # Shortened for PEP8 zealots.
        emit = self._console_signal.emit
        ex_dir = self._export_package_dir
        self._determine_keys_to_export()
        self._export_keys()
        total_keys = self._keys_copied_count + self._keys_missed_count
        emit("{} of {} keys to copied to {}.".format(self._keys_copied_count,
                                                     total_keys,
                                                     ex_dir))

    def _determine_keys_to_export(self):
        '''This function is for determining shared keys.

        The steps:

        1. Get all keys sent by Party 1 (Set 1)
            + Filter out keys sent by anyone other than Party 1
            + If user is 'ALL' don't filter. This gets keys sent by anybody.
        2. Get all keys received by Party 2 (Set 2)
            + Filter out keys receieved by anyone other than Party 2
            + If user=='ALL' don't filter. This gets keys received by anybody.
        3. Get all keys shared by Set 1 and Set 2 (Set 3)
            + This gives us keys sent by Party 1 and receieved by Party 2.
            + If 'ALL', don't filter as sender/receiever as directed.
        4. Add the keys from Set 3 to a pool of keys (Set 4)
            + This adds P1 -> P2 keys to output pool.
            + Either P1 or P2 can be "ALL", which means all users.
        5. Get all keys sent by Party 2 (Set 5)
            + Filter out keys sent by anyone other than Party 2
            + If user is 'ALL' don't filter. This gets keys sent by anybody.
        6. Get all keys receieved by Party 1 (Set 6)
            + Filter out keys receieved by anyone other than Party 1
            + If user=='ALL' don't filter. This gets keys received by anybody.
        7. Get all keys shared by set 5 and Set 6 (Set 7)
            + This gives us keys sent by Party 2 and receieved by Party 1.
            + If 'ALL', don't filter as sender/receiever as directed.
        8. Add keys from Set 7 to Set 4.
            + This adds P2 -> P1 keys to output pool.
            + Either P1 or P2 can be "ALL", which means all users.

        '''
        if self._party_1 == 'ALL':
            sent_by_party_1 = set([key.name for key in self._keys])
        else:
            sent_by_party_1 = set([key.name for key in self._keys
                                   if key.sender == self._party_1])
        if self._party_2 == 'ALL':
            received_by_party_2 = set([key.name for key in self._keys])
        else:
            received_by_party_2 = set([key.name for key in self._keys
                                       if key.receiver == self._party_2])
        intersection_1_to_2 = sent_by_party_1.intersection(received_by_party_2)
        self._keys_to_copy.extend(intersection_1_to_2)
        if self._party_2 == 'ALL':
            sent_by_party_2 = set([key.name for key in self._keys])
        else:
            sent_by_party_2 = set([key.name for key in self._keys
                                   if key.sender == self._party_2])
        if self._party_1 == 'ALL':
            received_by_party_1 = set([key.name for key in self._keys])
        else:
            received_by_party_1 = set([key.name for key in self._keys
                                       if key.receiver == self._party_1])
        intersection_2_to_1 = sent_by_party_1.intersection(received_by_party_2)
        self._keys_to_copy.extend(intersection_2_to_1)
        self._keys_to_copy = set(self._keys_to_copy)

    def _export_keys(self):
        emit = self._console_signal.emit
        number_to_copy = len(self._keys_to_copy)
        for index, key_name in enumerate(self._keys_to_copy, start=1):
            self.sleep(0)
            source_key_path = os.path.join(self._key_directory,
                                           key_name)
            destination_key_path = os.path.join(self._export_package_dir,
                                                key_name)
            with open(source_key_path, "r") as f1:
                file_data = f1.read()
            try:
                emit("Exporting key {} of {}.".format(index,
                                                      number_to_copy))
                with open(source_key_path, "r") as f1:
                    file_data = f1.read()
                with open(destination_key_path, 'w+') as f2:
                    f2.write(file_data)
                self._keys_copied_count += 1
            except FileNotFoundError:
                self._keys_missed_count += 1
